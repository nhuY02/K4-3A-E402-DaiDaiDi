"""Serve only public assets and proxy the one AI endpoint to loopback backend."""
import http.client

from server import Handler, serve


class Frontend(Handler):
    def do_GET(self):
        if not self.allowed():
            return self.reply(403, {'error': 'forbidden'})
        if self.path.split('?', 1)[0] not in {'/api/course-data', '/api/slide-image'}:
            return super().do_GET()
        try:
            connection = http.client.HTTPConnection('127.0.0.1', 8000, timeout=20)
            try:
                connection.request('GET', self.path)
                response = connection.getresponse()
                body = response.read()
                self.reply(response.status, body, response.getheader('Content-Type', 'application/json').split(';')[0])
            finally:
                connection.close()
        except (OSError, http.client.HTTPException):
            self.reply(503, {'error': 'backend_unavailable', 'message': 'Chưa kết nối được backend. Hãy chạy python server.py.'})

    def do_POST(self):
        if not self.allowed():
            return self.reply(403, {'error': 'forbidden'})
        if self.path not in {'/api/explain', '/api/search', '/api/chat'}:
            return self.reply(404, {'error': 'not_found'})
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 200000:
                return self.reply(413, {'error': 'invalid_size'})
            body = self.rfile.read(length)
            connection = http.client.HTTPConnection('127.0.0.1', 8000, timeout=55)
            try:
                connection.request('POST', self.path, body, {'Content-Type': self.headers.get('Content-Type', '')})
                response = connection.getresponse()
                self.reply(response.status, response.read())
            finally:
                connection.close()
        except (OSError, http.client.HTTPException):
            self.reply(503, {'error': 'backend_unavailable', 'message': 'Chưa kết nối được backend. Hãy chạy python server.py.'})
        except ValueError:
            self.reply(400, {'error': 'invalid_size'})


if __name__ == '__main__':
    serve(Frontend, 5173)
