import json
from multiprocessing import Event
from urllib import response
import urllib3
import configparser
from  schema import getSchemaTEST, getSchemaPROv1
from datetime import datetime
from pytz import timezone

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

    # parse expenses
    exp = events['Expenses']
    exp.replace(',','.') # notion use dot for decimals
    events['Expenses'] = exp

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


def handler(event, context):
    config = configparser.ConfigParser()
    config.read('config.cfg')
    
    flagPro = config.get('DATA','SCHEMA') == 'PRO'

    if flagPro:
        db_key = config.get('KEYS','DATABASE_ID_PRO')
    else:
        db_key = config.get('KEYS','DATABASE_ID_TEST')

    structuredFlag = event['StructuredData'] == True

    if structuredFlag: 
        params = extract_Structured(event, config.get('DATA','DATA_SCHEMA'))
    else:
        params = extract_Not_Structured(event, config.get('DATA','DATA_SCHEMA'))

    body = transform(db_key, params, schemaPro=flagPro)
    response = load(config.get('URLS','ENDPOINT'), config.get('KEYS','BEARER_TOKEN'), body)

    return {
        'statusCode': 200,
        'body': response
    }
