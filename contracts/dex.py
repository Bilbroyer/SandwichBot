from web3 import Web3
from dotenv import load_dotenv
from src.utils import *
from src.logs import *
import requests
import tkinter as tk
from tkinter import simpledialog
from decimal import Decimal, getcontext, InvalidOperation
import time

load_dotenv()  # Automatically loads from the root .env file

with open(r"..\config.json") as config_file:
    config = json.load(config_file)

RPC_PROVIDER = config["rpc_provider"]
NETWORK = config["network"]
CHAIN_ID = config["chain_id"]

INFURA_API_KEY = os.getenv("infura_api_key")

# RPC url
RPC_PROVIDERS = {
    "mainnet": {
        "infura": f'https://mainnet.infura.io/v3/{INFURA_API_KEY}',
        "quicknode": os.getenv("quicknode_mainnet_url"),
        "google": os.getenv("google_mainnet_url")
    },
    "sepolia": {
        "infura": f'https://sepolia.infura.io/v3/{INFURA_API_KEY}',
        "quicknode": os.getenv("quicknode_sepolia_url"),
        "google": os.getenv("google_sepolia_url")
    }
}
RPC_URL = (RPC_PROVIDERS.get(NETWORK, "mainnet")).get(RPC_PROVIDER, "infura")  # Your RPC URL
GAS_URL = f'https://gas.api.infura.io/v3/{INFURA_API_KEY}/networks//{CHAIN_ID}/suggestedGasFees'

# precision adjustment
"""
Format statement: 
All numbers in the transaction are int, Decimal in the user input, and float is prohibited in transaction amount.
If division is involved, all numbers involved in the operation should be changed beforehand to Decimal.
"""
getcontext().prec = 28

# abi
with open(r'abi\ERC20.json', 'r') as abi_file:
    erc20_abi = json.load(abi_file)
with open(r'abi\UniswapV2Factory.json', 'r') as abi_file:
    factory_abi = json.load(abi_file)
with open(r'abi\UniswapV2Router02.json', 'r') as abi_file:
    router_abi = json.load(abi_file)
with open(r'abi\UniswapV2Pair.json', 'r') as abi_file:
    pair_abi = json.load(abi_file)

# address
TOKEN_ADDRESS = os.getenv("YE")
WETH_ADDRESS = os.getenv("WETH")
UNISWAP_ROUTER = os.getenv("UNISWAP_V2_TEST_ROUTER_ADDRESS")
UNISWAP_FACTORY = os.getenv("UNISWAP_V2_TEST_FACTORY_ADDRESS")


root = tk.Tk()
root.withdraw()

password = simpledialog.askstring("PASSWORD", "Input your password：", show='*')

# account
private_key = load_keystore(r'..\keystore.json', password).hex()
account = w3.eth.account.from_key(private_key)
print(f"Your wallet: {account.address}")

# connect to the RPC server
w3 = Web3(Web3.HTTPProvider(RPC_URL))

if w3.is_connected():
    print("Connected to RPC server")
else:
    print("Failed to connect to Ethereum")
    exit(1)

# contracts
token_contract = w3.eth.contract(address=TOKEN_ADDRESS, abi=erc20_abi)
factory_contract = w3.eth.contract(address=UNISWAP_FACTORY, abi=factory_abi)
router_contract = w3.eth.contract(address=UNISWAP_ROUTER, abi=router_abi)
decimals = token_contract.functions.decimals().call()


def amount_input(clue):
    quantity = input(clue)
    try:
        quantity = Decimal(quantity)
    except InvalidOperation:
        print("Invalid amount")
        exit(1)
    return quantity


def get_gas_price(priority='medium'):
    response = requests.get(GAS_URL)
    data = response.json()
    log_info(f"Current gas price: {data[priority]['suggestedMaxFeePerGas']} gwei")
    max_fee = w3.to_wei(data[priority]['suggestedMaxFeePerGas'], 'gwei')
    priority_fee = w3.to_wei(data[priority]['suggestedMaxPriorityFeePerGas'], 'gwei')
    wait_time = data[priority]['maxWaitTimeEstimate']
    return [wait_time, max_fee, priority_fee]


