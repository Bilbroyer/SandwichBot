from web3 import Web3
from src.utils import *
from src.cache import read_cache
from src.constants import *
import requests
import tkinter as tk
from tkinter import simpledialog
import time
import json

# infura api
API_KEY = read_cache('infura', 'API_KEY', r'..\src\config')
API_SECRET = read_cache('infura', 'API_SECRET', r'..\src\config')

# RPC url
ETH_URL = f"https://{API_KEY}:{API_SECRET}@mainnet.infura.io/v3/{API_KEY}"
SEP_URL = f'https://{API_KEY}:{API_SECRET}@sepolia.infura.io/v3/{API_KEY}'

# abi
with open(r'abi\ERC20.json', 'r') as abi_file:
    erc20_abi = json.load(abi_file)
with open(r'abi\UniswapV2Router02.json', 'r') as abi_file:
    router_abi = json.load(abi_file)

# token
TOKEN_ADDRESS = TOKENS_TEST['YE']
WETH_ADDRESS = TOKENS_TEST['WETH']

# gas price
chainId = 11155111
GAS_URL = f'https://{API_KEY}:{API_SECRET}@gas.api.infura.io/v3/{API_KEY}/networks//{chainId}/suggestedGasFees'
response = requests.get(GAS_URL)
data = response.json()
max_fee = w3.to_wei(data['medium']['suggestedMaxFeePerGas'], 'gwei')
priority_fee = w3.to_wei(data['medium']['suggestedMaxPriorityFeePerGas'], 'gwei')

root = tk.Tk()
root.withdraw()

password = simpledialog.askstring("PASSWORD", "Input your password：", show='*')

# connect to the RPC server
w3 = Web3(Web3.HTTPProvider(SEP_URL))

if w3.is_connected():
    print("Connected to RPC server")
else:
    print("Failed to connect to Ethereum")
    exit(1)

# account
private_key = load_keystore(r'..\keystore.json', password).hex()
account = w3.eth.account.from_key(private_key)
print(account.address)

# contracts
token_contract = w3.eth.contract(address=TOKEN_ADDRESS, abi=erc20_abi)
router_contract = w3.eth.contract(address=UNISWAP_V2_TEST_ROUTER_ADDRESS, abi=router_abi)
decimals = token_contract.functions.decimals().call()
