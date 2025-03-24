from web3 import Web3
from dotenv import load_dotenv
from src.utils import *
from src.logs import *
import requests
import tkinter as tk
from tkinter import simpledialog
from decimal import Decimal, getcontext, InvalidOperation
import time

# Load environment variables from .env file in the root directory
load_dotenv()

# Load configuration from config.json
with open(r"..\config.json") as config_file:
    config = json.load(config_file)

# Extract configuration values
RPC_PROVIDER = config["rpc_provider"]
NETWORK = config["network"]
CHAIN_ID = config["chain_id"]

INFURA_API_KEY = os.getenv("infura_api_key")

# Define RPC providers for different networks
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

# Select RPC URL based on network and provider, default to "mainnet" and "infura" if not found
RPC_URL = (RPC_PROVIDERS.get(NETWORK, "mainnet")).get(RPC_PROVIDER, "infura")
GAS_URL = f'https://gas.api.infura.io/v3/{INFURA_API_KEY}/networks/{CHAIN_ID}/suggestedGasFees'

# Set decimal precision to 28 for accurate calculations
getcontext().prec = 28

# Load ABI files for smart contracts
with open(r'abi\ERC20.json', 'r') as abi_file:
    erc20_abi = json.load(abi_file)
with open(r'abi\UniswapV2Factory.json', 'r') as abi_file:
    factory_abi = json.load(abi_file)
with open(r'abi\UniswapV2Router02.json', 'r') as abi_file:
    router_abi = json.load(abi_file)
with open(r'abi\UniswapV2Pair.json', 'r') as abi_file:
    pair_abi = json.load(abi_file)

# Load contract addresses from environment variables
TOKEN_ADDRESS = os.getenv("YE")
WETH_ADDRESS = os.getenv("WETH_SEP")
UNISWAP_ROUTER = os.getenv("UNISWAP_V2_TEST_ROUTER_ADDRESS")
UNISWAP_FACTORY = os.getenv("UNISWAP_V2_TEST_FACTORY_ADDRESS")

# Create a hidden Tkinter window for secure password input
root = tk.Tk()
root.withdraw()

# Prompt user for password with masked input
password = simpledialog.askstring("PASSWORD", "Input your password：", show='*')

# Load private key from keystore file using the password
private_key = load_keystore(r'..\keystore.json', password).hex()
account = w3.eth.account.from_key(private_key)
print(f"Your wallet: {account.address}")

# Connect to Ethereum network via the selected RPC URL
w3 = Web3(Web3.HTTPProvider(RPC_URL))

# Verify connection to RPC server
if w3.is_connected():
    print("Connected to RPC server")
else:
    print("Failed to connect to Ethereum")
    exit(1)

# Initialize contract instances with their addresses and ABIs
token_contract = w3.eth.contract(address=TOKEN_ADDRESS, abi=erc20_abi)
factory_contract = w3.eth.contract(address=UNISWAP_FACTORY, abi=factory_abi)
router_contract = w3.eth.contract(address=UNISWAP_ROUTER, abi=router_abi)
decimals = token_contract.functions.decimals().call()  # Fetch token decimals


# Helper function to get user input as Decimal
def amount_input(prompt=''):
    quantity = input(prompt)
    try:
        quantity = Decimal(quantity)
    except InvalidOperation:
        print("Invalid amount")
        exit(1)
    return quantity


# Fetch suggested gas prices from Infura API
def get_gas_price(priority='medium'):
    response = requests.get(GAS_URL)
    data = response.json()
    log_info(f"Current gas price: {data[priority]['suggestedMaxFeePerGas']} gwei")
    max_fee = w3.to_wei(data[priority]['suggestedMaxFeePerGas'], 'gwei')
    priority_fee = w3.to_wei(data[priority]['suggestedMaxPriorityFeePerGas'], 'gwei')
    wait_time = data[priority]['maxWaitTimeEstimate']
    return [wait_time, max_fee, priority_fee]


# Sign and send a transaction, return receipt if successful
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


# Transfer ETH to a specified address
def transfer(amount, to_address):
    amount_to_transfer = w3.to_wei(amount, 'ether')
    balance = w3.eth.get_balance(account.address)
    gas_fee = get_gas_price()
    print(f"ETH Balance: {balance}")
    if balance < amount_to_transfer + 21000 * gas_fee[1]:
        print(f"Insufficient balance: {balance} wei, needed: {amount_to_transfer} wei")
        return
    else:
        print("Transferring ETH...")
    tx = {
        'from': account.address,
        'nonce': w3.eth.get_transaction_count(account.address),
        'to': to_address,
        'value': amount_to_transfer,
        'gas': 21000,  # Standard gas limit for ETH transfer
        'maxFeePerGas': gas_fee[1],
        'maxPriorityFeePerGas': gas_fee[2],
        'chainId': CHAIN_ID,
    }
    tx_receipt = sign(tx)
    print(f"Transaction has been confirmed. {tx_receipt}") if tx_receipt is not None else print("Check the error.")


