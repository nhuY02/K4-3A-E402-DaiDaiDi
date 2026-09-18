"""Loopback-only backend; explicit public-file allowlist keeps .env/logs private."""
import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from functools import lru_cache
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

from ai_service import (ROOT, ServiceError, chat_answer_live, configuration,
                        explain_selection, explain_selection_live)
from slide_search import DECKS, page_record, search_slides

PUBLIC = {'/': ('index.html', 'text/html'), '/index.html': ('index.html', 'text/html'),
          '/app.js': ('app.js', 'text/javascript'), '/styles.css': ('styles.css', 'text/css'),
          '/selection.css': ('selection.css', 'text/css')}
SLIDE_FILES = {
    'd1-slide-hackathon.pdf': ROOT / 'K4-3A-Day05-06-AI-Product-Hackathon' / 'data' / 'vlearn-pack' / 'slides' / 'd1-slide-hackathon.pdf',
    'd2-slide-hackathon.pdf': ROOT / 'K4-3A-Day05-06-AI-Product-Hackathon' / 'data' / 'vlearn-pack' / 'slides' / 'd2-slide-hackathon.pdf',
}
MAX_SELECTED_TEXT = 2000
MAX_HISTORY_MESSAGES = 8
MAX_HISTORY_CHARS = 8000
MAX_HISTORY_MESSAGE_CHARS = 4000

def course_data():
    return {'lessons': [{'id': meta['id'], 'title': meta['title'], 'deck_id': deck_id,
                         'pages': 29} for deck_id, meta in DECKS.items()]}


def normalize_pdf_text(value, *, fold_case=True):
    """Canonicalize harmless Unicode and PDF layout differences for validation."""
    value = unicodedata.normalize('NFKC', str(value))
    value = value.replace('\u00a0', ' ').replace('\u00ad', '')
    value = re.sub(r'[\u200b-\u200d\ufeff]', '', value)
    # Join only explicit line-break hyphenation; preserve ordinary in-line hyphens.
    value = re.sub(r'(?<=\w)-[ \t]*[\r\n]+[ \t]*(?=\w)', '', value)
    value = re.sub(r'[\r\n\t]+', ' ', value)
    value = re.sub(r'\s+', ' ', value).strip()
    return value.casefold() if fold_case else value


def _validation_tokens(value):
    return re.findall(r'\w+', normalize_pdf_text(value), flags=re.UNICODE)


def selection_match_mode(selected_text, page_text):
    """Return a conservative match mode, or None when text is not on the page."""
    selected = normalize_pdf_text(selected_text)
    page = normalize_pdf_text(page_text)
    if selected and selected in page:
        return 'normalized_substring'
    selected_tokens = _validation_tokens(selected_text)
    page_tokens = _validation_tokens(page_text)
    if not selected_tokens or len(selected_tokens) > len(page_tokens):
        return None
    size = len(selected_tokens)
    if any(page_tokens[index:index + size] == selected_tokens
           for index in range(len(page_tokens) - size + 1)):
        return 'contiguous_tokens'
    # Browser selection can concatenate adjacent absolutely-positioned PDF spans
    # (for example "trong" + "ngữ"). Ignoring token boundaries still requires
    # the exact normalized character sequence to be contiguous on this page.
    selected_compact = ''.join(selected_tokens)
    page_compact = ''.join(page_tokens)
    if len(selected_tokens) >= 2 and len(selected_compact) >= 8 and selected_compact in page_compact:
        return 'compact_token_sequence'
    return None


