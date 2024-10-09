import asyncio
import json
import time

from web3 import AsyncWeb3
from src.logs import *
from src.constants import *
from src.utils import *

from web3.providers.persistent import (
    WebSocketProvider
)



async def sandwich_uniswap_v2_router_tx(tx_hash, w3):
    str_log_prefix = f"txhash={tx_hash.hex()}"

    log_trace(str_log_prefix, "received")

    tx = await w3.eth.get_transaction(tx_hash)
    # get the transaction receipt
    try:
        tx = await w3.eth.get_transaction(tx_hash)
    except Exception:
        tx = None
    print(tx)

    try:
        tx_recp = await w3.eth.get_transaction_receipt(tx_hash)
    except Exception:
        tx_recp = None
    print(tx_recp)

    if tx_recp is not None:
        return

    if tx is None:
        return

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
