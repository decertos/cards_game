from random import choice, shuffle, randint
import socket
from datetime import datetime

import requests.exceptions
from requests import get
import segno

card_values = {"6": 6, "7": 7, "8": 8, "9": 9, "10": 10, "В": 11, "Д": 12, "К": 13, "Т": 14}

players = []
print("Cards Game [Version 2.7e]")
print("SERVER VERSION")
while True:
    try:
        player_amount = int(input("Введите количество игроков (максимально 6): "))
        if 1 < player_amount < 7:
            break
        raise ValueError
    except ValueError:
        print("Количество игроков может быть от 2 до 6.")
server_players = 0
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host = "127.0.0.1"  # выберите любой другой IP-адрес для подключения

print(f"{datetime.now().strftime("%H:%M:%S")} [info] Проверка наличия подключения к Интернету...")
try:
    get("https://example.com")
    print("[info] Интернет доступен")
    print(f"{datetime.now().strftime("%H:%M:%S")} [info] Пинг от example.com: ",
          get("https://example.com").elapsed.microseconds // 1000, "ms", sep="")
    host = "192.168.0.120"
except requests.exceptions.ConnectionError:
    print("[info] Отсутствует подключение к Интернету, сервер может быть запущен на адресе 127.0.0.1")
    host = "127.0.0.1"

print("Хост сервера:", host)

while True:
    random_port = randint(0, 65536)
    port = input(f"Введите порт сервера (нажмите Enter для порта {random_port}): ")
    if port == "":
        port = random_port
        break
    else:
        if -1 < int(port) < 65536:
            port = int(port)
            break
        else:
            print("Значение порта должно быть от 0 до 65535.")

server.bind((host, port))
server.listen(player_amount)
player_sockets = []
print(f"{datetime.now().strftime("%H:%M:%S")} [info] Сервер запущен")
connect_qr = segno.make_qr(f"({host}, {port})")
connect_qr.save("connect_qr.png")
connect_qr.show()


class Player:
    def __init__(self, name, index):
        self.nickname = name
        self.index = index
        self.cards = ["" for i in range(6)]

    def attacker_step(self, player, played_cards):
        played_values = []
        for i in played_cards:
            played_values.append(10 if len(i) == 3 else card_values[i[0]])
        while True:
            if len(self.cards) == 0:
                return "win"
            player_sockets[self.index].send(bytes(f"Колода: {self.cards};"
                                                  f"Сыгранные карты: {played_cards};"
                                                  f"{self.nickname}, выберите карту из своей колоды для "
                                                  f"игрока {player.nickname}:", "UTF-8"))
            player_step = int(player_sockets[self.index].recv(1024).decode())
            if player_step == -1:
                return "attacker_end"
            if player_step < 0 or len(self.cards) < player_step:
                player_sockets[self.index].send(
                    bytes(f"Нужно ввести число от 1 до {len(self.cards)}.;close_input", "UTF-8"))
            else:
                card_value = 10 if len(self.cards[player_step - 1]) == 3 else card_values[
                    self.cards[player_step - 1][0]]
                if player_step == -1:
                    player_sockets[self.index].send(bytes(f"Ожидайте хода {player.nickname};close_input", "UTF-8"))
                    return "attacker_end"
                if not played_cards:
                    player_sockets[self.index].send(bytes(f"Ожидайте хода {player.nickname};close_input", "UTF-8"))
                    return self.cards.pop(player_step - 1)
                if card_value in played_values:
                    player_sockets[self.index].send(bytes(f"Ожидайте хода {player.nickname};close_input", "UTF-8"))
                    return self.cards.pop(player_step - 1)
                else:
                    player_sockets[self.index].send(bytes("Можно подложить только карты со значением, сыгранным "
                                                          "ранее.;close_input", "UTF-8"))

    def attacked_step(self, played_cards, is_trump_card, trump_suit):
        attacked_played_cards = []
        player_sockets[self.index].send(
            bytes(f"Колода: {self.cards};Карты для покрытия: {played_cards};close_input", "UTF-8"))
        i = 0
        while i != len(played_cards):
            if len(self.cards) == 0:
                return "win", []
            card_value = 10 if len(played_cards[i]) == 3 else card_values[played_cards[i][0]]
            card_suit = played_cards[i][-1]
            player_sockets[self.index].send(
                bytes(f"{self.nickname}, выберите карту из своей колоды против карты {played_cards[i]}:", "UTF-8"))
            player_step = int(player_sockets[self.index].recv(1024).decode())
            if player_step == -1:
                player_sockets[self.index].send(bytes(f"Ожидайте своего хода;close_input", "UTF-8"))
                return "attacked_end", attacked_played_cards
            if player_step < 0 or len(self.cards) < player_step:
                player_sockets[self.index].send(
                    bytes(f"Нужно ввести число от 1 до {len(self.cards)}.;close_input", "UTF-8"))
            else:
                selected_card_value = 10 if len(self.cards[player_step - 1]) == 3 \
                    else card_values[self.cards[player_step - 1][0]]
                if card_value == selected_card_value:
                    attacked_played_cards.append(self.cards[player_step - 1])
                    self.cards.pop(player_step - 1)
                    return "to_the_next", attacked_played_cards
                if not is_trump_card:
                    if card_value < selected_card_value and self.cards[player_step - 1][-1] == card_suit:
                        attacked_played_cards.append(self.cards[player_step - 1])
                        self.cards.pop(player_step - 1)
                        i += 1
                    elif self.cards[player_step - 1][-1] == trump_suit:
                        attacked_played_cards.append(self.cards[player_step - 1])
                        self.cards.pop(player_step - 1)
                        i += 1
                    else:
                        player_sockets[self.index].send(
                            bytes(f"Нужно положить либо карту с мастью {card_suit} большего "
                                  f"значения, чем {played_cards[i]}, "
                                  f"либо положить карту с мастью {trump_suit}.;close_input", "UTF-8"))
                else:
                    if card_value < selected_card_value and self.cards[player_step - 1][-1] == trump_suit:
                        attacked_played_cards.append(self.cards[player_step - 1])
                        self.cards.pop(player_step - 1)
                        i += 1
                    else:
                        player_sockets[self.index].send(bytes(
                            f"Нужно положить карту с мастью {trump_suit} большего значения, чем {played_cards[i]}.;close_input",
                            "UTF-8"))
        player_sockets[self.index].send(bytes(f"Ожидайте хода атакующего;close_input", "UTF-8"))
        return "normal_step", attacked_played_cards


def send_all(message):
    for i in player_sockets:
        i.send(bytes(message, "UTF-8"))


for i in range(player_amount):
    client_socket, addr = server.accept()
    player_sockets.append(client_socket)
    print(f"{datetime.now().strftime("%H:%M:%S")} [users] Подключен пользователь {addr}")
    player_sockets[i].send(bytes("Введите никнейм:", "UTF-8"))
    server_players += 1
    data = client_socket.recv(1024).decode()
    players.append(Player(data, i))
    print(f"{datetime.now().strftime("%H:%M:%S")} [info] Добавлен игрок {data}")
    send_all(f"Подключен игрок {data}.;close_input")
    send_all(f"Ожидание игроков: {server_players}/{player_amount} игроков подключилось.;close_input")
    print(
        f"[info] Подключено {server_players}/{player_amount} игроков. Ожидание ещё {player_amount - server_players} игроков")

send_all("Запуск игры...;close_input")

all_cards = ["6♠", "7♠", "8♠", "9♠", "10♠", "В♠", "Д♠", "К♠", "Т♠",
             "6♥", "7♥", "8♥", "9♥", "10♥", "В♥", "Д♥", "К♥", "Т♥",
             "6♦", "7♦", "8♦", "9♦", "10♦", "В♦", "Д♦", "К♦", "Т♦",
             "6♣", "7♣", "8♣", "9♣", "10♣", "В♣", "Д♣", "К♣", "Т♣"]
shuffle(all_cards)

if len(players) <= 6:
    for i in players:
        i.cards = all_cards[:6]
        all_cards = all_cards[6:]

if not all_cards:
    trump_suit = choice(["♠", "♥", "♦", "♣"])
else:
    trump_suit = all_cards[0][-1]
attacker = players[0]
attacked = players[1]
round_cards = []
cards_to_cover = []
send_all(f"Козырь: {trump_suit};close_input")


def who_is_next(player_index, player_amount):
    if player_index + 1 == player_amount:
        return 0
    return player_index + 1


def new_round():
    global attacker, attacked, round_cards, cards_to_cover
    round_cards = []
    cards_to_cover = []
    while len(attacker.cards) < 6:
        if 0 < len(all_cards):
            attacker.cards.append(all_cards[0])
            all_cards.pop(0)
        else:
            return "no_cards"
    while len(attacked.cards) < 6:
        if 0 < len(all_cards):
            attacked.cards.append(all_cards[0])
            all_cards.pop(0)
        else:
            return "no_cards"
    attacker = players[who_is_next(players.index(attacker), len(players))]
    attacked = players[who_is_next(players.index(attacked), len(players))]
    return "refreshed"


while len(players) != 1:
    print(all_cards)
    attacker_step = attacker.attacker_step(attacked, round_cards)
    if attacker_step == "attacker_end":
        send_all("Бито.;close_input")
        new_round()
        continue
    if len(attacker.cards) == 0:
        send_all(f"Игрок {attacker.nickname} стал одним из победителей!;close_input")
        players.remove(attacker)
        if len(players) != 1:
            new_round()
            continue
        break
    round_cards.append(attacker_step)
    trump_suit_step = False
    if attacker_step[-1] == trump_suit:
        trump_suit_step = True
    cards_to_cover.append(attacker_step)
    attacked_step = attacked.attacked_step(cards_to_cover, trump_suit_step, trump_suit)
    if len(attacked.cards) == 0:
        send_all(f"Игрок {attacked.nickname} стал одним из победителей!;close_input")
        players.remove(attacked)
        if len(players) != 1:
            new_round()
            continue
        break
    if attacked_step[0] == "to_the_next":
        for i in attacked_step[1]:
            if i not in round_cards:
                round_cards.append(i)
        for i in attacked_step[1]:
            if i not in cards_to_cover:
                cards_to_cover.append(i)
        attacker = players[who_is_next(players.index(attacker), len(players))]
        attacked = players[who_is_next(players.index(attacked), len(players))]
        attacked_step = attacked.attacked_step(cards_to_cover, trump_suit_step, trump_suit)
        for i in attacked_step[1]:
            if i not in round_cards:
                round_cards.append(i)
    if attacked_step[0] == "attacked_end":
        attacked.cards += round_cards
        send_all(f"{attacked.nickname} взял карты.;close_input")
        new_round()
        new_round()
    if attacked_step[0] == "normal_step":
        for i in attacked_step[1]:
            if i not in round_cards:
                round_cards.append(i)
        cards_to_cover = []
        continue
