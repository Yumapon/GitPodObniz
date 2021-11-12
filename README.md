# メモ

```sh

#
cd getinputdata/

pip install -r requirements.txt

az login --use-device-code 

func azure functionapp publish getinputdatafunc --python


#関数の作成(node.js)
npm install obniz 

func new --name PeriodicAcquisitionOfDataFunc --template "Timer trigger"

az functionapp create \
--resource-group ObnizInputData-rg \
--consumption-plan-location japanwest \
--runtime node \
--runtime-version 12 \
--functions-version 3 \
--name PeriodicAcquisitionOfDataFunc \
--storage-account obnizinputdata

func azure functionapp publish PeriodicAcquisitionOfDataFunc

pip install -r requirements.txt 

```