@lru_cache(maxsize=64)
def _pdf_page_content(canonical_deck_id, page_number):
    """Extract image-aligned text and words once from the allowlisted PDF page."""
    try:
        import fitz
    except ImportError as exc:
        raise ServiceError('renderer_unavailable', 'Không thể đọc lớp văn bản của slide.', 503) from exc
    try:
        with fitz.open(SLIDE_FILES[DECKS[canonical_deck_id]['file']]) as document:
            pdf_page = document.load_page(page_number - 1)
            width, height = float(pdf_page.rect.width), float(pdf_page.rect.height)
            page_text = pdf_page.get_text('text')
            horizontal_boxes = []
            for block in pdf_page.get_text('dict').get('blocks', []):
                if block.get('type') != 0:
                    continue
                for line in block.get('lines', []):
                    direction = line.get('dir', (1.0, 0.0))
                    if direction[0] > 0.98 and abs(direction[1]) < 0.02:
                        horizontal_boxes.append(tuple(line['bbox']))
            items = []
            for index, word in enumerate(pdf_page.get_text('words')):
                x0, y0, x1, y1, text, block_no, line_no, word_no = word
                text = str(text).strip()
                if not text or x1 <= x0 or y1 <= y0:
                    continue
                center_x, center_y = (x0 + x1) / 2, (y0 + y1) / 2
                if not any(left - 1 <= center_x <= right + 1 and top - 1 <= center_y <= bottom + 1
                           for left, top, right, bottom in horizontal_boxes):
                    continue
                items.append({'text': text,
                              'x': max(0.0, min(1.0, x0 / width)),
                              'y': max(0.0, min(1.0, y0 / height)),
                              'w': max(0.0, min(1.0, (x1 - x0) / width)),
                              'h': max(0.0, min(1.0, (y1 - y0) / height)),
                              'block': int(block_no), 'line': int(line_no),
                              'word': int(word_no), 'index': index})
    except (OSError, KeyError, ValueError, RuntimeError) as exc:
        raise ServiceError('renderer_unavailable', 'Không thể đọc lớp văn bản của slide.', 503) from exc
    return {'width': width, 'height': height, 'page_text': page_text, 'items': items}


def slide_text_layer(deck_id, page):
    """Return visible words and normalized PDF coordinates for one allowlisted page."""
    record = page_record(deck_id, page)
    if record is None:
        raise ServiceError('invalid_slide', 'Không tìm thấy trang slide.', 404)
    content = _pdf_page_content(record['deck_id'], record['page'])
    return {'deck_id': DECKS[record['deck_id']]['id'], 'page': int(page),
            'width': content['width'], 'height': content['height'],
            'items': [dict(item) for item in content['items']]}


def selection_service_payload(payload):
    """Resolve a UI selection against the real page while retaining the CP3 contract."""
    required = {'source', 'deck_id', 'page', 'selected_text'}
    allowed = required | {'original_question', 'original_answer'}
    if not isinstance(payload, dict) or not required.issubset(payload) or not set(payload).issubset(allowed):
        raise ServiceError('invalid_input', 'Thiếu dữ liệu đoạn văn bản được chọn.', 400)
    if payload['source'] not in {'slide', 'tutor'}:
        raise ServiceError('invalid_input', 'Nguồn đoạn văn bản không hợp lệ.', 400)
    for field in ('deck_id', 'selected_text'):
        if not isinstance(payload[field], str):
            raise ServiceError('invalid_input', 'Dữ liệu đoạn văn bản không hợp lệ.', 400)
    original_question = payload.get('original_question', '')
    original_answer = payload.get('original_answer', '')
    if not isinstance(original_question, str) or not isinstance(original_answer, str):
        raise ServiceError('invalid_input', 'Dữ liệu đoạn văn bản không hợp lệ.', 400)
    selected = payload['selected_text'].strip()
    if not selected or len(selected) > MAX_SELECTED_TEXT:
        raise ServiceError('invalid_input', 'Đoạn được chọn trống hoặc quá dài.', 400)
    record = page_record(payload['deck_id'], payload['page'])
    if record is None:
        raise ServiceError('invalid_slide', 'Không tìm thấy trang slide.', 404)
    page_content = _pdf_page_content(record['deck_id'], record['page'])
    course_context = page_content['page_text']
    if payload['source'] == 'slide':
        if selection_match_mode(selected, course_context) is None:
            raise ServiceError('invalid_input', 'Đoạn được chọn không thuộc trang slide hiện tại.', 400)
        question = 'Giải thích đoạn văn bản được chọn từ slide.'
        # ai_service validates that the selection belongs to original_answer.
        # The selection itself is the smallest safe interaction container;
        # factual authority remains the real page text in course_context.
        original_answer = selected
    else:
        if len(original_question) > 4000 or len(original_answer) > 16000:
            raise ServiceError('invalid_input', 'Ngữ cảnh hội thoại quá dài.', 400)
        if selected not in original_answer:
            raise ServiceError('invalid_input', 'Đoạn được chọn không thuộc câu trả lời Tutor.', 400)
        question = original_question
    return {'course_context': course_context, 'original_question': question,
            'original_answer': original_answer, 'selected_text': selected}


