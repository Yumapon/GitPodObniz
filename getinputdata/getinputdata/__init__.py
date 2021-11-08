import logging

import azure.functions as func
from cosmos import DatabaseConnection
from cosmos import getItem, getReplacedItem


def main(req: func.HttpRequest) -> func.HttpResponse:

    print("---")
    dbConnection = DatabaseConnection()

    print(dbConnection.initialize_database())
    print(dbConnection.initialize_container())

    dbConnection.create_item(getItem("1"))
    dbConnection.create_item(getItem("2"))
    dbConnection.create_item(getItem("3"))
    dbConnection.upsert_item(getReplacedItem("3"))
    dbConnection.upsert_item(getReplacedItem("4"))
    dbConnection.delete_item(getItem("2"))

    print("---")
    itemList = dbConnection.read_items()
    for item in itemList:
        print(item)

    """
    logging.info('Python HTTP trigger function processed a request.')

    name = req.params.get('name')

    doc.set(func.Document.from_json(request_body))

    if not name:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            name = req_body.get('name')

    if name:
        return func.HttpResponse(f"Hello, {name}. This HTTP triggered function executed successfully.")
    else:
        return func.HttpResponse(
             "This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response.",
             status_code=200
        )
    """
