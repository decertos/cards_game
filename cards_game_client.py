import socket
import requests.exceptions
from requests import get

print("Правила игры:")
print("Все стандартные правила. Чтобы взять карты или сказать 'Бито', в поле ввода номера карты напишите -1.")
print("Соседи пока что не могут подкидывать карты.")
print("")

print("Cards Game [Version 2.7]")
print("CLIENT VERSION")

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print("Проверка наличия подключения к Интернету...")
try:
    get("https://example.com")
    print("Интернет доступен")
    server = input("Введите адрес сервера: ")
except requests.exceptions.ConnectionError:
    print("Отсутствует подключение к Интернету, можно подключиться только к адресу 127.0.0.1")
    server = "127.0.0.1"

port = int(input("Введите порт: "))

print(f"Подключение к серверу с адресом {server} и портом {port}...")
try:
    client.connect((server, port))
except ConnectionRefusedError:
    print("Сервер найден, но на нём не запущена серверная версия игры.")
    exit(0)
except socket.gaierror:
    print(f"Не найдено сервера с адресом {server} и портом {port}.")
    exit(0)
print("Успешно подключен")

while True:
    try:
        data = client.recv(4096).decode().split(";")
        print(data)
        print(data[0])
        if data[0] and "close_input" not in data:
            print(True)
            out_data = input()
            client.sendall(bytes(out_data, "UTF-8"))
    except ConnectionResetError:
        print("Сервер отключен.")
        break
    except ConnectionAbortedError:
        print("Сервер отключен.")
        break
