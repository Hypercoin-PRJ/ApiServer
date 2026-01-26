from server.methods.transaction import Transaction
from server import utils
from server import cache
import config


class Block():
    @classmethod
    def height(cls, height: int):
        data = utils.make_request("getblockhash", [height])

        if data["error"] is not None:
            return data

        bhash = data["result"]
        block = utils.make_request("getblock", [bhash])

        if block["error"] is not None:
            return block

        result = block["result"]

        # SAFE txcount
        if "nTx" in result:
            result["txcount"] = result.pop("nTx")
        elif "tx" in result:
            result["txcount"] = len(result["tx"])
        else:
            result["txcount"] = 0

        return {
            "result": result,
            "error": None,
            "id": data.get("id")
        }

    @classmethod
    def hash(cls, bhash: str):
        data = utils.make_request("getblock", [bhash])

        if data["error"] is not None:
            return data

        result = data["result"]

        # SAFE txcount
        if "nTx" in result:
            result["txcount"] = result.pop("nTx")
        elif "tx" in result:
            result["txcount"] = len(result["tx"])
        else:
            result["txcount"] = 0

        return data

    @classmethod
    @cache.memoize(timeout=config.cache)
    def get(cls, height: int):
        return utils.make_request("getblockhash", [height])

    @classmethod
    def range(cls, height: int, offset: int):
        blocks = []

        for h in range(height - (offset - 1), height + 1):
            bhash = utils.make_request("getblockhash", [h])
            nethash = utils.make_request("getnetworkhashps", [120, h])

            if bhash["error"] is not None or nethash["error"] is not None:
                continue

            block = utils.make_request("getblock", [bhash["result"]])
            if block["error"] is not None:
                continue

            result = block["result"]

            # SAFE txcount
            if "nTx" in result:
                result["txcount"] = result.pop("nTx")
            elif "tx" in result:
                result["txcount"] = len(result["tx"])
            else:
                result["txcount"] = 0

            result["nethash"] = int(nethash["result"])
            blocks.append(result)

        return blocks[::-1]

    @classmethod
    @cache.memoize(timeout=config.cache)
    def inputs(cls, bhash: str):
        data = cls.hash(bhash)

        if data["error"] is not None:
            return []

        return Transaction().addresses(data["result"].get("tx", []))
