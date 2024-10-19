import sys
import time
import json
import hashlib
import threading
import uuid
import random

import web3
import hexbytes
import eth_abi
import requests

# import setting

PAYMENT_ABI = '''[
    {
      "inputs": [
        {
          "internalType": "address",
          "name": "_token_address",
          "type": "address"
        }
      ],
      "stateMutability": "nonpayable",
      "type": "constructor"
    },
    {
      "anonymous": false,
      "inputs": [
        {
          "indexed": true,
          "internalType": "uint256",
          "name": "topup_id",
          "type": "uint256"
        },
        {
          "indexed": true,
          "internalType": "address",
          "name": "spender",
          "type": "address"
        },
        {
          "indexed": false,
          "internalType": "uint256",
          "name": "amount",
          "type": "uint256"
        }
      ],
      "name": "TopupCreated",
      "type": "event"
    },
    {
      "anonymous": false,
      "inputs": [
        {
          "indexed": true,
          "internalType": "uint256",
          "name": "topup_id",
          "type": "uint256"
        },
        {
          "indexed": true,
          "internalType": "address",
          "name": "spender",
          "type": "address"
        },
        {
          "indexed": false,
          "internalType": "uint256",
          "name": "remaining_balance",
          "type": "uint256"
        }
      ],
      "name": "TopupSpent",
      "type": "event"
    },
    {
      "inputs": [],
      "name": "next_topup_id",
      "outputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "uint256",
          "name": "_from_topup_id",
          "type": "uint256"
        },
        {
          "internalType": "address",
          "name": "_to_address",
          "type": "address"
        },
        {
          "internalType": "uint256",
          "name": "_amount",
          "type": "uint256"
        },
        {
          "internalType": "bytes",
          "name": "_signature",
          "type": "bytes"
        }
      ],
      "name": "pay_to",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "token",
      "outputs": [
        {
          "internalType": "contract IERC20",
          "name": "",
          "type": "address"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "uint256",
          "name": "_amount",
          "type": "uint256"
        },
        {
          "internalType": "address",
          "name": "_spender",
          "type": "address"
        }
      ],
      "name": "topup",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "name": "topups",
      "outputs": [
        {
          "internalType": "address",
          "name": "spender",
          "type": "address"
        },
        {
          "internalType": "uint256",
          "name": "balance",
          "type": "uint256"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "total",
      "outputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    }
]
'''

TOPUP_CREATED_EVENT = '0x8a883af501b0e5b7e5c72df878f0651b9c07b663453ecd9b6da8a52980a0519e'
TOPUP_SPENT_EVENT = '0x23cec44a79afa2fa52a38fffc67d3f5eb7f1c8743ccd23bf17806984b1223ad9'
RPC_URL = 'http://127.0.0.1:8545'
PAYMENT_CONTRACT = '0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512'
w3 = web3.Web3(web3.Web3.HTTPProvider(RPC_URL))
w31 = web3.Web3(web3.Web3.HTTPProvider(RPC_URL))
w32 = web3.Web3(web3.Web3.HTTPProvider(RPC_URL))
w33 = web3.Web3(web3.Web3.HTTPProvider(RPC_URL))


def fetch_block(height):
    global block_cache, w31, w32, w33
    w3 = random.choice([w31, w32, w33])
    # if '-d' in sys.argv:
    #     w3 = w31
    print('fetch_block', height)
    while True:
        try:
            block = w3.eth.get_block(height, True)
            block_cache[height] = block
            break
        except Exception as e:
            print('Exception', e)
            time.sleep(1)

block_cache = {}
from_block = 1
if '-d' in sys.argv:
    from_block = 1

# req = requests.get('http://127.0.0.1:%s/height?chain=op' % setting.NODE_PORT)
# height = req.json()['height']
# print(height)
# if height:
#     current_block = height
# else:
current_block = from_block
fetch_height = current_block

latest_block = w3.eth.get_block_number()
while True:
    time.sleep(0.5)
    print(current_block, fetch_height, latest_block, latest_block - current_block)
    if fetch_height >= latest_block:
        try:
            latest_block = w3.eth.get_block_number()
        except:
            continue

    if fetch_height <= latest_block:
        print(threading.active_count(), block_cache.keys())
        if threading.active_count() < 4 and len(block_cache.keys()) < 8:
            to_height = min(fetch_height+2, latest_block+1)
            for i in range(fetch_height, to_height):
                thread = threading.Thread(target=fetch_block, args=[i])
                thread.start()
            fetch_height = to_height

    if current_block <= latest_block:
        block = block_cache.get(current_block)
        if block:
            print(current_block, len(block_cache.keys()))
            del block_cache[current_block]

            topups_created = []
            topups_spent = []
            for tx in block.transactions:
                print('to', tx['to'])
                if tx['to'] == PAYMENT_CONTRACT:
                    # print(transaction)
                    tx_receipt = w31.eth.get_transaction_receipt(tx['hash'])
                    # print(tx_receipt['logs'])
                    logs = tx_receipt['logs']
                    for log in logs:
                        if log['address'] == PAYMENT_CONTRACT:
                            print(log['topics'][0].hex())
                            if log['topics'][0].hex() == TOPUP_CREATED_EVENT:
                                topup_id, = eth_abi.decode(['uint256'], log['topics'][1])
                                spender, = eth_abi.decode(['address'], log['topics'][2])
                                # print(log['data'])
                                amount, = eth_abi.decode(['uint256'], log['data'])
                                print('TopupCreated', topup_id, spender, amount)
                                topups_created.append([topup_id, spender, amount])

                            elif log['topics'][0].hex() == TOPUP_SPENT_EVENT:
                                topup_id, = eth_abi.decode(['uint256'], log['topics'][1])
                                spender, = eth_abi.decode(['address'], log['topics'][2])
                                remaining_balance, = eth_abi.decode(['uint256'], log['data'])
                                print('TopupSpent', topup_id, spender, remaining_balance)
                                topups_spent.append([topup_id, spender, remaining_balance])
                                # print('TopupSpent', topup_id, creator, amount, spender)

            body = {'created': topups_created, 'spent': topups_spent}
            data = json.dumps(body)
            while True:
                try:
                    # requests.post('http://127.0.0.1:%s/watch' % GATEWAY_PORT, data=data.encode('utf8'))
                    break
                except:
                    time.sleep(0.5)

            current_block += 1

    if current_block == latest_block:
        time.sleep(1)
