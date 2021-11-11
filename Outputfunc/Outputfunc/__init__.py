import logging

import azure.functions as func
import requests
import json
from datetime import date, datetime

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    #  out通知取得
    out = req.params.get('out')
    #  obnizURL設定
    url_obniz = 'https://obniz.com/obniz/4412-3035/webhook/20xG44xDmF_1AgkpsfEDWhU34d0eYyWr?'
    #  時＋分　取得
    datetime1 = datetime.now()
    hourmin= str(datetime1.hour) + ":" + str(datetime1.minute)
      
    #hourmin = '22:0'  #2200設定（仮)
    if hourmin == '22:0':
        out = '9'  #22:00だったら9
        payload = {'out':out}
        requests.get(url_obniz,params=payload)
    elif out == '1' or '2' or '3' or '4' or '5':  #光、香りobniz
        payload = {'out':out}
        requests.get(url_obniz,params=payload)
   
    result = {"status":"ok"}
    return func.HttpResponse(
        json.dumps(result),
        mimetype="application/json",
        status_code=200
    )
