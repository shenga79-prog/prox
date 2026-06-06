# proxy.py - ПОЛНОСТЬЮ РАБОЧАЯ ВЕРСИЯ
import socket
import threading
import os

PORT = int(os.environ.get('PORT', 8080))
HOST = '0.0.0.0'

print(f"🚀 Прокси сервер запущен на {HOST}:{PORT}")
print(f"✅ Поддерживаются HTTP и HTTPS запросы")

def forward(source, dest):
    try:
        while True:
            data = source.recv(4096)
            if not data:
                break
            dest.send(data)
    except:
        pass

def handle_client(client_socket):
    try:
        # Получаем запрос
        request = client_socket.recv(4096)
        if not request:
            client_socket.close()
            return
        
        # Разбираем первую строку
        first_line = request.split(b'\n')[0].decode()
        parts = first_line.split(' ')
        
        if len(parts) < 2:
            client_socket.close()
            return
            
        method = parts[0]
        url = parts[1]
        
        print(f"📨 {method} {url}")
        
        # Обработка HTTPS (CONNECT)
        if method == 'CONNECT':
            host_port = url.split(':')
            host = host_port[0]
            port = int(host_port[1]) if len(host_port) > 1 else 443
            
            print(f"  🔒 HTTPS туннель к {host}:{port}")
            
            # Отправляем успешный ответ
            client_socket.send(b'HTTP/1.1 200 Connection Established\r\n\r\n')
            
            # Создаем туннель
            remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote.connect((host, port))
            
            # Двусторонняя передача
            threading.Thread(target=forward, args=(client_socket, remote)).start()
            forward(remote, client_socket)
            
        else:
            # Обработка HTTP
            # Полный URL или путь?
            if url.startswith('http://'):
                full_url = url[7:]
            elif url.startswith('https://'):
                full_url = url[8:]
            else:
                full_url = url
            
            # Извлекаем хост и путь
            if '/' in full_url:
                host = full_url.split('/')[0]
                path = '/' + '/'.join(full_url.split('/')[1:])
            else:
                host = full_url
                path = '/'
            
            # Убираем порт из хоста
            if ':' in host:
                host = host.split(':')[0]
            
            print(f"  🌐 HTTP запрос к {host}{path}")
            
            # Подключаемся к серверу
            remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote.connect((host, 80))
            
            # Формируем HTTP запрос
            # Разбираем исходный запрос
            request_str = request.decode('utf-8', errors='ignore')
            lines = request_str.split('\r\n')
            
            # Меняем первую строку (убираем полный URL)
            lines[0] = f"{method} {path} HTTP/1.1"
            
            # Перестраиваем заголовки
            new_lines = []
            host_added = False
            
            for line in lines:
                lower_line = line.lower()
                if lower_line.startswith('host:'):
                    new_lines.append(f"Host: {host}")
                    host_added = True
                elif lower_line.startswith('proxy-'):
                    # Пропускаем proxy-заголовки
                    continue
                else:
                    new_lines.append(line)
            
            # Добавляем Host если его не было
            if not host_added:
                new_lines.insert(1, f"Host: {host}")
            
            # Собираем запрос
            new_request = '\r\n'.join(new_lines).encode()
            
            # Отправляем
            remote.send(new_request)
            
            # Получаем ответ и отправляем клиенту
            while True:
                response = remote.recv(8192)
                if not response:
                    break
                client_socket.send(response)
            
            remote.close()
            
    except Exception as e:
        print(f"  ❌ Ошибка: {e}")
    finally:
        try:
            client_socket.close()
        except:
            pass

# Запуск сервера
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen(100)

print("="*50)
print("✅ ПРОКСИ ГОТОВ К РАБОТЕ")
print(f"📡 Порт: {PORT}")
print("="*50)

while True:
    client, addr = server.accept()
    print(f"\n🔗 Новое подключение: {addr}")
    threading.Thread(target=handle_client, args=(client,)).start()
