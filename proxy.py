# proxy.py - с обработкой health check
import socket
import threading
import os

PORT = int(os.environ.get('PORT', 8080))
HOST = '0.0.0.0'

print(f"🚀 Прокси запускается на порту {PORT}")

def handle_client(client_socket):
    try:
        request = client_socket.recv(4096)
        if not request:
            client_socket.close()
            return
        
        first_line = request.split(b'\n')[0].decode()
        parts = first_line.split(' ')
        
        if len(parts) < 2:
            client_socket.close()
            return
            
        method = parts[0]
        url = parts[1]
        
        # Для health check (GET /)
        if url == '/' or url == '/favicon.ico':
            client_socket.send(b'HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nOK')
            client_socket.close()
            return
        
        print(f"📨 {method} {url[:50]}")
        
        # HTTPS
        if method == 'CONNECT':
            host_port = url.split(':')
            host = host_port[0]
            port = int(host_port[1]) if len(host_port) > 1 else 443
            
            client_socket.send(b'HTTP/1.1 200 Connection Established\r\n\r\n')
            
            remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote.connect((host, port))
            
            threading.Thread(target=forward, args=(client_socket, remote)).start()
            forward(remote, client_socket)
            
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
            
            host = host.split(':')[0]
            
            remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote.connect((host, 80))
            remote.send(request)
            
            while True:
                response = remote.recv(8192)
                if not response:
                    break
                client_socket.send(response)
            
            remote.close()
            
    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        try:
            client_socket.close()
        except:
            pass

def forward(source, dest):
    try:
        while True:
            data = source.recv(4096)
            if not data:
                break
            dest.send(data)
    except:
        pass

# Запуск
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen(100)

print("="*40)
print("✅ ПРОКСИ РАБОТАЕТ")
print(f"📡 Порт: {PORT}")
print("="*40)

while True:
    client, addr = server.accept()
    threading.Thread(target=handle_client, args=(client,), daemon=True).start()
