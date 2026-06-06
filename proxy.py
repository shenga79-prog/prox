# proxy.py
import socket
import threading
import os
import sys

# ПРИНУДИТЕЛЬНЫЙ ВЫВОД В ЛОГИ
print("="*60, flush=True)
print("🚀 ПРОКСИ СЕРВЕР ЗАПУСКАЕТСЯ", flush=True)
print("="*60, flush=True)

# Получаем порт
PORT = int(os.environ.get('PORT', 8080))
print(f"📡 Порт: {PORT}", flush=True)

# Показываем ВСЕ переменные окружения (для отладки)
print("\n🔍 ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ:", flush=True)
for key, value in os.environ.items():
    if 'URL' in key or 'HOST' in key or 'DOMAIN' in key:
        print(f"   {key}: {value}", flush=True)

# Показываем главную ссылку
print("\n" + "="*60, flush=True)
print("✅ ПРОКСИ ДОСТУПЕН:", flush=True)
print(f"   http://localhost:{PORT}", flush=True)
print(f"   http://0.0.0.0:{PORT}", flush=True)
print("="*60 + "\n", flush=True)

# Форсируем вывод (заставляем показать сразу)
sys.stdout.flush()

class Proxy:
    def __init__(self):
        self.port = PORT
        self.host = '0.0.0.0'
        
    def start(self):
        try:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((self.host, self.port))
            server.listen(100)
            
            print(f"✅ Сервер запущен и слушает порт {self.port}", flush=True)
            print(f"🟢 Ожидание подключений...\n", flush=True)
            
            while True:
                client, addr = server.accept()
                print(f"📱 Подключение от {addr}", flush=True)
                threading.Thread(target=self.handle, args=(client,), daemon=True).start()
                
        except Exception as e:
            print(f"❌ ОШИБКА: {e}", flush=True)
            
    def handle(self, client):
        try:
            data = client.recv(4096)
            if not data:
                return
            
            first = data.split(b'\n')[0].decode()
            method = first.split(' ')[0]
            url = first.split(' ')[1]
            
            print(f"📨 {method} {url[:50]}", flush=True)
            
            # CONNECT (HTTPS)
            if method == 'CONNECT':
                host_port = url.split(':')
                host = host_port[0]
                port = int(host_port[1]) if len(host_port) > 1 else 443
                
                client.send(b'HTTP/1.1 200 Connection Established\r\n\r\n')
                
                remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                remote.connect((host, port))
                
                threading.Thread(target=self.forward, args=(client, remote)).start()
                self.forward(remote, client)
                
            else:
                # HTTP
                if url.startswith('http://'):
                    url = url[7:]
                
                if '/' in url:
                    host = url.split('/')[0]
                    path = '/' + '/'.join(url.split('/')[1:])
                else:
                    host = url
                    path = '/'
                
                port = 80
                if ':' in host:
                    host, port = host.split(':')
                    port = int(port)
                
                remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                remote.connect((host, port))
                
                req_str = data.decode()
                lines = req_str.split('\r\n')
                lines[0] = f"{method} {path} HTTP/1.1"
                
                has_host = False
                for i, line in enumerate(lines):
                    if line.lower().startswith('host:'):
                        has_host = True
                        break
                
                if not has_host:
                    lines.insert(1, f"Host: {host}")
                
                new_req = '\r\n'.join(lines).encode()
                remote.send(new_req)
                
                while True:
                    resp = remote.recv(4096)
                    if not resp:
                        break
                    client.send(resp)
                
                remote.close()
                
        except Exception as e:
            print(f"⚠️ Ошибка: {e}", flush=True)
        finally:
            client.close()
            
    def forward(self, source, dest):
        try:
            while True:
                data = source.recv(4096)
                if not data:
                    break
                dest.send(data)
        except:
            pass

# ЗАПУСК
if __name__ == '__main__':
    print("🚀 Запуск прокси...", flush=True)
    proxy = Proxy()
    try:
        proxy.start()
    except KeyboardInterrupt:
        print("\n🛑 Остановка...", flush=True)
