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
ARB_URL = f'https://{API_KEY}:{API_SECRET}@arbitrum-mainnet.infura.io/v3/{API_KEY}'
SEP_URL = f'https://{API_KEY}:{API_SECRET}@sepolia.infura.io/v3/{API_KEY}'

# abi
erc20_abi = json.loads(
    '[{"constant":false,"inputs":[{"name":"spender","type":"address"},{"name":"amount","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"type":"function"}]')
with open(r'abi\UniswapV2Factory.json', 'r') as abi_file:
    factory_abi = json.load(abi_file)
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
# gas_estimate = 2000000
max_fee = w3.to_wei(data['medium']['suggestedMaxFeePerGas'], 'gwei')
priority_fee = w3.to_wei(data['medium']['suggestedMaxPriorityFeePerGas'], 'gwei')

root = tk.Tk()
root.withdraw()

password1 = simpledialog.askstring("密码输入", "请输入密码：", show='*')

# connect to the RPC server
w3 = Web3(Web3.HTTPProvider(SEP_URL))

if w3.is_connected():
    print("Connected to RPC server")
else:
    print("Failed to connect to Ethereum")

# account
private_key = load_keystore(r'..\keystore1.json', password1).hex()
account = w3.eth.account.from_key(private_key)
print(account.address)

# contracts
token_contract = w3.eth.contract(address=TOKEN_ADDRESS, abi=erc20_abi)
factory_contract = w3.eth.contract(address=UNISWAP_V2_TEST_FACTORY_ADDRESS, abi=factory_abi)
router_contract = w3.eth.contract(address=UNISWAP_V2_TEST_ROUTER_ADDRESS, abi=router_abi)


def create_pair():
    try:
        pair_address = factory_contract.functions.getPair(TOKEN_ADDRESS, WETH_ADDRESS).call()
    except:
        pair_address = '0x0000000000000000000000000000000000000000'

    if pair_address != '0x0000000000000000000000000000000000000000':
        print(f"Pair already exists at: {pair_address}")
        return pair_address

    gas_estimate = factory_contract.functions.createPair(TOKEN_ADDRESS, WETH_ADDRESS).estimate_gas()
    tx = factory_contract.functions.createPair(TOKEN_ADDRESS, WETH_ADDRESS).build_transaction({
        'from': account.address,
        'chainId': chainId,
        'gas': gas_estimate,
        'maxFeePerGas': max_fee,
        'maxPriorityFeePerGas': priority_fee,
        'nonce': w3.eth.get_transaction_count(account.address),
    })

    signed_tx = w3.eth.account.sign_transaction(tx, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    print(f"Transaction sent: {tx_hash.hex()}")
    print(f"Waiting for the transaction to be deployed...")
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"Pair created at: {tx_receipt['logs'][0]['address']}")
    return tx_receipt['logs'][0]['address']


def add_liquidity():
    deadline = int(time.time()) + 600  # 10-minute deadline

    # Amount values should be in the correct units
    amount_token_desired = 1_000_000  # Example value, replace with your desired amount
    amount_token_min = 990_000  # Minimum token amount to accept
    amount_eth_min = w3.to_wei(0.1, 'ether')  # Minimum ETH to accept
    gas_estimate = router_contract.functions.addLiquidityETH(
        TOKEN_ADDRESS,
        amount_token_desired,
        amount_token_min,
        amount_eth_min,
        account.address,
        deadline
    ).estimate_gas()

    tx = router_contract.functions.addLiquidityETH(
        TOKEN_ADDRESS,
        amount_token_desired,
        amount_token_min,
        amount_eth_min,
        account.address,
        deadline
    ).build_transaction({
        'from': account.address,
        'chainId': chainId,
        'gas': gas_estimate,
        'maxFeePerGas': max_fee,
        'maxPriorityFeePerGas': priority_fee,
        'value': amount_eth_min,  # ETH value to be added
        'nonce': w3.eth.get_transaction_count(account.address),
    })

    signed_tx = w3.eth.account.sign_transaction(tx, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    print(f"Transaction sent: {tx_hash.hex()}")
    print(f"Waiting for the transaction to be deployed...")
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"Liquidity added.{tx_receipt}")


if __name__ == "__main__":
    create_pair()
    add_liquidity()