def validate_chat_history(history):
    """Accept only a small, natural-language user/assistant transcript."""
    if not isinstance(history, list):
        raise ServiceError('invalid_input', 'Lịch sử hội thoại phải là một danh sách.', 400)
    if len(history) > MAX_HISTORY_MESSAGES:
        raise ServiceError('invalid_input', 'Lịch sử hội thoại vượt quá số lượt cho phép.', 400)
    cleaned = []
    total = 0
    for message in history:
        if not isinstance(message, dict) or set(message) != {'role', 'content'}:
            raise ServiceError('invalid_input', 'Tin nhắn lịch sử không hợp lệ.', 400)
        role, content = message['role'], message['content']
        if role not in {'user', 'assistant'}:
            raise ServiceError('invalid_input', 'Vai trò trong lịch sử không được phép.', 400)
        if not isinstance(content, str) or not content.strip() or len(content) > MAX_HISTORY_MESSAGE_CHARS:
            raise ServiceError('invalid_input', 'Nội dung lịch sử trống hoặc quá dài.', 400)
        total += len(content)
        if total > MAX_HISTORY_CHARS:
            raise ServiceError('invalid_input', 'Tổng lịch sử hội thoại quá dài.', 400)
        cleaned.append({'role': role, 'content': content.strip()})
    return cleaned


def chat_service_payload(payload):
    required = {'deck_id', 'page', 'question', 'history'}
    if not isinstance(payload, dict) or set(payload) != required:
        raise ServiceError('invalid_input', 'Cần deck_id, page, question và history.', 400)
    if not isinstance(payload['deck_id'], str) or not isinstance(payload['question'], str):
        raise ServiceError('invalid_input', 'Tham chiếu slide hoặc câu hỏi không hợp lệ.', 400)
    question = payload['question'].strip()
    if not question or len(question) > 2000:
        raise ServiceError('invalid_input', 'Hãy nhập một câu hỏi hợp lệ.', 400)
    history = validate_chat_history(payload['history'])
    record = page_record(payload['deck_id'], payload['page'])
    if record is None:
        raise ServiceError('invalid_slide', 'Không tìm thấy trang slide.', 404)
    related = search_slides({'query': question}).get('results', [])
    related_context = '\n\n'.join(
        f"{item['lesson']} · trang {item['page']}: {item['snippet']}"
        for item in related if item['id'] != record['id']
    )
    return {'question': question, 'course_context': record['page_text'],
            'related_context': related_context, 'history': history,
            'lesson': record['lesson_title'], 'page': record['page']}


