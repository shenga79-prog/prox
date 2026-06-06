# test.py - минимальный тест
import os

PORT = os.environ.get('PORT', 8080)

print("="*50)
print("ТЕСТОВЫЙ СЕРВЕР ЗАПУЩЕН")
print("="*50)
print(f"Порт: {PORT}")
print("="*50)

# Простой HTTP сервер
from http.server import HTTPServer, BaseHTTPRequestHandler

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        html = f"""
        <html>
        <body>
            <h1>✅ Сервер работает!</h1>
            <p>Порт: {PORT}</p>
            <p>Ваш IP: {self.client_address[0]}</p>
        </body>
        </html>
        """
        self.wfile.write(html.encode())
    
    def log_message(self, format, *args):
        print(f"Запрос: {args}")

print(f"Запуск HTTP сервера на порту {PORT}...")
server = HTTPServer(('0.0.0.0', int(PORT)), Handler)
print("Сервер готов! Ожидание запросов...")
server.serve_forever()
