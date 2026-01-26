import config
import math
import json
import datetime
import requests
from dateutil.parser import parse
from datetime import datetime, timedelta
from dateutil import parser
from urllib.parse import urlparse
from urllib.parse import parse_qs
import decimal
import sys
import ssl
import time
import traceback
import subprocess
# Increase recursion limit
sys.setrecursionlimit(10000)

def dead_response(message="Invalid Request", rid=config.rid):
    return {"error": {"code": 404, "message": message}, "id": rid}

def response(result, error=None, rid=config.rid):
    return {"error": error, "id": rid, "result": result}

def make_request(method, params=[]):
    headers = {"content-type": "text/plain;"}
    data = json.dumps({"id": config.rid, "method": method, "params": params})

    try:
        return requests.post(config.endpoint, headers=headers, data=data).json()
    except Exception:
        return dead_response()

def reward(height):
    halvings = height // 2102400
    if halvings >= 64:
        return 0
    return int(satoshis(50.00000000) // (2 ** halvings))

def reward2(block_height):
    halvings = 2102400
    getrw = 0
    reward = 0

    if 1 < block_height <= 50000:
        getrw = 25
    elif 50001 <= block_height <= 100000:
        getrw = 15
    elif 100001 <= block_height <= 500000:
        getrw = 5
    else:
        reward = 2.5
        halvings_count = math.floor(block_height / halvings)
        reward = reward / (2 ** halvings_count)
        getrw = reward

    return format(getrw, '.2f')

def significant(num, signum):
    expo = 10**(int(math.log(num, 10)) - signum + 1)
    return expo * (num // expo)

def supplyrt():
    data2 = make_request("gettxoutsetinfo")
    return {
        "halvings": int(0),
        "supply": satoshis(int(data2["result"]["total_amount"])),
        "total/max supply": satoshis(21000000)
    }
def supply(height):
    # ---------Updated for BKC----------------
    getward_c1 = 3500000
    getward_c2 = 2499999       
    getward_c3 = 999980
    halvings_count = 0
    
    if height > 100000 and height <500000:
       calheight = height -  100001
       getward_c4 = calheight * 10
       sub_total_supply = getward_c1 + getward_c2 + getward_c3 + getward_c4 
       supply1 = sub_total_supply
    elif height > 500000 and height<=2102400:
        calheight = height - 500001
        getward_c5 = calheight * 5
        getward_c4 = 3999990 
        sub_total_supply = getward_c1 + getward_c2 + getward_c3 + getward_c4  + getward_c5
    #print('Info message:'+ str(calheight) +" reward:"+ str(getward_c3) +"tt:"+ str(sub_total_supply))
    elif height > 2102400:
        getward_c4 = 3999990
        getward_c5 = 8011990
        h1 = 2.5
        reward = satoshis(5.00000000)
        halvings = 2102400
        supply = reward
        halvings_count = 0
        if height > halvings:
            height = height - halvings
        supplybfhalving = getward_c1 + getward_c2 + getward_c3 + getward_c4 + getward_c5
        sub_total_supply2 = (supplybfhalving + (height * h1))
        sub_total_supply3 = supplybfhalving
    # ---------End Updated----------------
    data2 = make_request("gettxoutsetinfo")
    return {
        "halvings": int(0),
        "supply": satoshis(int(data2["result"]["total_amount"])),
        "total/max supply": satoshis(21000000)
        #"supply": type(str(sub_total_supply) + "00000000")
    }

def satoshis(value):
    return math.ceil(value * math.pow(10, 8))

def amount(value):
    return round(value / math.pow(10, 8), 8)

def getprice():
    return {
            "price_btc": "0.00000000",
            "price_usd": "0.00000000",
            "status": f"Error: {str(e)}"
        }
    
'''def getprice():
    try:
        try:
            result = subprocess.run(
                ['python3', '/root/ApiServer/gen_price.py'],
                check=True,
                capture_output=True,
                text=True
            )
            print("Subprocess output:", result.stdout)
        except subprocess.CalledProcessError as e:
            print("Subprocess failed:")
            print("Return code:", e.returncode)
            print("Output:", e.output)
            print("Error output:", e.stderr)
            raise
            btc = 0.0
            usd = 0.0
        try:
            with open('/root/ApiServer/price.log', 'r') as file:
                content = file.read().strip()

            if not content:
                print("The file is empty.")
            else:
                parts = content.split(',')
                parts = [part.strip() for part in parts]

                if len(parts) >= 2:
                    usd = parts[0]
                    btc = parts[1]
                    #print(f"Part 0: {usd}")
                    #print(f"Part 1: {btc}")
                else:
                    print("The file does not contain enough parts.")
        except FileNotFoundError:
            print("The file '/root/ApiServer/price.log' was not found.")
        except Exception as e:
            print(f"An error occurred: {e}")

        return {
            "price_btc": btc,
            "price_usd": usd,
            "status": "Success"
        }
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return {
            "price_btc": "0.00000000",
            "price_usd": "0.00000000",
            "status": f"Error: {str(e)}"
        }'''

def getprice2():
    url = "https://api.coinpaprika.com/v1/tickers/hrc-hypercoin"
    try:

        response = real_requests.get(url, timeout=10)  
        response.raise_for_status()
        data = response.json()

        btc = float(0.00000000)
        usd = float(data['quotes']['USD']['price'])

        return {
            "price_btc": f"{btc:.8f}",
            "price_usd": f"{usd:.8f}",
            "status": "Success"
        }
    except Exception as e:
        return {
            "price_btc": "0.00000000",
            "price_usd": "0.00000000",
            "status": f"Error: {str(e)}"
        }