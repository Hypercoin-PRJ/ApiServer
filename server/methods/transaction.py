from server import utils
from server import cache
import config
import json

class Transaction():
    
    @classmethod
    def broadcast(cls, raw: str):
        return utils.make_request("sendrawtransaction", [raw])

    @classmethod
    @cache.memoize(timeout=config.cache)
    def decode(cls, raw: str):
        return utils.make_request("decoderawtransaction", [raw])

    @classmethod
    def info(cls, thash: str):
        data = utils.make_request("getrawtransaction", [thash, True])

        # Handle transaction-not-found error (-5) gracefully
        if data.get("error") and data["error"].get("code") == -5:
            return {
                "error": {"code": -5, "message": "Transaction not found"},
                "result": None
            }

        if data["error"] is None:
            # If confirmed, attach block height
            if "blockhash" in data["result"]:
                block = utils.make_request("getblock", [data["result"]["blockhash"]])["result"]
                data["result"]["height"] = block["height"]
            else:
                # In mempool
                data["result"]["height"] = -1

            # Attach vin details (scriptPubKey + value)
            if data["result"]["height"] != 0:
                for index, vin in enumerate(data["result"]["vin"]):
                    if "txid" in vin:
                        vin_data = utils.make_request("getrawtransaction", [vin["txid"], True])
                        if vin_data["error"] is None:
                            prev_vout = vin_data["result"]["vout"][vin["vout"]]
                            data["result"]["vin"][index]["scriptPubKey"] = prev_vout["scriptPubKey"]
                            data["result"]["vin"][index]["value"] = utils.satoshis(prev_vout["value"])

            # Normalize vout values + compute total
            amount = 0
            for index, vout in enumerate(data["result"]["vout"]):
                sat_value = utils.satoshis(vout["value"])
                data["result"]["vout"][index]["value"] = sat_value
                amount += sat_value

            data["result"]["amount"] = amount

        return data


    @classmethod
    @cache.memoize(timeout=config.cache)
    def addresses(cls, tx_data):
        updates = {}
        for tx in tx_data:
            transaction = Transaction().info(tx)
            vin = transaction["result"]["vin"]
            vout = transaction["result"]["vout"]

            for info in vin:
                if "scriptPubKey" in info:
                    if "addresses" in info["scriptPubKey"]:
                        for address in info["scriptPubKey"]["addresses"]:
                            if address in updates:
                                updates[address].append(tx)
                                updates[address] = list(set(updates[address]))
                            else:
                                updates[address] = [tx]

            for info in vout:
                if "scriptPubKey" in info:
                    if "addresses" in info["scriptPubKey"]:
                        for address in info["scriptPubKey"]["addresses"]:
                            if address in updates:
                                updates[address].append(tx)
                                updates[address] = list(set(updates[address]))
                            else:
                                updates[address] = [tx]

        return updates

    @classmethod
    def spent(cls, txid: str):
        return utils.make_request("getspentinfo", [txid])