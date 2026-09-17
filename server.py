"""Loopback-only backend; explicit public-file allowlist keeps .env/logs private."""
import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

from ai_service import ROOT, ServiceError, chat_answer, configuration, explain_selection
from slide_search import DECKS, page_record, search_slides

PUBLIC = {'/': ('index.html', 'text/html'), '/index.html': ('index.html', 'text/html'),
          '/app.js': ('app.js', 'text/javascript'), '/styles.css': ('styles.css', 'text/css')}
SLIDE_FILES = {
    'd1-slide-hackathon.pdf': ROOT / 'K4-3A-Day05-06-AI-Product-Hackathon' / 'data' / 'vlearn-pack' / 'slides' / 'd1-slide-hackathon.pdf',
    'd2-slide-hackathon.pdf': ROOT / 'K4-3A-Day05-06-AI-Product-Hackathon' / 'data' / 'vlearn-pack' / 'slides' / 'd2-slide-hackathon.pdf',
}

def course_data():
    return {'lessons': [{'id': meta['id'], 'title': meta['title'], 'deck_id': deck_id,
                         'pages': 29} for deck_id, meta in DECKS.items()]}


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
        if self.path not in {'/api/explain', '/api/search', '/api/chat'}:
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
            self.reply(exc.status, {'error': exc.code, 'message': exc.message})
        except (ValueError, UnicodeError):
            self.reply(400, {'error': 'invalid_json', 'message': 'Dữ liệu gửi lên không hợp lệ.'})
        except Exception:
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