# Transfer ERC20 tokens to a specified address
def transfer_erc20(amount, to_address, contract=token_contract):
    amount_to_transfer = int(amount * (10 ** decimals))
    balance_token = contract.functions.balanceOf(account.address).call()
    balance = w3.eth.get_balance(account.address)
    gas_fee = get_gas_price()
    print(f"Token Balance: {balance_token}")
    if balance_token < amount_to_transfer or 50000 * gas_fee[1] > balance:
        print(
            f"Insufficient balance: {balance_token} token, needed: {amount_to_transfer} token; {balance} wei, needed: {50000 * gas_fee[1]} wei")
        return
    else:
        print("Transferring tokens...")
    gas_estimate = 50000  # Manual gas estimate due to issues with estimate_gas() on testnet
    tx = contract.functions.transfer(to_address, amount_to_transfer).build_transaction({
        'from': account.address,
        'chainId': CHAIN_ID,
        'gas': gas_estimate,
        'maxFeePerGas': gas_fee[1],
        'maxPriorityFeePerGas': gas_fee[2],
        'nonce': w3.eth.get_transaction_count(account.address),
    })
    tx_receipt = sign(tx)
    print(f"Transaction has been confirmed. {tx_receipt}") if tx_receipt is not None else print("Check the error.")


# Check the price of token1 in terms of token2 using Uniswap V2 pair reserves
def check_price(address1, address2, contract=factory_contract):
    pair_address = contract.functions.getPair(address1, address2).call()
    if pair_address == "0x0000000000000000000000000000000000000000":
        return None
    else:
        print(f"Pool already exists at: {pair_address}")
    pair_contract = w3.eth.contract(address=pair_address, abi=pair_abi)
    pair_reserves = pair_contract.functions.getReserves().call()
    reserve0, reserve1 = Decimal(pair_reserves[0]), Decimal(pair_reserves[1])
    print(f"The current price of token1 is: {reserve1 / reserve0} token2")
    return [reserve0, reserve1]


# Approve an address to spend a specified amount of ERC20 tokens
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
    gas_estimate = 100000  # Manual gas estimate
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


# Add liquidity to an Uniswap V2 pool
def add_liquidity(amount_eth, amount_token, slippage=0.01):
    amount_token_desired = int(amount_token * (10 ** decimals))
    amount_token_min = int(amount_token_desired * (1 - slippage))
    amount_eth_wei = w3.to_wei(amount_eth, 'ether')
    amount_eth_min = int(amount_eth_wei * (1 - slippage))
    gas_estimate = 1000000  # Manual gas estimate
    gas_fee = get_gas_price()
    deadline = int(time.time() + gas_fee[0] / 500)  # Set deadline based on estimated wait time
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
        'value': amount_eth_wei,
        'nonce': w3.eth.get_transaction_count(account.address),
    })
    tx_receipt = sign(tx)
    print(f"Liquidity added. {tx_receipt}") if tx_receipt is not None else print("Check the error.")


# Swap ETH for an exact amount of tokens with slippage tolerance
def swap_eth_for_exact_tokens(amount_token, amount_eth, slippage=0.01):
    amount_token_out = int(amount_token * (10 ** decimals))
    amount_eth_max = w3.to_wei(amount_eth, 'ether')
    amount_eth_max_with_slippage = int(amount_eth_max * (1 + slippage))
    gas_fee = get_gas_price()
    gas_estimate = 200000
    total_eth_needed = amount_eth_max_with_slippage + gas_estimate * gas_fee[1]
    eth_balance = w3.eth.get_balance(account.address)
    if eth_balance < total_eth_needed:
        print(f"Insufficient ETH balance: {eth_balance} wei, needed: {total_eth_needed} wei")
        return
    path = [WETH_ADDRESS, TOKEN_ADDRESS]
    deadline = int(time.time() + gas_fee[0] / 500)
    tx = router_contract.functions.swapETHForExactTokens(
        amount_token_out,
        path,
        account.address,
        deadline
    ).build_transaction({
        'from': account.address,
        'value': amount_eth_max_with_slippage,
        'gas': gas_estimate,
        'maxFeePerGas': gas_fee[1],
        'maxPriorityFeePerGas': gas_fee[2],
        'nonce': w3.eth.get_transaction_count(account.address),
        'chainId': CHAIN_ID
    })
    tx_receipt = sign(tx)
    print(f"Transaction has been confirmed. {tx_receipt}") if tx_receipt is not None else print("Check the error.")