def selection_live_payload(payload):
    if not isinstance(payload, dict):
        raise ServiceError('invalid_input', 'Thiếu dữ liệu đoạn văn bản được chọn.', 400)
    live_fields = {'history', 'current_request'}
    if not live_fields.issubset(payload):
        raise ServiceError('invalid_input', 'Thiếu lịch sử hoặc yêu cầu giải thích.', 400)
    history = validate_chat_history(payload['history'])
    current_request = payload['current_request']
    if not isinstance(current_request, str) or not current_request.strip() or len(current_request) > 2400:
        raise ServiceError('invalid_input', 'Yêu cầu giải thích không hợp lệ.', 400)
    ui_payload = {key: value for key, value in payload.items() if key not in live_fields}
    grounded = selection_service_payload(ui_payload)
    return {**grounded, 'history': history, 'current_request': current_request.strip()}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_args):
        pass  # Do not print request content or attacker-controlled paths.

    def reply(self, status, data, mime='application/json', allow_frame=False):
        body = data if isinstance(data, bytes) else json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', mime + '; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        frame_policy = "'self'" if allow_frame else "'none'"
        self.send_header('Content-Security-Policy', f"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors {frame_policy}")
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def allowed(self):
        port = self.server.server_port
        hosts = {f'127.0.0.1:{port}', f'localhost:{port}'}
        origin = self.headers.get('Origin')
        return self.headers.get('Host') in hosts and (not origin or origin in {f'http://{h}' for h in hosts})

    def do_GET(self):
        if not self.allowed():
            return self.reply(403, {'error': 'forbidden'})
        path = urlsplit(self.path).path
        if path == '/api/health':
            return self.reply(200, {'status': 'ok', 'api_key_configured': bool(configuration()[0])})
        if path == '/api/course-data':
            return self.reply(200, course_data())
        if path == '/api/slide-text-layer':
            query = parse_qs(urlsplit(self.path).query)
            try:
                data = slide_text_layer(query.get('deck_id', [''])[0], query.get('page', [''])[0])
                return self.reply(200, data)
            except ServiceError as exc:
                return self.reply(exc.status, {'error': exc.code, 'message': exc.message})
        if path == '/api/slide-image':
            query = parse_qs(urlsplit(self.path).query)
            deck_id, page = query.get('deck_id', [''])[0], query.get('page', [''])[0]
            if page_record(deck_id, page) is None:
                return self.reply(404, {'error': 'invalid_slide'})
            try:
                import fitz
                with fitz.open(SLIDE_FILES[DECKS[deck_id]['file']]) as document:
                    pixmap = document.load_page(int(page) - 1).get_pixmap(matrix=fitz.Matrix(1.7, 1.7), alpha=False)
                    return self.reply(200, pixmap.tobytes('png'), 'image/png')
            except ImportError:
                # The normal path is PyMuPDF. Poppler is a safe local fallback for
                # this managed runtime when the optional wheel is unavailable.
                renderer = shutil.which('pdftoppm')
                if not renderer:
                    return self.reply(503, {'error': 'renderer_unavailable'})
                temp_prefix = Path(tempfile.mktemp(prefix='vlearn-slide-', suffix=''))
                try:
                    subprocess.run([renderer, '-f', str(page), '-l', str(page), '-singlefile', '-png', '-r', '122', str(SLIDE_FILES[DECKS[deck_id]['file']]), str(temp_prefix)], capture_output=True, check=True, timeout=20)
                    image_path = Path(f'{temp_prefix}.png')
                    return self.reply(200, image_path.read_bytes(), 'image/png')
                except (OSError, subprocess.SubprocessError):
                    return self.reply(503, {'error': 'renderer_unavailable'})
                finally:
                    for candidate in (temp_prefix, Path(f'{temp_prefix}.png')):
                        try:
                            candidate.unlink()
                        except OSError:
                            pass
            except (OSError, KeyError, ValueError):
                return self.reply(503, {'error': 'renderer_unavailable'})
        if path not in PUBLIC:
            return self.reply(404, {'error': 'not_found'})
        name, mime = PUBLIC[path]
        self.reply(200, (ROOT / name).read_bytes(), mime)

    def do_POST(self):
        if not self.allowed():
            return self.reply(403, {'error': 'forbidden'})
        if self.path not in {'/api/explain', '/api/explain-selection', '/api/search', '/api/chat'}:
            return self.reply(404, {'error': 'not_found'})
        try:
            if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
                return self.reply(415, {'error': 'json_required'})
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 200000:
                return self.reply(413, {'error': 'invalid_size'})
            payload = json.loads(self.rfile.read(length))
            if self.path.split('?', 1)[0] == '/api/search':
                self.reply(200, search_slides(payload))
            elif self.path.split('?', 1)[0] == '/api/chat':
                self.reply(200, chat_answer_live(chat_service_payload(payload)))
            elif self.path.split('?', 1)[0] == '/api/explain-selection':
                self.reply(200, explain_selection_live(selection_live_payload(payload)))
            else:
                if not isinstance(payload, dict) or set(payload) != {'deck_id', 'page', 'original_question', 'original_answer', 'selected_text'}:
                    return self.reply(400, {'error': 'invalid_input', 'message': 'Thiếu tham chiếu slide.'})
                record = page_record(payload['deck_id'], payload['page'])
                if record is None:
                    return self.reply(404, {'error': 'invalid_slide', 'message': 'Không tìm thấy trang slide.'})
                grounded = dict(payload)
                grounded['course_context'] = record['page_text']
                grounded.pop('deck_id'); grounded.pop('page')
                self.reply(200, explain_selection(grounded)['result'])
        except ServiceError as exc:
            print(json.dumps({'event': 'api_error', 'stage': self.path.split('?', 1)[0],
                              'exception_class': type(exc).__name__, 'http_status': exc.status,
                              'service_error_code': exc.code}, ensure_ascii=True),
                  file=sys.stderr, flush=True)
            self.reply(exc.status, {'error': exc.code, 'message': exc.message})
        except (ValueError, UnicodeError):
            self.reply(400, {'error': 'invalid_json', 'message': 'Dữ liệu gửi lên không hợp lệ.'})
        except Exception as exc:
            print(json.dumps({'event': 'api_error', 'stage': self.path.split('?', 1)[0],
                              'exception_class': type(exc).__name__, 'http_status': 500,
                              'service_error_code': 'internal_error'}, ensure_ascii=True),
                  file=sys.stderr, flush=True)
            self.reply(500, {'error': 'internal_error', 'message': 'Backend gặp lỗi. Hãy thử lại.'})


def serve(handler=Handler, default_port=8000):
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=default_port)
    args = parser.parse_args()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), handler)
    print(f'Local server: http://127.0.0.1:{args.port}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    serve()
