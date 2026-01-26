from server import utils


class Address:

    @classmethod
    def _has_addressindex(cls):
        """
        Detect if the node supports addressindex RPCs.
        """
        test = utils.make_request("getaddressbalance", ["dummyaddress123"])
        return test["error"] is None or test["error"].get("code") != -32601

    @classmethod
    def _import_address(cls, address: str, rescan: bool = False):
        """
        Import an address as watch-only for wallet-based fallback.
        rescan=False is fast (only future TXs), rescan=True scans full chain.
        """
        try:
            utils.make_request("importaddress", [address, "", rescan])
        except Exception:
            pass  # already imported is fine

    @classmethod
    def balance(cls, address: str):
        if cls._has_addressindex():
            # Fast, works for any address
            data = utils.make_request("getaddressbalance", [address])
            if data["error"] is None:
                data["result"] = {"balance": int(data["result"]["balance"])}
            return data
        else:
            # Wallet fallback
            cls._import_address(address, rescan=False)
            data = utils.make_request("listunspent", [0, 9999999, [address]])
            if data["error"] is None:
                total = sum([utxo["amount"] for utxo in data["result"]])
                data["result"] = {"balance": int(total * 100_000_000)}
            return data

    @classmethod
    def unspent(cls, address: str, amount: int = 0):
        if cls._has_addressindex():
            data = utils.make_request("getaddressutxos", [address, utils.amount(amount)])
            if data["error"] is None:
                utxos = []
                for u in data["result"]:
                    utxos.append({
                        "txid": u["txid"],
                        "index": u["outputIndex"],
                        "script": u["script"],
                        "value": u["satoshis"],
                        "height": u["height"]
                    })
                data["result"] = utxos
            return data
        else:
            cls._import_address(address, rescan=False)
            data = utils.make_request("listunspent", [0, 9999999, [address]])
            if data["error"] is None:
                utxos = []
                total = 0
                for u in data["result"]:
                    if amount > 0 and u["amount"] < amount:
                        continue
                    utxos.append({
                        "txid": u["txid"],
                        "index": u["vout"],
                        "script": u["scriptPubKey"],
                        "value": int(u["amount"] * 100_000_000),
                        "height": u.get("height", 0)
                    })
                    total += u["amount"]
                    if total > amount:
                        break
                data["result"] = utxos
            return data

    @classmethod
    def mempool(cls, address: str, raw: bool = False):
        if cls._has_addressindex():
            data = utils.make_request("getaddressmempool", [address])
            if data["error"] is None:
                txs = [tx["txid"] for tx in data["result"]]
                if not raw:
                    txs_detail = []
                    for tx in data["result"]:
                        d = tx.copy()
                        d.pop("address", None)
                        txs_detail.append(d)
                    txs = txs_detail
                data["result"] = {"tx": txs, "txcount": len(txs)}
            return data
        else:
            # Wallet fallback
            cls._import_address(address, rescan=False)
            mempool = utils.make_request("getrawmempool", [True])
            if mempool["error"] is None:
                txs = []
                for txid, txdata in mempool["result"].items():
                    for vout in txdata.get("vout", []):
                        if "addresses" in vout.get("scriptPubKey", {}):
                            if address in vout["scriptPubKey"]["addresses"]:
                                txs.append(txid if raw else txdata)
                                break
                mempool["result"] = {"tx": txs, "txcount": len(txs)}
            return mempool

    @classmethod
    def history(cls, address: str):
        if cls._has_addressindex():
            data = utils.make_request("getaddresstxids", [address])
            if data["error"] is None:
                txs = data["result"][::-1]  # newest first
                data["result"] = {"tx": txs, "txcount": len(txs)}
            return data
        else:
            # Wallet fallback
            cls._import_address(address, rescan=False)
            data = utils.make_request("listtransactions", ["*", 1000, 0, True])
            if data["error"] is None:
                txs = [tx["txid"] for tx in data["result"] if tx.get("address") == address]
                data["result"] = {"tx": txs[::-1], "txcount": len(txs)}
            return data

    @classmethod
    def check(cls, addresses: list):
        addresses = list(set(addresses))
        result = []
        if cls._has_addressindex():
            for addr in addresses:
                data = utils.make_request("getaddresstxids", [addr])
                if data["error"] is None and len(data["result"]) > 0:
                    result.append(addr)
        else:
            # Wallet fallback
            for addr in addresses:
                cls._import_address(addr, rescan=False)
                data = utils.make_request("listunspent", [0, 9999999, [addr]])
                if data["error"] is None and len(data["result"]) > 0:
                    result.append(addr)
        return utils.response(result)
