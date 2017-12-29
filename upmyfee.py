#!/usr/bin/env python
import argparse
from decimal import Decimal
from pprint import pprint

from authproxy import AuthServiceProxy

UNLOCK_TIMEOUT = 60


class UpMyFee():
    def __init__(self, service_url, wallet_unlock_timeout):
        self.wallet_unlock_timeout = wallet_unlock_timeout
        self.api = AuthServiceProxy(service_url=service_url, verify=False)

    def get_tx_amount(self, txid):
        return self.api.gettransaction(txid)['amount']

    def get_new_tx(self, orig_tx, payer, to, fee):
        new_amount = 0
        orig_amount = 0

        if len(orig_tx['vout']) > 2:
            raise BaseException('Multiaddresses is NOT supported')

        orig_vins = [{'txid': t['txid'], 'vout': t['vout']} for t in orig_tx['vin']]
        vins_sum_amounts = sum([self.get_tx_amount(t['txid']) for t in orig_vins])

        orig_vout = orig_tx['vout']
        vouts_sum_amounts = sum(v['value'] for v in orig_vout)

        orig_fee = vins_sum_amounts - vouts_sum_amounts

        if orig_fee >= fee:
            raise BaseException('New tx fee should be more than the original!')

        for v in orig_vout:
            addresses = v['scriptPubKey']['addresses']
            if len(addresses) > 1:
                raise BaseException('Multiaddresses is NOT supported')

        if payer not in [v['scriptPubKey']['addresses'][0] for v in orig_vout]:
            raise BaseException('Payer address not in transaction')

        fee_diff = fee - orig_fee

        new_vouts = {}

        for vout in orig_vout:
            addr = vout['scriptPubKey']['addresses'][0]
            amount = vout['value']

            if addr == payer:
                orig_amount = amount
                amount -= fee_diff
                new_amount = amount
                new_vouts[to] = new_amount
            else:
                new_vouts[addr] = amount

        if new_amount <= Decimal(0):
            raise BaseException('New fee is very big!')

        return orig_vins, new_vouts, orig_fee, fee_diff, orig_amount, new_amount

    def get_user_confirm(self, payer, to, txid, fee, orig_fee, fee_diff, orig_amount, new_amount):
        print("Transaction ID:\t%s" % txid)
        print("Payer address:\t%s" % payer)
        print("New recipient:\t%s" % to)
        print("Orig fee:\t%s" % orig_fee)
        print("New fee:\t%s" % fee)
        print("Diff fee:\t%s" % fee_diff)
        print("Orig amount:\t%s" % orig_amount)
        print("New amount:\t%s" % new_amount)

        user_result = input("All is correct? (yes/no): ")
        if user_result != "yes":
            print('Exit.')
            return False

        return True

    def change_fee(self, payer, to, txid, fee, debug):
        orig_rawtx = self.api.getrawtransaction(txid)
        orig_tx = self.api.decoderawtransaction(orig_rawtx)

        vin, vout, orig_fee, fee_diff, orig_amount, new_amount = self.get_new_tx(orig_tx, payer, to, fee)

        new_rawtx = self.api.createrawtransaction(vin, vout)
        new_tx = self.api.decoderawtransaction(new_rawtx)

        if debug:
            pprint(new_tx)

        if not self.get_user_confirm(payer, to, txid, fee, orig_fee, fee_diff, orig_amount, new_amount):
            return False

        passphrase = input("Please enter the wallet passphrase: ")

        self.api.walletpassphrase(passphrase, self.wallet_unlock_timeout)

        tx_sign_result = self.api.signrawtransaction(new_rawtx)
        if not tx_sign_result['complete']:
            raise BaseException('Error sign transaction: %s' % str(tx_sign_result))

        tx_signed_hex = tx_sign_result['hex']
        tx_signed = self.api.decoderawtransaction(tx_signed_hex)

        if debug:
            pprint(tx_signed)

        print('HEX of signed transaction: ')
        print(print(tx_signed_hex))
        print('You can decode and broadcast transaction use https://blockchain.info/pushtx')

        user_result = input("Broadcast transaction using your Bitcoin node? (yes/no): ")
        if user_result != "yes":
            print('Exit.')
            return False

        sent_txid = self.api.sendrawtransaction(tx_signed_hex)
        print('New TxID: %s' % sent_txid)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Up bitcoin transaction tools')
    parser.add_argument('--rpc-url', help='Bitcoin-RPC URL', required=True)
    parser.add_argument('--payer', help='Payer Bitcoin address', required=True)
    parser.add_argument('--to', help='New transaction recipient', required=True)
    parser.add_argument('--txid', help='ID of Bitcoin Transaction without confirmation', required=True)
    parser.add_argument('--fee', help='New fee', required=True)
    parser.add_argument('--debug', help='Debug mode', default=False, type=bool)

    args = parser.parse_args()

    service_url = args.rpc_url
    payer = args.payer
    to = args.to
    txid = args.txid
    debug = args.debug

    try:
        fee = Decimal(args.fee)
    except:
        raise argparse.ArgumentTypeError('Fee most be decimal type')

    upmyfee = UpMyFee(service_url, UNLOCK_TIMEOUT)
    upmyfee.change_fee(payer, to, txid, fee, debug)