# Swap an exact amount of tokens for ETH with slippage tolerance
def swap_exact_tokens_for_eth(amount_token, amount_eth, slippage=0.01):
    amount_token_in = int(amount_token * (10 ** decimals))
    amount_eth_min = w3.to_wei(amount_eth, 'ether')
    amount_eth_min_with_slippage = int(amount_eth_min * (1 - slippage))
    gas_fee = get_gas_price()
    gas_estimate = 200000
    total_eth_needed = gas_estimate * gas_fee[1]
    token_balance = token_contract.functions.balanceOf(account.address).call()
    eth_balance = w3.eth.get_balance(account.address)
    if token_balance < amount_token_in:
        print(f"Insufficient token balance: {token_balance}, needed: {amount_token_in}")
        return
    if eth_balance < total_eth_needed:
        print(f"Insufficient ETH balance for gas: {eth_balance} wei, needed: {total_eth_needed} wei")
        return
    approve_erc20(amount_token)
    path = [TOKEN_ADDRESS, WETH_ADDRESS]
    deadline = int(time.time() + gas_fee[0] / 500)
    tx = router_contract.functions.swapExactTokensForETH(
        amount_token_in,
        amount_eth_min_with_slippage,
        path,
        account.address,
        deadline
    ).build_transaction({
        'from': account.address,
        'gas': gas_estimate,
        'maxFeePerGas': gas_fee[1],
        'maxPriorityFeePerGas': gas_fee[2],
        'nonce': w3.eth.get_transaction_count(account.address),
        'chainId': CHAIN_ID
    })
    tx_receipt = sign(tx)
    print(f"Transaction has been confirmed. {tx_receipt}") if tx_receipt is not None else print("Check the error.")


# Main function to handle user interactions
def main():
    print("What do you want to do? (in uniswap v2)")
    print("1. transfer ETH")
    print("2. transfer ERC20 tokens")
    print("3. Add liquidity")
    print("4. Swap ETH for exact tokens")
    print("5. Swap exact tokens for ETH")
    eth_balance = w3.eth.get_balance(account.address)
    print(f"ETH balance: {Decimal(eth_balance) / Decimal(10 ** 18)}")
    choice = input("Enter your choice: ")
    if choice == '1':
        amount_eth = amount_input("Enter the amount of ETH to transfer: ")
        to_address = input("Enter the recipient's address: ")
        if not w3.is_checksum_address(to_address):
            print("Invalid address")
            exit(1)
        transfer(amount_eth, to_address)
    elif choice == '2':
        amount_token = amount_input("Enter the amount of tokens to transfer: ")
        to_address = input("Enter the recipient's address: ")
        if not w3.is_checksum_address(to_address):
            print("Invalid address")
            exit(1)
        transfer_erc20(amount_token, to_address)
    elif choice == '3':
        amount_eth_desired = amount_input("Enter the amount of ETH to add: ")
        amount_token_desired = amount_input("Enter the amount of tokens to add: ")
        reserves = check_price(TOKEN_ADDRESS, WETH_ADDRESS)
        if reserves is None:
            print("No pool exists, the pair will be created when adding liquidity.")
        elif reserves[0] == 0 or reserves[1] == 0:
            print("One of the reserves is 0.")
        else:
            # Adjust amounts if the desired ratio differs from the current pool ratio
            if reserves[1] / reserves[0] > amount_eth_desired / amount_token_desired:
                print("The current price is different from the desired price.")
                amount_token_desired = amount_eth_desired * reserves[0] / reserves[1]
                print(f"Adjusted token amount: {amount_token_desired}")
            elif reserves[1] / reserves[0] < amount_eth_desired / amount_token_desired:
                print("The current price is different from the desired price.")
                amount_eth_desired = amount_token_desired * reserves[1] / reserves[0]
                print(f"Adjusted ETH amount: {amount_eth_desired}")
        token_balance = token_contract.functions.balanceOf(account.address).call()
        total_eth_needed = w3.to_wei(amount_eth_desired, 'ether') + (1100000 * get_gas_price()[1])
        if eth_balance < total_eth_needed:
            print(f"Insufficient ETH balance: {eth_balance} wei, needed: {total_eth_needed} wei")
            exit(1)
        elif token_balance < amount_token_desired * (10 ** decimals):
            print(f"Insufficient token balance: {token_balance}, needed: {amount_token_desired}")
            exit(1)
        approve_erc20(amount_token_desired)
        add_liquidity(amount_eth_desired, amount_token_desired)
    elif choice == '4':
        amount_token = amount_input("Enter the amount of tokens to swap: ")
        reserves = check_price(TOKEN_ADDRESS, WETH_ADDRESS)
        if reserves is None:
            print("No pool exists, please add liquidity first.")
            exit(1)
        elif reserves[0] == 0 or reserves[1] == 0:
            print("One of the reserves is 0. Cannot swap.")
            exit(1)
        else:
            amount_eth = amount_token * reserves[1] / reserves[0]
            print(f"Needed ETH amount: {amount_eth}")
        swap_eth_for_exact_tokens(amount_token, amount_eth)
    elif choice == '5':
        amount_token = amount_input("Enter the amount of tokens to swap: ")
        reserves = check_price(TOKEN_ADDRESS, WETH_ADDRESS)
        if reserves is None:
            print("No pool exists, please add liquidity first.")
            exit(1)
        elif reserves[0] == 0 or reserves[1] == 0:
            print("One of the reserves is 0. Cannot swap.")
            exit(1)
        else:
            amount_eth = amount_token * reserves[1] / reserves[0]
            print(f"ETH amount to obtain: {amount_eth}")
        swap_exact_tokens_for_eth(amount_token, amount_eth)


if __name__ == "__main__":
    main()