def sign(tx):
    eth_cost_most = Decimal(tx.get('maxFeePerGas', 0) * tx.get('gas', 0) + tx.get('value', 0))
    log_fatal(f"Estimated max cost: {eth_cost_most / Decimal(10 ** 18)} eth. Are you sure to continue?[y/n]")
    if input() != 'y':
        print("Transaction cancelled.")
        return None
    signed_tx = w3.eth.account.sign_transaction(tx, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    print(f"Transaction sent: {tx_hash.hex()}")
    print(f"Waiting for the transaction to be deployed...")
    try:
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    except Exception as e:
        print(f"Transaction failed: {e}")
        return None
    return tx_receipt


def transfer(amount, to_address):
    amount_to_transfer = w3.to_wei(amount, 'ether')
    balance = w3.eth.get_balance(account.address)
    gas_fee = get_gas_price()
    print(f"ETH Balance: {balance}")
    if balance < amount_to_transfer + 21000 * gas_fee[1]:  # check if you have enough balance, including the gas fee
        print(f"Insufficient balance: {balance} wei, needed: {amount_to_transfer} wei")
        return
    else:
        print("Transferring ETH...")
    tx = {
        'from': account.address,
        'nonce': w3.eth.get_transaction_count(account.address),
        'to': to_address,
        'value': amount_to_transfer,
        'gas': 21000,
        'maxFeePerGas': gas_fee[1],
        'maxPriorityFeePerGas': gas_fee[2],
        'chainId': CHAIN_ID,
    }
    tx_receipt = sign(tx)
    print(f"Transaction has been confirmed. {tx_receipt}") if tx_receipt is not None else print("Check the error.")


def transfer_erc20(amount, to_address, contract=token_contract):
    amount_to_transfer = int(amount * (10 ** decimals))
    balance_token = contract.functions.balanceOf(account.address).call()
    balance = w3.eth.get_balance(account.address)
    gas_fee = get_gas_price()
    print(f"Token Balance: {balance_token}")
    if balance_token < amount_to_transfer or 50000 * gas_fee[
        1] < balance:  # check if you have enough balance, including the gas fee
        print(
            f"Insufficient balance: {balance_token} token, needed: {amount_to_transfer} token; {balance} wei, needed: {50000 * gas_fee[1]} wei")
        return
    else:
        print("Transferring tokens...")
    # gas_estimate = token_contract.functions.transfer(to_address, amount_to_transfer).estimate_gas()
    gas_estimate = 50000  # I don't know why the estimate_gas() method is not working in test net
    tx = token_contract.functions.transfer(to_address, amount_to_transfer).build_transaction({
        'from': account.address,
        'chainId': CHAIN_ID,
        'gas': gas_estimate,
        'maxFeePerGas': gas_fee[1],
        'maxPriorityFeePerGas': gas_fee[2],
        'nonce': w3.eth.get_transaction_count(account.address),
    })
    tx_receipt = sign(tx)
    print(f"Transaction has been confirmed. {tx_receipt}") if tx_receipt is not None else print("Check the error.")


def check_price(address1, address2, contract=factory_contract):
    pair_address = contract.functions.getPair(address1, address2).call()

    if pair_address == "0x0000000000000000000000000000000000000000":
        return None
    else:
        print(f"Pool already exists at: {pair_address}")

    pair_contract = w3.eth.contract(address=pair_address, abi=pair_abi)
    pair_reserves = pair_contract.functions.getReserves().call()
    # reverse is supposed to be an integer. In order to meet the precision requirement, we need to convert it to Decimal
    reverse0, reverse1 = Decimal(pair_reserves[0]), Decimal(pair_reserves[1])
    print(f"The current price of token1 is: {reverse1 / reverse0} token2")
    return [reverse0, reverse1]


def approve_erc20(amount, address=UNISWAP_ROUTER):
    amount_to_approve = int(amount * (10 ** decimals))
    balance = token_contract.functions.balanceOf(account.address).call()
    print(f"Token Balance: {balance}")
    allowance = token_contract.functions.allowance(account.address, address).call()
    print(f"Current allowance: {allowance}")
    if allowance >= amount_to_approve:
        print("Already approved")
        return
    else:
        print("Approving tokens...")
    # gas_estimate = token_contract.functions.approve(address, amount_to_approve).estimate_gas()
    gas_estimate = 100000  # I don't know why the estimate_gas() method is not working in test net
    gas_fee = get_gas_price()
    tx = token_contract.functions.approve(address, amount_to_approve).build_transaction({
        'from': account.address,
        'chainId': CHAIN_ID,
        'gas': gas_estimate,
        'maxFeePerGas': gas_fee[1],
        'maxPriorityFeePerGas': gas_fee[2],
        'nonce': w3.eth.get_transaction_count(account.address),
    })

    tx_receipt = sign(tx)
    print(
        f"Approved {amount_to_approve} tokens to Uniswap V2 Router. {tx_receipt}") if tx_receipt is not None else print(
        "Check the error.")


def add_liquidity(amount_eth, amount_token, slippage=0.01):
    # Amount values should be in the correct units
    amount_token_desired = int(amount_token * (10 ** decimals))  # Example value, replace with your desired amount
    amount_token_min = int(amount_token_desired * (1 - slippage))  # Minimum token amount to accept
    amount_eth = w3.to_wei(amount_eth, 'ether')  # Minimum ETH to accept
    amount_eth_min = int(amount_eth * (1 - slippage))  # Minimum ETH to accept

    # gas_estimate = router_contract.functions.addLiquidityETH(
    #     TOKEN_ADDRESS,
    #     amount_token_desired,
    #     amount_token_min,
    #     amount_eth_min,
    #     account.address,
    #     deadline
    # ).estimate_gas()
    gas_estimate = 1000000
    gas_fee = get_gas_price()
    deadline = int(time.time() + gas_fee[0] / 500)
    tx = router_contract.functions.addLiquidityETH(
        TOKEN_ADDRESS,
        amount_token_desired,
        amount_token_min,
        amount_eth_min,
        account.address,
        deadline
    ).build_transaction({
        'from': account.address,
        'chainId': CHAIN_ID,
        'gas': gas_estimate,
        'maxFeePerGas': gas_fee[1],
        'maxPriorityFeePerGas': gas_fee[2],
        'value': amount_eth,  # ETH value to be added
        'nonce': w3.eth.get_transaction_count(account.address),
    })

    tx_receipt = sign(tx)
    print(f"Liquidity added. {tx_receipt}") if tx_receipt is not None else print("Check the error.")


def swap_eth_for_exact_tokens(amount_token, amount_eth, slippage=0.01):
    pass


def swap_exact_tokens_for_eth(amount_token, amount_eth, slippage=0.01):
    pass


def main():
    print("What do you want to do? (in uniswap v2)")
    print("1. transfer ETH")
    print("2. transfer ERC20 tokens")
    print("3. Add liquidity")
    print("4. Swap ETH for tokens")
    print("5. Swap tokens for ETH")
    choice = input("Enter your choice: ")
    if choice == '1':
        amount_eth = amount_input("Enter the amount of ETH to transfer: ")
        to_address = input("Enter the recipient's address: ")
        if not w3.is_checksum_address(to_address):  # ensure no typos in your address
            print("Invalid address")
            exit(1)
        transfer(amount_eth, to_address)
    elif choice == '2':
        amount_token = amount_input("Enter the amount of tokens to transfer: ")
        to_address = input("Enter the recipient's address: ")
        if not w3.is_checksum_address(to_address):  # ensure no typos in your address
            print("Invalid address")
            exit(1)
        transfer_erc20(amount_token, to_address)
    elif choice == '3':
        amount_eth_desired = amount_input("Enter the amount of ETH to add: ")
        amount_token_desired = amount_input("Enter the amount of tokens to add: ")
        reverses = check_price(TOKEN_ADDRESS, WETH_ADDRESS)
        if reverses is None:
            print("No pool exists, the pair will be created when adding liquidity.")
        elif reverses[0] == 0 or reverses[1] == 0:
            print("One of the reserves is 0.")
        else:
            # Check if the current price is different from the desired price, and adjust the amount accordingly
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
        total_eth_needed = w3.to_wei(amount_eth_desired, 'ether') + (
                1100000 * get_gas_price()[1])  # Adjust based on your values
        if eth_balance < total_eth_needed:
            print(f"Insufficient ETH balance: {eth_balance} wei, needed: {total_eth_needed} wei")
            exit(1)
        elif token_balance < amount_token_desired * (10 ** decimals):
            print(f"Insufficient token balance: {token_balance}, needed: {amount_token_desired}")
            exit(1)
        approve_erc20(amount_token_desired)
        add_liquidity(amount_eth_desired, amount_token_desired)
    elif choice == '4':
        pass


if __name__ == "__main__":
    main()
