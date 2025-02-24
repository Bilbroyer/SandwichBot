from web3 import Web3
from src.utils import *
from src.cache import read_cache
from src.constants import *
import requests
import tkinter as tk
from tkinter import simpledialog
import time
import json

# infura api from the src/config.ini file, you can replace it with your own API key and secret
API_KEY = read_cache('infura', 'API_KEY', r'..\src\config')
API_SECRET = read_cache('infura', 'API_SECRET', r'..\src\config')

# RPC url
ETH_URL = f"https://{API_KEY}:{API_SECRET}@mainnet.infura.io/v3/{API_KEY}"
SEP_URL = f'https://{API_KEY}:{API_SECRET}@sepolia.infura.io/v3/{API_KEY}'

# abi
with open(r'abi\ERC20.json', 'r') as abi_file:
    erc20_abi = json.load(abi_file)
with open(r'abi\UniswapV2Factory.json', 'r') as abi_file:
    factory_abi = json.load(abi_file)
with open(r'abi\UniswapV2Router02.json', 'r') as abi_file:
    router_abi = json.load(abi_file)
with open(r'abi\UniswapV2Pair.json', 'r') as abi_file:
    pair_abi = json.load(abi_file)

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

# account
private_key = load_keystore(r'..\keystore.json', password).hex()
account = w3.eth.account.from_key(private_key)
print(f"Your wallet: {account.address}")

# connect to the RPC server
w3 = Web3(Web3.HTTPProvider(SEP_URL))

if w3.is_connected():
    print("Connected to RPC server")
else:
    print("Failed to connect to Ethereum")
    exit(1)

# contracts
token_contract = w3.eth.contract(address=TOKEN_ADDRESS, abi=erc20_abi)
factory_contract = w3.eth.contract(address=UNISWAP_V2_TEST_FACTORY_ADDRESS, abi=factory_abi)
router_contract = w3.eth.contract(address=UNISWAP_V2_TEST_ROUTER_ADDRESS, abi=router_abi)
decimals = token_contract.functions.decimals().call()


def check_price(address1, address2, factory_contract=factory_contract):
    pair_address = factory_contract.functions.getPair(address1, address2).call()

    if pair_address == "0x0000000000000000000000000000000000000000":
        return None
    else:
        print(f"Pool already exists at: {pair_address}")

    pair_contract = w3.eth.contract(address=pair_address, abi=pair_abi)
    pair_reserves = pair_contract.functions.getReserves().call()
    reverse0, reverse1 = pair_reserves[0], pair_reserves[1]
    print(f"The current price of token1 is: {reverse1 / reverse0} token2")
    return pair_reserves


def approve_erc20(amount):
    amount_to_approve = int(amount * (10 ** decimals))
    balance = token_contract.functions.balanceOf(account.address).call()
    print(f"Token Balance: {balance}")
    allowance = token_contract.functions.allowance(account.address, UNISWAP_V2_TEST_ROUTER_ADDRESS).call()
    print(f"Current allowance: {allowance}")
    if allowance >= amount_to_approve:
        print("Already approved")
        return
    else:
        print("Approving tokens...")
    # gas_estimate = token_contract.functions.approve(UNISWAP_V2_TEST_ROUTER_ADDRESS, amount_to_approve).estimate_gas()
    gas_estimate = 100000  # I don't know why the estimate_gas() method is not working in test net
    tx = token_contract.functions.approve(UNISWAP_V2_TEST_ROUTER_ADDRESS, amount_to_approve).build_transaction({
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
    print(f"Approved {amount_to_approve} tokens to Uniswap V2 Router.{tx_receipt}")


def add_liquidity(amount_eth, amount_token, slippage=0.01):
    # Amount values should be in the correct units
    amount_token_desired = int(amount_token * (10 ** decimals))  # Example value, replace with your desired amount
    amount_token_min = int(amount_token_desired * (1 - slippage))  # Minimum token amount to accept
    amount_eth = w3.to_wei(amount_eth, 'ether')  # Minimum ETH to accept
    amount_eth_min = int(amount_eth * (1 - slippage))  # Minimum ETH to accept

    deadline = int(time.time()) + 600  # 10-minute deadline

    # gas_estimate = router_contract.functions.addLiquidityETH(
    #     TOKEN_ADDRESS,
    #     amount_token_desired,
    #     amount_token_min,
    #     amount_eth_min,
    #     account.address,
    #     deadline
    # ).estimate_gas()
    gas_estimate = 1000000

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
        'value': amount_eth,  # ETH value to be added
        'nonce': w3.eth.get_transaction_count(account.address),
    })

    signed_tx = w3.eth.account.sign_transaction(tx, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    print(f"Transaction sent: {tx_hash.hex()}")
    print(f"Waiting for the transaction to be deployed...")
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"Liquidity added.{tx_receipt}")


def swap_eth_for_exact_tokens(amount_token, amount_eth, slippage=0.01):
    pass


def swap_exact_tokens_for_eth(amount_token, amount_eth, slippage=0.01):
    pass


def main():
    print("What do you want to do? (in uniswap v2)")
    print("1. Add liquidity")
    print("2. Swap ETH for tokens")
    print("3. Swap tokens for ETH")
    choice = input("Enter your choice: ")
    if choice == '1':
        amount_eth_desired = 0.1  # Example value, replace with your desired amount
        amount_token_desired = 1_000_000  # Example value, replace with your desired amount
        reverses = check_price(TOKEN_ADDRESS, WETH_ADDRESS)
        if reverses is None:
            print("No pool exists, the pair will be created when adding liquidity.")
        elif reverses[0] == 0 or reverses[1] == 0:
            print("One of the reserves is 0.")
        else:
            if reverses[1] / reverses[0] > amount_eth_desired / amount_token_desired:
                print("The current price is different from the desired price.")
                amount_token_desired = amount_eth_desired * reverses[0] / reverses[1]
                print(f"Adjusted token amount: {amount_token_desired}")
            elif reverses[1] / reverses[0] < amount_eth_desired / amount_token_desired:
                print("The current price is different from the desired price.")
                amount_eth_desired = amount_token_desired * reverses[1] / reverses[0]
                print(f"Adjusted ETH amount: {amount_eth_desired}")

        eth_balance = w3.eth.get_balance(account.address)
        token_balance = token_contract.functions.balanceOf(account.address).call()
        total_eth_needed = w3.to_wei(amount_eth_desired, 'ether') + (1100000 * max_fee)  # Adjust based on your values
        if eth_balance < total_eth_needed:
            print(f"Insufficient ETH balance: {eth_balance} wei, needed: {total_eth_needed} wei")
            exit(1)
        elif token_balance < amount_token_desired * (10 ** decimals):
            print(f"Insufficient token balance: {token_balance}, needed: {amount_token_desired}")
            exit(1)
        approve_erc20(amount_token_desired)
        add_liquidity(amount_eth_desired, amount_token_desired)
    elif choice == '2':
        pass

if __name__ == "__main__":
    main()
