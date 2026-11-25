import socket
import threading
from cryptography.fernet import Fernet
import os

KEY_FILE = "secret.key"

def receive_messages(client_socket, cipher_suite):
    """Поток для постоянного получения и расшифровки сообщений от сервера"""
    while True:
        try:
            encrypted_message = client_socket.recv(1024)
            if not encrypted_message:
                break
            message = cipher_suite.decrypt(encrypted_message).decode('utf-8')
            print(f"\n{message}")
            print("Введите сообщение: ", end="", flush=True)
        except Exception:
            print("\nСоединение с сервером разорвано.")
            break

def start_client():
    if not os.path.exists(KEY_FILE):
        print(f"Ошибка: Файл ключа '{KEY_FILE}' не найден. Сначала запустите server.py")
        return

    with open(KEY_FILE, "rb") as key_file:
        key = key_file.read()
    cipher_suite = Fernet(key)

    host = input("Введите адрес сервера (по умолчанию 127.0.0.1): ").strip() or '127.0.0.1'
    try:
        port_input = input("Введите порт сервера (по умолчанию 12345): ").strip()
        port = int(port_input) if port_input else 12345
    except ValueError:
        print("Некорректный порт. Используется 12345")
        port = 12345

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        client_socket.connect((host, port))
        print("Успешно подключено к серверу!")
    except Exception as e:
        print(f"Ошибка подключения: {e}")
        return

    receive_thread = threading.Thread(target=receive_messages, args=(client_socket, cipher_suite))
    receive_thread.daemon = True
    receive_thread.start()

    while True:
        try:
            message = input("Введите сообщение: ")
            if message.lower() == 'выход':
                break
            
            encrypted_message = cipher_suite.encrypt(message.encode('utf-8'))
            client_socket.send(encrypted_message)
        except Exception as e:
            print(f"Ошибка отправки: {e}")
            break

    client_socket.close()
    print("Соединение закрыто.")

if __name__ == "__main__":
    start_client()