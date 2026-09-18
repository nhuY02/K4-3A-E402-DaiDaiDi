"""Loopback-only backend; explicit public-file allowlist keeps .env/logs private."""
import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

from ai_service import ROOT, ServiceError, chat_answer, configuration, explain_selection
from slide_search import DECKS, page_record, search_slides

PUBLIC = {'/': ('index.html', 'text/html'), '/index.html': ('index.html', 'text/html'),
          '/app.js': ('app.js', 'text/javascript'), '/styles.css': ('styles.css', 'text/css'),
          '/selection.css': ('selection.css', 'text/css')}
SLIDE_FILES = {
    'd1-slide-hackathon.pdf': ROOT / 'K4-3A-Day05-06-AI-Product-Hackathon' / 'data' / 'vlearn-pack' / 'slides' / 'd1-slide-hackathon.pdf',
    'd2-slide-hackathon.pdf': ROOT / 'K4-3A-Day05-06-AI-Product-Hackathon' / 'data' / 'vlearn-pack' / 'slides' / 'd2-slide-hackathon.pdf',
}
MAX_SELECTED_TEXT = 2000

def course_data():
    return {'lessons': [{'id': meta['id'], 'title': meta['title'], 'deck_id': deck_id,
                         'pages': 29} for deck_id, meta in DECKS.items()]}


def slide_text_layer(deck_id, page):
    """Return visible words and normalized PDF coordinates for one allowlisted page."""
    record = page_record(deck_id, page)
    if record is None:
        raise ServiceError('invalid_slide', 'Không tìm thấy trang slide.', 404)
    try:
        import fitz
    except ImportError as exc:
        raise ServiceError('renderer_unavailable', 'Không thể đọc lớp văn bản của slide.', 503) from exc
    try:
        with fitz.open(SLIDE_FILES[DECKS[record['deck_id']]['file']]) as document:
            pdf_page = document.load_page(int(page) - 1)
            width, height = float(pdf_page.rect.width), float(pdf_page.rect.height)
            items = []
            horizontal_boxes = []
            for block in pdf_page.get_text('dict').get('blocks', []):
                if block.get('type') != 0:
                    continue
                for line in block.get('lines', []):
                    direction = line.get('dir', (1.0, 0.0))
                    if direction[0] > 0.98 and abs(direction[1]) < 0.02:
                        horizontal_boxes.append(tuple(line['bbox']))
            for x0, y0, x1, y1, text, block_no, line_no, word_no in pdf_page.get_text('words'):
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
                              'word': int(word_no)})
    except (OSError, KeyError, ValueError, RuntimeError) as exc:
        raise ServiceError('renderer_unavailable', 'Không thể đọc lớp văn bản của slide.', 503) from exc
    return {'deck_id': DECKS[record['deck_id']]['id'], 'page': int(page),
            'width': width, 'height': height, 'items': items}


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
    if payload['source'] == 'slide':
        normalize = lambda value: ' '.join(value.split()).casefold()
        if normalize(selected) not in normalize(record['page_text']):
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
    return {'course_context': record['page_text'], 'original_question': question,
            'original_answer': original_answer, 'selected_text': selected}


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
                if not isinstance(payload, dict) or set(payload) != {'deck_id', 'page', 'question'}:
                    return self.reply(400, {'error': 'invalid_input', 'message': 'Cần deck_id, page và question.'})
                if not isinstance(payload['deck_id'], str) or not isinstance(payload['question'], str):
                    return self.reply(400, {'error': 'invalid_input', 'message': 'Tham chiếu slide hoặc câu hỏi không hợp lệ.'})
                if not payload['question'].strip() or len(payload['question']) > 2000:
                    return self.reply(400, {'error': 'invalid_input', 'message': 'Hãy nhập một câu hỏi hợp lệ.'})
                record = page_record(payload['deck_id'], payload['page'])
                if record is None:
                    return self.reply(404, {'error': 'invalid_slide', 'message': 'Không tìm thấy trang slide.'})
                related = search_slides({'query': payload['question']}).get('results', [])
                related_context = '\n\n'.join(
                    f"{item['lesson']} · trang {item['page']}: {item['snippet']}"
                    for item in related if item['id'] != record['id']
                )
                self.reply(200, chat_answer({'question': payload['question'],
                                             'course_context': record['page_text'],
                                             'related_context': related_context}) )
            elif self.path.split('?', 1)[0] == '/api/explain-selection':
                grounded = selection_service_payload(payload)
                self.reply(200, explain_selection(grounded)['result'])
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
