from server import utils


class Address:
    @classmethod
    def _import_address(cls, address: str, rescan: bool = False):
        """
        Import an address into the wallet so that listunspent works.
        - rescan = False (fast, only sees future txs)
        - rescan = True (slow, scans full chain history)
        """
        try:
            utils.make_request("importaddress", [address, "", rescan])
        except Exception:
            # If already imported, Core throws an error, safe to ignore
            pass

    @classmethod
    def balance(cls, address: str):
        # Import without rescan (fast)
        cls._import_address(address, rescan=False)

        # Query unspent outputs
        data = utils.make_request(
            "listunspent", [0, 9999999, [address]]
        )

        if data["error"] is None:
            balance = sum([utxo["amount"] for utxo in data["result"]])
            satoshi_amount = int(balance * 100000000)
            data["result"] = {"balance": f"{satoshi_amount:02d}"}

        return data

    @classmethod
    def mempool(cls, address: str, raw=False):
        data = utils.make_request("getrawmempool", [True])

        if data["error"] is None:
            transactions = []
            for txid, txdata in data["result"].items():
                # Look inside vout addresses
                for vout in txdata.get("vout", []):
                    if "addresses" in vout.get("scriptPubKey", {}):
                        if address in vout["scriptPubKey"]["addresses"]:
                            transactions.append(txid)
                            break

            total = len(transactions)
            data["result"] = {"tx": transactions, "txcount": total}
        else:
            data["result"] = {"tx": [], "txcount": 0}

        return data


    @classmethod
    def unspent(cls, address: str, amount: int):
        cls._import_address(address, rescan=False)

        data = utils.make_request(
            "listunspent", [0, 9999999, [address]]
        )

        if data["error"] is None:
            total = 0
            utxos = []

            for utxo in data["result"]:
                utxos.append(
                    {
                        "txid": utxo["txid"],
                        "index": utxo["vout"],
                        "script": utxo["scriptPubKey"],
                        "value": int(utxo["amount"] * 100000000),  # satoshis
                        "height": utxo.get("height", 0),
                    }
                )

                total += utxo["amount"]

                if total > amount:
                    break

            data["result"] = utxos

        return data

    @classmethod
    def history(cls, address: str):
        # Fallback to wallet transactions (only works if address is in wallet)
        data = utils.make_request("listtransactions", ["*", 1000, 0, True])

        if data["error"] is None:
            # Filter only txs involving this address
            transactions = []
            for tx in data["result"]:
                if "address" in tx and tx["address"] == address:
                    transactions.append(tx["txid"])

            transactions = transactions[::-1]
            data["result"] = {"tx": transactions, "txcount": len(transactions)}

        return data


    @classmethod
    def check(cls, addresses: list):
        addresses = list(set(addresses))
        result = []
        for address in addresses:
            data = utils.make_request("getaddresstxids", [{"addresses": [address]}])
            if data["error"] is None and len(data["result"]) > 0:
                result.append(address)

        return utils.response(result)