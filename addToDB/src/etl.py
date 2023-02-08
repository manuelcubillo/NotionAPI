from asyncio import events
import json
from multiprocessing import Event
from urllib import response
import urllib3
import configparser
from  schema import getSchemaTEST, getSchemaPROv1
from datetime import datetime
from pytz import timezone
import boto3
from botocore.config import Config
import logging
import os
import boto3
 
# Define the client to interact with AWS Lambda
client = boto3.client('lambda')

logging.basicConfig(filename='log.log', filemode="w", level=logging.DEBUG)


def getKeys(mode, config):

    notion_endpoint_createPage, notion_bearer_token = "", ""

    if mode == 'pro':
        logging.debug("Using SSM service to get credentials")

        # Initialize SSM Client
        config = Config(
        retries = {
            'max_attempts': 10,
            'mode': 'standard'
        },
        region_name = "eu-west-1"
        )
        ssm_client = boto3.client('ssm', config = config)
        # Get the API Key from SSM
        #ssm_name = os.getenv('SSM_KEY_NAME', '/amplify/AWS_HASH_KEY/YOUR_AMPLIFY_ENVIRONEMT/AMPLIFY_mycoolapi_MY_COOL_API_KEY')
        notion_endpoint_createPage = ssm_client.get_parameter(Name="notion_endpoint_createPage", WithDecryption=True)['Parameter']['Value']
        notion_bearer_token = ssm_client.get_parameter(Name="notion_bearer_token", WithDecryption=True)['Parameter']['Value']
        notion_db_id_pro = ssm_client.get_parameter(Name="notion_db_id_pro", WithDecryption=True)['Parameter']['Value']

    else:
        logging.debug("Using config file to get credentials")
        notion_endpoint_createPage = config['URLS']['ENDPOINT']
        notion_bearer_token = config['KEYS']['BEARER_TOKEN']
        notion_db_id_pro = config['KEYS']['DATABASE_ID_PRO'] 


    return notion_endpoint_createPage, notion_db_id_pro, notion_bearer_token


def extract_Structured(events, schema):
    """
    check every parameters is in the message
    """

    for key in json.loads(schema):
        if not key in events.keys(): 
            raise Exception("Sorry, missing values in message, or wrong key {} not in the message".format(key))


    #get current date in format yyyy-mm-dd
    fmt = "%Y-%m-%d"
    now_time = datetime.now(timezone('Europe/Madrid'))
    events['date'] = now_time.strftime(fmt)

    #get categories
    cat = events['Categories']
    if len(cat) > 0: 
        categories_string = ""
        
        for index, category in enumerate(cat):
            categories_string += """{ "name" : \"""" + category + """\" }"""
            
            if (len(cat) - 1) > index:
                categories_string += ","
        
        events['Categories'] = categories_string

    else:
        raise Exception("Category field missing value.")

    events = parseDot(events)

    return events

def parseDot(events):
    """
     notion use dot for decimals instead of coma
    """
    # parse expenses
    exp = events['Expenses']
    exp = exp.replace(',','.') 
    events['Expenses'] = exp

    # parse times
    ts = events['T.Sport']
    ts = ts.replace(',','.') 
    events['T.Sports'] = ts

    tp = events['T.Projects']
    tp = tp.replace(',','.') 
    events['T.Projects'] = tp

    tr = events['T.Reading']
    tr = tr.replace(',','.') 
    events['T.Reading'] = tr

    return events

def extract_Not_Structured(events, schema):
    """
    not implemented yet
    
    """
    raise Exception("Sorry, not structured data is not implemented yet")

def transform(db_id, params, schemaPro = False):
    """
    build body message
    """

    if schemaPro:
        body = getSchemaPROv1(db_id, params)
    else:
        body = getSchemaTEST(db_id, params)

    return body

def load(url, token, body):
    """
    send to Notion API the request

    Returns:
        result of the request
    """

    headers = {'Notion-Version': '2021-08-16',
    'Content-Type': 'application/json',
    'Authorization' : 'Bearer {0}'.format(token)}

    
    http = urllib3.PoolManager()
    response = http.request('POST',
                            url,
                            body = body,
                            headers = headers)

    dataJson = json.loads(response.data.decode('utf8'))
    return dataJson

def getWeekExpenses():
    """
    call lambda to work out the expenses of the current week
    """

    inputParams = {
    "mode" : "pro",
    "monthQuery": "1",
    "query" : "weekExpenses"
    }

    print("Calling queryDB lambda function...")
    response = client.invoke(
        FunctionName = 'arn:aws:lambda:eu-west-1:473090859996:function:sam-notion-app-queryDBFunction-xGIwS3Yp7xbh',
        InvocationType = 'RequestResponse',
        Payload = json.dumps(inputParams)
    )
    
    payload = json.load(response['Payload'])['body']    

    print("Total week expenses", payload)

    return payload

def handler(event, context):
    config = configparser.ConfigParser()
    config.read('config.cfg')

    print("Event: ", json.dumps(event)) 
    
    if 'body' in event:
        payload = json.loads(event['body']) # print event
    else:
        payload = event

    mode = 'local' if  payload['mode'] == 'local' else 'pro' # select mode of execution. Affect to place where read keys

    notion_endpoint_createPage, db_key, notion_bearer_token = getKeys(mode, config)

    flagPro = config.get('DATA','SCHEMA') == 'PRO'

    structuredFlag = payload['StructuredData'] == True

    if structuredFlag: 
        params = extract_Structured(payload, config.get('DATA','DATA_SCHEMA'))
    else:
        params = extract_Not_Structured(payload, config.get('DATA','DATA_SCHEMA'))

    body = transform(db_key, params, schemaPro=flagPro)
    response = load(notion_endpoint_createPage, notion_bearer_token, body)

    print("Entry added to Notion DB")
    # get total week expenses
    weekExpenses = getWeekExpenses()

    return {
        "statusCode": 200,
        "headers": {
                "Access-Control-Allow-Origin": os.environ.get('ALLOWED_ORIGINS')
            },
        "body":  weekExpenses
    }
