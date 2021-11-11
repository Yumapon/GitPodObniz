import logging

import azure.functions as func
import requests
import datetime

from PeriodicAcquisitionOfDataFunc.cosmosdb import DatabaseConnection
from PeriodicAcquisitionOfDataFunc.cosmosdb import getItem, getReplacedItem


def main(req: func.HttpRequest) -> func.HttpResponse:

    """
    Cosmos DBからお気に入り情報を取得し、メイン関数を実行します

    Parameters
    -----------
    req : HttpRequest
    
    Returns
    -----------
    HttpResponse

    """

    logging.info('Python HTTP trigger function processed a request.')

    #reqから照度、温度を取得
    averageill = float(req.params.get('averageill'))
    temp = req.params.get('temp')

    #照度を判定
    if averageill > 4.6:
        sun = "True"
    else:
        sun = "False"

    #SoujiさんAPIで湿度を取得
    print('APIを呼び出します')
    url = "https://hack2021goudou.azurewebsites.net/api/gethumid?code=gjHcmUhiNajYsy8f18vkEsV2JsoGo1LUWtEHz1A/yykhrob66kqA3w=="
    apireq = requests.get(url)
    #TODO: Soujiさんにcode:関数キーが何か確認
    pyaload = {"code":"xxxx"}
    data = apireq.json()
    humid = data['humid']

    #TODO: なんとかAzure Functionのoutとバインディングできそうだが、面倒すぎるのでやめる。
    #Cosmosdbの準備
    dbConnection = DatabaseConnection()

    #Cosmosdbの初期化（不要）
    #print(dbConnection.initialize_database())
    #print(dbConnection.initialize_container())

    #Cosmosdbからデータを取得
    items = dbConnection.read_items()

    #SoujiさんAPIへ送付するデータを作成

    #debug: 温度、湿度、天気
    print('temp:' + temp)
    print('humid:' + humid)
    print('sun:' + sun)

    #favデータ作成
    favstr = ''
    for item in items:
        favstr = favstr + item['temp'][0:4] + ',' + item['humid'] + ','

    favstr = favstr[:-1]
    print('fav:',favstr)

    #Soujiさんのメイン関数をキック
    print('APIを呼び出します')
    url = "https://hack2021goudou.azurewebsites.net/api/main"
    payload = {
        "fav": favstr,
        "temp": temp,
        "humid": humid,
        "sun": sun,
        "code": "iOsvEWB/pWnWAPOJNsZKOH9LopyciYvQ8R81N3A8i72w8N0kmvM4lQ==",
        "test_isfav": "False"
    }
    apires = requests.get(url,payload)

    print(apires.url)
    print(apires.status_code)

    return func.HttpResponse(
        "OK!!!",
        status_code=200
    )