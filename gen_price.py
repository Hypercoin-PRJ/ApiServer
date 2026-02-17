import requests
import math

def gen_p():
    response = requests.get("https://api.coinpaprika.com/v1/tickers/hrc-hypercoin", timeout=10)
    response.raise_for_status()
    data = response.json()
    gusd = round(float(data['quotes']['USD']['price']), 10)
    fname = "price.log"
    livecoinwatch_api = None
    with open('/root/ApiServer/api-key.log', 'r') as file:
        for line in file:
            if 'endline' in line.lower():
                break  
            if line.startswith('livecoinwatch='):
                livecoinwatch_api = line.strip().split('=')[1]  
    #---
    url = "https://api.livecoinwatch.com/coins/single"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": livecoinwatch_api
    }
    payload = {
        "currency": "USD",
        "code": "__HRC",
        "meta": True
    }
    response = requests.post(url, headers=headers, json=payload, timeout=10)
    response.raise_for_status()
    data3 = response.json()
    bkc_lcw_def = data3['rate']
    def_bkc_livecoinwatch = 0

    if not isinstance(bkc_lcw_def, (int, float)):
        def_bkc_livecoinwatch = 0
    else:
        def_bkc_livecoinwatch = round(float(data3['rate']), 10)
    if not isinstance(gusd, (int, float)):
        gusd = 0
    #---
    rtext = str(gusd)
    getmax_val = max(def_bkc_livecoinwatch,gusd)
    
    response2 = requests.get("https://api.coinpaprika.com/v1/tickers/btc-bitcoin", timeout=10)
    response2.raise_for_status()
    data2 = response2.json()
    btc_price = float(data2['quotes']['USD']['price'])
    btc_amount = getmax_val / btc_price
    formatted_btc_amount = f"{btc_amount:.10f}"
    formatted_usd_amount = f"{getmax_val:.10f}"
    
    if len(rtext) > 0:
        with open(fname, 'w') as file:
            file.write(str(formatted_usd_amount)+","+formatted_btc_amount)
    else:
        print("Nothing to write — text is empty.")
        
if __name__ == "__main__":
    gen_p()