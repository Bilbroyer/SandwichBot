import json
from web3 import Web3
from eth_abi import decode

# Load UniswapV2 Router ABI
with open('contracts/abi/IUniswapV2Router02.json', 'r') as abi_file:
    uniswap_v2_router_abi = json.load(abi_file)


# Create a dictionary to map method names to the function signatures
def get_function_signature_mapping(abi):
    return {
        f['name']: f['inputs'] for f in abi if f['type'] == 'function'
    }


# Get the mapping of function signatures from the ABI
function_signatures = get_function_signature_mapping(uniswap_v2_router_abi)


# Helper function to decode UniswapV2 Router transaction data
def parse_univ2_router_tx(tx_data):
    # Remove '0x' from tx data and get the first 4 bytes (the method selector)
    method_selector = tx_data[:10]

    # Check if the method is 'swapExactETHForTokens'
    method_name = None
    for name, inputs in function_signatures.items():
        # 'swapExactETHForTokens' has the selector '0x7ff36ab5'
        if name == 'swapExactETHForTokens' and method_selector == '0x7ff36ab5':
            method_name = name
            break

    if method_name is None:
        return None  # Return None if it's not the 'swapExactETHForTokens' method

    # Decode parameters
    decoded_params = decode(
        ['uint256', 'address[]', 'address', 'uint256'],  # The parameters for 'swapExactETHForTokens'
        bytes.fromhex(tx_data[10:])  # Strip the first 4 bytes (method selector)
    )

    amount_out_min, path, to, deadline = decoded_params

    return {
        'amountOutMin': amount_out_min,
        'path': path,
        'to': to,
        'deadline': deadline
    }