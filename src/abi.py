import json
from web3 import Web3

# Load UniswapV2 Router ABI
with open('../contracts/abi/UniswapV2Factory.json', 'r') as abi_file:
    contract_abi = json.load(abi_file)

contract_methods = {}

for item in contract_abi:
    if item["type"] == "function":
        # Get the function signature
        param_types = ",".join([param["type"] for param in item["inputs"]])
        function_signature = f"{item['name']}({param_types})"
        # Get the function selector
        selector = Web3.keccak(text=function_signature)[:4].hex()
        print(f"{function_signature} => {'0x' + str(selector)}")
        contract_methods[str(selector)] = function_signature

print(contract_methods)
with open('../contracts/abi/UniswapV2Factory_methods.json', 'w') as f:
    json.dump(contract_methods, f, default=str)
