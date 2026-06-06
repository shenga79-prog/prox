# proxy.py
import socket
import threading
import os

print("\n" + "="*60)
print("🚀 ЗАПУСК ПРОКСИ СЕРВЕРА")
print("="*60)

# Получаем порт от Railway
PORT = int(os.environ.get('PORT', 8080))

print(f"\n✅ ПРОКСИ ДОСТУПЕН ПО АДРЕСУ:")
print(f"   http://localhost:{PORT}")
print(f"\n📱 ДЛЯ ТЕЛЕФОНА (IPHONE):")
print(f"   Сервер: localhost")
print(f"   Порт: {PORT}")
print("="*60 + "\n")

def handle_client(client_socket):
    try:
        request = client_socket.recv(4096)
        if not request:
            return
        
        first_line = request.split(b'\n')[0].decode()
        method = first_line.split(' ')[0]
        url = first_line.split(' ')[1]
        
        # CONNECT метод (HTTPS)
        if method == 'CONNECT':
            host_port = url.split(':')
            host = host_port[0]
            port = int(host_port[1]) if len(host_port) > 1 else 443
            
            client_socket.send(b'HTTP/1.1 200 Connection Established\r\n\r\n')
            
            remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote.connect((host, port))
            
            threading.Thread(target=forward, args=(client_socket, remote)).start()
            forward(remote, client_socket)
        
        # HTTP метод
        else:
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
            
            # Модифицируем запрос
            request_str = request.decode()
            lines = request_str.split('\r\n')
            lines[0] = f"{method} {path} HTTP/1.1"
            
            has_host = False
            for i, line in enumerate(lines):
                if line.lower().startswith('host:'):
                    has_host = True
                    break
            
            if not has_host:
                lines.insert(1, f"Host: {host}")
            
            new_request = '\r\n'.join(lines).encode()
            remote.send(new_request)
            
            while True:
                response = remote.recv(4096)
                if not response:
                    break
                client_socket.send(response)
            
            remote.close()
            
    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        client_socket.close()

def forward(source, dest):
    try:
        while True:
            data = source.recv(4096)
            if not data:
                break
            dest.send(data)
    except:
        pass

# Запускаем сервер
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(('0.0.0.0', PORT))
server.listen(100)

print(f"🟢 Прокси запущен и слушает порт {PORT}")
print(f"🟢 Ожидание подключений...\n")

while True:
    client, addr = server.accept()
    print(f"📱 Подключился: {addr}")
    threading.Thread(target=handle_client, args=(client,)).start()
    
