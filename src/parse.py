import json
from eth_abi import decode

# Load UniswapV2 Router ABI
with open('contracts/abi/UniswapV2Router02.json', 'r') as abi_file:
    uniswap_v2_router_abi = json.load(abi_file)

with open('contracts/abi/UniswapV2Router02_methods.json', 'r') as methods_file:
    uniswap_v2_router_methods = json.load(methods_file)

# Create a dictionary to map method names to the function signatures
def get_function_signature_mapping(abi):
    return {
        f['name']: f['inputs'] for f in abi if f['type'] == 'function'
    }


# Get the mapping of function signatures from the ABI
function_signatures = get_function_signature_mapping(uniswap_v2_router_abi)

# Helper function to decode UniswapV2 Router transaction data
def parse_univ2_router_tx(tx_data: str):
    """Parse a UniswapV2 Router transaction input.

    Parameters
    ----------
    tx_data: str
        Hex string of the transaction input data.
    Returns
    -------
    dict
        Parsed transaction information.
    """

    # remove `0x` prefix if present and extract the first 4 bytes (8 hex chars)
    tx_data = tx_data[2:] if tx_data.startswith("0x") else tx_data
    method_selector = tx_data[:8]

    if method_selector not in uniswap_v2_router_methods:
        return {
            "method": None,
            "availability": False,
        }

    method = uniswap_v2_router_methods[method_selector]

    if not method.startswith("swap"):
        return {
            "method": method,
            "availability": False,
        }

    # Decode parameters of swap methods
    decoded_params = decode(
        ["uint256", "address[]", "address", "uint256"],
        bytes.fromhex(tx_data[8:]),
    )

    amount_out_min, path, to, deadline = decoded_params

    return {
        "availability": True,
        "method": method,
        "amountOutMin": amount_out_min,
        "path": path,
        "to": to,
        "deadline": deadline,
    }

