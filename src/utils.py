import os

# Clear console
def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

def match_addresses(address: str, addresses: list[str]) -> bool:
    return address.lower() in [a.lower() for a in addresses]