import logging

import azure.functions as func
import requests
import datetime

from cosmos import DatabaseConnection
from cosmos import getItem, getReplacedItem


def main(req: func.HttpRequest) -> func.HttpResponse:

    """
    Cosmos DBにデータを格納します。

    Parameters
    -----------
    req : HttpRequest
    
    Returns
    -----------
    HttpResponse

    """

    logging.info('Python HTTP trigger function processed a request.')

    #reqから照度、温度を取得
    illuminance = req.params.get('illuminance')
    temp = req.params.get('temp')

    #SoujiさんAPIで湿度を取得
    url = "https://hack2021goudou.azurewebsites.net/api/gethumid?code=gjHcmUhiNajYsy8f18vkEsV2JsoGo1LUWtEHz1A/yykhrob66kqA3w=="
    apireq = requests.get(url)
    #TODO: Soujiさんにcode:関数キーが何か確認
    pyaload = {"code":"xxxx"}
    humid = req.params.get('humid')

    #TODO: なんとかAzure Functionのoutとバインディングできそうだが、面倒すぎるのでやめる。
    #Cosmosdbの準備
    dbConnection = DatabaseConnection()

    #Cosmosdbの初期化
    print(dbConnection.initialize_database())
    print(dbConnection.initialize_container())

    #主キーとするタイムスタンプを取得し、Cosmosdbへ格納する
    DIFF_JST_FROM_UTC = 9
    now = datetime.datetime.utcnow() + datetime.timedelta(hours=DIFF_JST_FROM_UTC)
    dbConnection.create_item(getItem(now, illuminance, temp, humid))

    return func.HttpResponse("Success!", status_code=200)

