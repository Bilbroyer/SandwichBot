import asyncio
# import json
# import time

from web3 import AsyncWeb3
from src.cache import read_cache
from src.logs import *
from src.utils import *
from src.parse import *
from src.constants import *

from web3.providers.persistent import (
    WebSocketProvider
)

transaction_count = 0
# WebSocket URL, you might change it to your own RPC server. You should create the config.ini file in the src/config folder, or you can replace the WSS_URL with your own RPC server URL.
WSS_URL = read_cache('quicknode', 'sepolia_wss', r'src\config')

async def sandwich_uniswap_v2_router_tx(tx_hash: hex, w3):
    global transaction_count
    str_log_prefix = f"txhash={tx_hash.hex()}"
    # log_trace(str_log_prefix, "received")
    transaction_count += 1
    if transaction_count % 200 == 0:
        clear_console()
        transaction_count = 0
    # get the transaction receipt
    try:
        tx = await w3.eth.get_transaction(tx_hash)
    except Exception:
        tx = None

    try:
        tx_recp = await w3.eth.get_transaction_receipt(tx_hash)
    except Exception:
        tx_recp = None

    if tx_recp is not None:
        return

    if tx is None:
        return

    if not tx['to'].lower() == UNISWAP_V2_ROUTER_ADDRESS.lower():
        return

    log_info(str_log_prefix, "UniswapV2 Router transaction detected")

    tx_data = tx['input']

    if len(tx_data) < 10:
        return

    route_data = parse_univ2_router_tx(tx_data)
    log_info(str_log_prefix, f"method={route_data['method']}")

    """
    To be continued...
    """


async def main():
    # connect to RPC by WebSocket
    w3 = AsyncWeb3(WebSocketProvider(WSS_URL))
    await w3.provider.connect()
    if await w3.is_connected():
        log_info(f"Connected to RPC by WebSocket")
    else:
        log_fatal(f"Failed to connect to {WSS_URL}")
        exit(1)
    log_info(
        "============================================================================"
    )
    log_info(
        r"""
     _______.     ___      .__   __.  _______  ____    __    ____  __    ______  __    __  
    /       |    /   \     |  \ |  | |       \ \   \  /  \  /   / |  |  /      ||  |  |  | 
   |   (----`   /  ^  \    |   \|  | |  .--.  | \   \/    \/   /  |  | |  ,----'|  |__|  | 
    \   \      /  /_\  \   |  . `  | |  |  |  |  \            /   |  | |  |     |   __   | 
.----)   |    /  _____  \  |  |\   | |  '--'  |   \    /\    /    |  | |  `----.|  |  |  | 
|_______/    /__/     \__\ |__| \__| |_______/     \__/  \__/     |__|  \______||__|  |__|                                                                                             
        """
    )
    log_info(
        "============================================================================\n"
    )

    log_info("Listening to mempool...\n")

    # monitor pending transactions
    async def log_loop():
        event_filter = await w3.eth.filter("pending")
        while True:
            tx_hashes = await event_filter.get_new_entries()
            for tx_hash in tx_hashes:
                try:
                    await sandwich_uniswap_v2_router_tx(tx_hash, w3)
                except Exception as e:
                    log_fatal(f"txhash={tx_hash} error {str(e)}")

    await log_loop()


if __name__ == "__main__":
    asyncio.run(main())
