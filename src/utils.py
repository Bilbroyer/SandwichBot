import os, json, random
from web3.auto import w3

# Clear console
def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

def generate_keystore(content, password):
    keystore = w3.eth.account.encrypt(content, password)
    return keystore


def save_keystore(keystore, filename):
    with open(filename, 'w') as f:
        json.dump(keystore, f)


def load_keystore(filename, password):
    with open(filename, 'r') as f:
        keystore = json.load(f)
    try:
        return w3.eth.account.decrypt(keystore, password)
    except ValueError:
        return random.getrandbits(256).to_bytes(32, 'big')


def match_addresses(address: str, addresses: list[str]) -> bool:
    return address.lower() in [a.lower() for a in addresses]