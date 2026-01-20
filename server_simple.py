import http.server
import socketserver
import os
import json
import config
from urllib.parse import urlparse, parse_qs

PORT = config.SERVER_PORT
UPLOAD_FOLDER = config.UPLOADS_DIR
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_HEAD(self):
        self.serve_request(send_body=False)

    def do_GET(self):
        self.serve_request(send_body=True)

    def serve_request(self, send_body=True):
        print(f"DEBUG: {self.command} path={self.path}")
        
        # Эндпоинт проверки здоровья
        if '/health' in self.path:
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            if send_body:
                self.wfile.write(json.dumps({"status": "ok"}).encode())
            return

        filename = None
        
        # Пытаемся вычленить имя файла из любого пути
        # Обрабатываем /webhook?file=...
        if 'file=' in self.path:
            try:
                query = parse_qs(urlparse(self.path).query)
                filename = query.get('file', [None])[0]
            except: pass
        
        # Если имя файла не найдено в query, берем последнюю часть пути (для /static/file.mp4)
        if not filename:
            filename = os.path.basename(urlparse(self.path).path)

        if filename and filename.endswith('.mp4'):
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            
            if os.path.exists(file_path):
                try:
                    file_size = os.path.getsize(file_path)
                    self.send_response(200)
                    self.send_header("Content-Type", "video/mp4")
                    self.send_header("Content-Length", str(file_size))
                    self.send_header("Accept-Ranges", "bytes")
                    self.end_headers()
                    
                    if send_body:
                        with open(file_path, 'rb') as f:
                            import shutil
                            shutil.copyfileobj(f, self.wfile)
                        print(f"DEBUG: Отправлен файл {filename} ({file_size} байт)")
                except Exception as e:
                    print(f"ERROR: {e}")
            else:
                print(f"DEBUG: Файл не найден: {file_path}")
                self.send_response(404)
                self.end_headers()
            return

        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        if '/webhook' in self.path:
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "accepted"}).encode())
        else:
            self.send_response(404)
            self.end_headers()

print(f"Старт сервера на порту {PORT}...")
socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("", PORT), Handler) as httpd:
    httpd.serve_forever()
