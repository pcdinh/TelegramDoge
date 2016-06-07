import requests
import time
from block_io import BlockIo  # see https://block.io/api/python
import logging
logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s')

# Block.io configuration
API_KEY = ""
API_SECRET = ""  # pin
API_VERSION = 2

logger = logging.getLogger("")
token = ""  # Telegram bot token
url = "https://api.telegram.org/bot%s/" % (token)
n = 0
block_io = BlockIo(API_KEY, API_SECRET, API_VERSION)
active_users = {}


def get_count(chat_id):
    n = []
    t = time.time()
    chat_users = active_users[chat_id]
    for i in chat_users:
        if t - chat_users[i] <= 600:
            n.append(i)
    return n

def send_message(message, chat_id):
    requests.get(url + "sendMessage", data={"chat_id":chat_id, "text":message})


def process(message, username, chat_id):
    message = message.split(" ")
    for _ in range(message.count(' ')):
        message.remove(' ')

    # Handle /register command
    if message[0].startswith("/register"):
        try:
            block_io.get_new_address(label=username)
            send_message("@" + username + " you are now registered.", chat_id)
        except:
            send_message("@" + username + " you are already registered.", chat_id)
        return True
    # Handle /balance command
    if message[0].startswith("/balance"):
        try:
            data = block_io.get_address_balance(labels=username)
            balance = data['data']['balances'][0]['available_balance']
            pending_balance = data['data']['balances'][0]['pending_received_balance']
            send_message("@" + username + " Balance : " + balance + "LTC (" + pending_balance + " LTC)", chat_id)
        except:
            send_message("@" + username + " you are not regsitered yet. use /register to register.", chat_id)
        return True
    # Handle /tip
    if message[0].startswith("/tip"):
        try:
            person = message[1].replace('@', '')
            amount = abs(float(message[2]))
            block_io.withdraw_from_labels(amounts=str(amount), from_labels=username, to_labels=person)
            send_message("@" + username + " tipped " + str(amount) + " LTC to @" + person + "", chat_id)
        except ValueError:
            send_message("@" + username + " invalid amount.", chat_id)
        except:
            send_message("@" + username + " insufficient balance or @" + person + " is not registered yet.", chat_id)
        return True
    # Handle /address
    if message[0].startswith("/address"):
        try:
            data = block_io.get_address_by_label(label=username)
            send_message("@" + username + " your address is " + data['data']['address'] + "", chat_id)
        except:
            send_message("@" + username + " you are not registered yet. use /register to register.", chat_id)
        return True
    # Command /withdraw
    if message[0].startswith("/withdraw"):
        try:
            amount = abs(float(message[1]))
            address = message[2]
            data = block_io.withdraw_from_labels(amounts=str(amount), from_labels=username, to_addresses=address)
        except ValueError:
            send_message("@" + username + " invalid amount.", chat_id)
        except:
            send_message("@" + username + " insufficient balance or you are not registered yet.", chat_id)
        return True
    # Command /rain
    if message[0].startswith("/rain"):
        try:
            users = get_count(chat_id)
            if username in users:
                users.remove(username)
            number = len(users)

            amount = ("10," * (number - 1)) + '10'
            name = username
            username = ((username + ',') * (number - 1)) + username
            if number < 2:
                send_message("@" + username + " less than 2 litecoiners are active.", chat_id)
            else:
                print(amount)
                print(username)
                block_io.withdraw_from_labels(amounts=amount, from_labels=username, to_labels=','.join(users))
                send_message("@" + name + " is raining on " + ','.join(users) + "", chat_id)
        except:
            logger.exception("Error when handling /rain")
        return True
    # Command /active
    if "/active" in message:
        send_message("Current active : %d litecoiners" % (len(get_count(chat_id))), chat_id)
    else:
        global active_users
        try:
            active_users[chat_id][username] = time.time()
        except KeyError:
            active_users[chat_id] = {}
            active_users[chat_id][username] = time.time()


if __name__ == "__main__":
    while True:
        try:
            data = requests.get(url + "getUpdates", data={"offset": n}).json()
            n = data["result"][0]["update_id"] + 1
            username = data["result"][0]["message"]["from"]['username']
            chat_id = data["result"][0]["message"]["chat"]["id"]
            message = data["result"][0]["message"]["text"]
            process(message, username, chat_id)
        except:
            logger.exception("Error when listening to chat room activities")
