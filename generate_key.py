from web3.auto import w3
from src.utils import save_keystore

account = w3.eth.account.create()

print(f"Address: {account.address}")
print(f"Private Key: {account._private_key.hex()} !DONT SHARE THIS!")

password = input("Enter a password to encrypt the private key: ")
print("You should keep this password safe, or you won't be able to access your account.")

keystore = w3.eth.account.encrypt(account._private_key.hex(), password)
save_keystore(keystore, 'keystore.json')

print("Your keystore is now ready to use.")
