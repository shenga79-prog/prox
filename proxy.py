# proxy.py - ИСПРАВЛЕННАЯ ВЕРСИЯ
import socket
import threading
import os

PORT = int(os.environ.get('PORT', 8080))
HOST = '0.0.0.0'

print(f"🚀 Прокси запущен на {HOST}:{PORT}")

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
        
        print(f"{method} {url}")
        
        # ДЛЯ HTTPS
        if method == 'CONNECT':
            host_port = url.split(':')
            host = host_port[0]
            port = int(host_port[1]) if len(host_port) > 1 else 443
            
            client_socket.send(b'HTTP/1.1 200 Connection Established\r\n\r\n')
            
            remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote.connect((host, port))
            
            threading.Thread(target=forward, args=(client_socket, remote)).start()
            forward(remote, client_socket)
            
        # ДЛЯ HTTP
        else:
            # Извлекаем хост
            if url.startswith('http://'):
                url = url[7:]
            
            # Получаем хост и путь
            if '/' in url:
                host = url.split('/')[0]
                path = '/' + '/'.join(url.split('/')[1:])
            else:
                host = url
                path = '/'
            
            # Убираем порт из хоста если есть
            host = host.split(':')[0]
            
            print(f"  -> HTTP запрос к {host}")
            
            # Подключаемся к серверу
            remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote.settimeout(10)
            remote.connect((host, 80))
            
            # Формируем новый запрос
            request_str = request.decode('utf-8', errors='ignore')
            lines = request_str.split('\r\n')
            
            # Меняем первую строку
            lines[0] = f"{method} {path} HTTP/1.1"
            
            # Убираем старый Host и добавляем новый
            new_lines = []
            for line in lines:
                if not line.lower().startswith('host:'):
                    new_lines.append(line)
            
            # Добавляем Host в начало
            new_lines.insert(1, f"Host: {host}")
            
            new_request = '\r\n'.join(new_lines).encode()
            
            print(f"  -> Отправка запроса")
            remote.send(new_request)
            
            # Получаем ответ
            while True:
                response = remote.recv(8192)
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
server.bind((HOST, PORT))
server.listen(100)

print("✅ ПРОКСИ РАБОТАЕТ")
print(f"📡 HTTP и HTTPS поддерживаются")
print("="*50)

while True:
    client, addr = server.accept()
    print(f"\n📱 Подключение от {addr}")
    threading.Thread(target=handle_client, args=(client,)).start()
