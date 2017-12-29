# UpMyFee
Python script for up unconfirmed Bitcoin transaction fee.

Sometimes transactions in Bitcoin are confirmed for a very long time.
This is usually due to network congestion and / or low commission.

If the transaction does not have any confirmation yet, you can correct the situation.

Also you can change recipient address of unconfirmed transaction.

# How it works?
This script creates a new transaction, similar to the original, but with a large fee and new recipient address.

Why you need create new recipient addres?
Because if you submit some transaction with some addresses - you can receive
`Error #-26: 18: txn-mempool-conflict`

## More details?
Application use Bitcoin RPC for:
* get and decode raw transaction
* get vin transactions for create new tx
* change one tx vout amount for extend fee
* create and sign new raw transaction
* send edited transaction to Bitcoin Blockchain

# Requirements
* Bitcoin node with the RPC access and address from where the transaction was sent. `--txindex` flag is required.
* Python 3
* Python [requests](http://docs.python-requests.org/en/master/)

# Usage

## From scratch

    git clone https://github.com/kuberstack/upmyfee.git
    cd upmyfee
    pip install -r requirements.txt
    
    # ./upmyfee.py --help
    usage: upmyfee.py [-h] --rpc-url RPC_URL --payer PAYER --to TO --txid TXID
                      --fee FEE [--debug DEBUG]
    
    Up bitcoin transaction tools
    
    optional arguments:
      -h, --help         show this help message and exit
      --rpc-url RPC_URL  Bitcoin-RPC URL
      --payer PAYER      Payer Bitcoin address
      --to TO            New transaction recipient
      --txid TXID        ID of Bitcoin Transaction without confirmation
      --fee FEE          New fee
      --debug DEBUG      Debug mode
      
    # Example
    # ./upmyfee.py --rpc-url='https://rpcuser:rpcpassword@localhost:8332' \
        --txid=43d234c7961261298cd9eb421e31146620be52db1c4ab45cecef022a5c3d85c0 \
        --payer=mn8Aqp424K8q7A6cpjvQnkEmhrUcRfARoG \
        --to=mtCWVpxZ46bK9dBM2gELgnxu711kEKefK8 \
        --fee=0.003

## Docker way

    git clone https://github.com/kuberstack/upmyfee.git
    cd upmyfee
    docker build -t upmyfee .
    docker run -ti upmyfee --rpc-url='https://rpcuser:rpcpassword@localhost:8332' \
        --txid=43d234c7961261298cd9eb421e31146620be52db1c4ab45cecef022a5c3d85c0 \
        --payer=mn8Aqp424K8q7A6cpjvQnkEmhrUcRfARoG \
        --to=mtCWVpxZ46bK9dBM2gELgnxu711kEKefK8 \
        --fee=0.003