from dataclasses import dataclass
import json
from multiprocessing import Event
from sqlite3 import Timestamp
from urllib import response
import urllib3
import configparser
import time
import calendar
from  schema import getSchemaTEST, getSchemaPROv1
from datetime import datetime, date, timedelta
from pytz import timezone
from dataclasses import dataclass
import logging
import json
import os
import urllib
from urllib import request, parse
import boto3
from botocore.config import Config
from users import getUserKeys

logging.basicConfig(filename='log.log', filemode="w", level=logging.INFO)

@dataclass
class item:
    """
    item object in notion DB
    """
    name:str = ""
    date:datetime = None # type: ignore
    expenses:str = ""
    month:str = ""
    year:str = ""
    day:str = ""

@dataclass
class weekReport:
    """
    summary of week
    """
    month : str = ''
    weekIni : str = ''
    weekEnd : str = ''
    totalAmount : int = 0

def getKeys(mode, config):
    
    notion_endpoint_querydb, db_key, notion_bearer_token = "", "", ""

    if mode == 'pro':
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
        notion_endpoint_querydb = ssm_client.get_parameter(Name="notion_endpoint_querydb", WithDecryption=True)['Parameter']['Value']
        notion_bearer_token = ssm_client.get_parameter(Name="notion_bearer_token", WithDecryption=True)['Parameter']['Value']

    else:
        notion_endpoint_querydb = config['URLS']['ENDPOINT']
        notion_bearer_token = config['KEYS']['BEARER_TOKEN']


    return notion_endpoint_querydb, db_key,  notion_bearer_token

def fetch_data(url, token, iniDate, endDate):
    """
    fetch data from notion db
    """

    headers = {'Notion-Version': '2021-08-16',
    'Content-Type': 'application/json',
    'Authorization' : 'Bearer {0}'.format(token)}
    
    http = urllib3.PoolManager()
    response = http.request('POST',
                            url,
                            body = get_Date_Filter(iniDate, endDate),
                            headers = headers)

    dataJson = json.loads(response.data.decode('utf8'))
    return dataJson['results']

def get_Date_Filter(iniDate, endDate):
    """
    create date filter to fetch data from notion
    """
    week_day = endDate.weekday()
    day = endDate.day -1
    toD = endDate.strftime('%Y-%m-%d')
    fromD = iniDate.strftime('%Y-%m-%d')

    # fromD = (endDate - timedelta(days=day)).strftime('%Y-%m-%d') # get month first day of the month

    print("ini requested to notion: ", fromD)
    print("end requested to notion: ", toD)
    return str("""{
    "filter": {
          "and": [
              {
                  "property": "date",
                  "date": {
                      "on_or_before": \"""" + toD + """\"
                  }
              },
              {
                  "property": "date",
                  "date": {
                      "on_or_after": \"""" + fromD + """\"
                  }
              }
          ]
      }
    }""")

def format_data(data):
    """
    transform data into a known format
    """
    new_format = []

    for d in data:
        if len(d['properties']['item']['title']) == 0: # skip rows without name
            continue
        
        i = item()
        i.name = d['properties']['item']['title'][0]['plain_text']
        i.expenses = d['properties']['Expenses']['number']
        dateParts = d['properties']['date']['date']['start'].split('-')
        
        if len(dateParts) < 2: # if there is not date, skip this data
            continue

        i.date = datetime.fromisoformat( d['properties']['date']['date']['start'])
        i.month = dateParts[1]
        i.year = dateParts[0]
        i.day = dateParts[2]

        new_format.append(i)
        

    return data, new_format

def group_by_week(data_formatted, iniDate, endDate):
    """
    take a formated data and work out the expenses by week
    """
    month_report = [] # list of weeks reports

    current_date = endDate
    current_month = current_date.strftime('%m')
    current_year = current_date.strftime('%y')
    current_day =  current_date.strftime("%d")
    week_day = current_date.weekday()

    # first iter
    fromDate = current_date - timedelta(days=week_day)
    toDate = current_date
    totalAmount = getExpensesBetweenDays(data_formatted, fromDate, toDate)

    wk = create_week_report(current_month, fromDate, toDate, totalAmount)

    month_report.append(wk)

    # others iter -  stop when month change
    # number day of month - number day of week -> if there are more days, keep processing
    daysToProcess = int(fromDate.strftime("%d")) - 1
    if(daysToProcess > 0):
        
        offset_toDay = get_offSetToDay(toDate) # move toDate to the nearest Sunday

        # work out if there is more than one week, or there are not enough days to make a full week
        while(daysToProcess > 0):
            wk = weekReport()

            if(daysToProcess >= 7):
                fromDate = fromDate - timedelta(days=7)
                toDate =  toDate - timedelta(days=offset_toDay)
                daysToProcess = daysToProcess - 7
            else:
                fromDate = fromDate - timedelta(days=daysToProcess)
                toDate =  toDate - timedelta(days=offset_toDay)
                daysToProcess = 0

            offset_toDay = 7 # move toDate 7 days


            totalAmount = getExpensesBetweenDays(data_formatted, fromDate , toDate )
            wk = create_week_report(current_month, fromDate, toDate, totalAmount)
            month_report.append(wk)

    return month_report

def create_week_report(current_month, fromDate, toDate, totalAmount):
    """
    week report constructor

    Args:
        current_month (_type_): _description_
        fromDate (_type_): _description_
        toDate (_type_): _description_
        totalAmount (_type_): _description_

    Returns:
        _type_: _description_
    """
    wk = weekReport()
    wk.month = current_month
    wk.weekIni = fromDate
    wk.weekEnd = toDate
    wk.totalAmount = totalAmount
    return wk

def getTotalMonth(m_report):
    """
    return total expense amount of the month

    Args:
        m_report (_type_): _description_

    Returns:
        _type_: _description_
    """
    total = 0

    for w in m_report:
        total = total + w.totalAmount

    return total

def get_offSetToDay(toDate):
    """
    datetime.date consider monday as 1
    """
    if(toDate.isoweekday() == 1):
        return 1
    else:
        return toDate.isoweekday()

def getExpensesBetweenDays(data_formatted, fromDate: datetime, toDate: datetime):
    """
    calcule the sum of expenses those are between a date range. 
    ini and end date are also taken into account

    Args:
        data_formatted (_type_): _description_
        fromDate (datetime): _description_
        toDate (datetime): _description_

    Returns:
        _type_: _description_
    """
    amount = 0

    for d in data_formatted:
        logging.debug(d.name + " " + d.date.strftime("%m/%d/%Y")  + " " + str(d.expenses))

    size = len(data_formatted)-1

    result = filter(lambda x : datetime.timestamp(x.date) >= time.mktime(fromDate.timetuple()) and 
    datetime.timestamp(x.date) <= time.mktime(toDate.timetuple()), data_formatted)        
    result = list(result)
    
    if len(result) > 0:
        for x in result:
            amount = amount + int(x.expenses)


    return amount

def getDateRange(month):
    """
    given a month return the first and last day in datetime format
    if it is the current month, return today as endDate
    Args:
        month (_type_): _description_
    """

    year = date.today().strftime("%Y")
    lastDay = calendar.monthrange(int(year), int(month))[1]
    d = "1/"+str(month)+"/"+year
    ini = datetime.strptime(d, '%d/%m/%Y')
    d = str(lastDay)+"/"+str(month)+"/"+year
    end = datetime.strptime(d, '%d/%m/%Y')

    if(date.today().strftime("%m") == month):
        end = date.today()

    return ini, end

def create_message(m_report):
    """
    make a string message from the report
    """

    msg = ""
    msg += "\n**** WEEKLY REPORT **** \n"

    for week in m_report:
        msg += "Report from " + week.weekIni.strftime("%d/%m/%Y") + "\n"
        msg += "To... " + week.weekEnd.strftime("%d/%m/%Y") + "\n"
        msg += "Total week -> " + str(week.totalAmount) + "\n"
        msg += "+-+-+-+-+-+-+-+-+-+-+ \n"

    msg += "-> TOTAL MONTH: " + str(getTotalMonth(m_report)) + " <-\n"
    msg += "----------------------"

    return msg

def getMonthReport(month, notion_endpoint_querydb, notion_bearer_token):
    """
    return a string message with the full month report
    """
     # 0. get date range depending of the month 
    iniDate, endDate = getDateRange(month)
    # 1. download data from notion DB, for a delimited period of time
    data = fetch_data(notion_endpoint_querydb, notion_bearer_token, iniDate, endDate)
    # 2. parse information from db to a item object 
    data, data_formatted = format_data(data)
    # 3. group the data by week to show the results
    m_report = group_by_week(data_formatted, iniDate, endDate)
    # 4. make a string message from the report
    msg = create_message(m_report)

    return msg

def getCurrentWeekExpenses(notion_endpoint_querydb, notion_bearer_token):
    """
    return number with the total expenses of the current week
    """
    # 0. get date range
    today = datetime.today()
    numDays = today.isoweekday() - 1
    fromD = (today - timedelta(days=numDays)) 
    fromD = datetime(year=fromD.year, month=fromD.month, day=fromD.day, hour=0, minute=0, second=0)

    # 2. query esas fechas
    data = fetch_data(notion_endpoint_querydb, notion_bearer_token, fromD, today)
    # 2. parse information from db to a item object 
    data, data_formatted = format_data(data)
    print(data_formatted)
    # 3. sum
    totalAmount = getExpensesBetweenDays(data_formatted, fromD, today)

    return totalAmount


def handler(event, context):

    config = configparser.ConfigParser()
    config.read('config.cfg')
    msg = ""
    status = 200

    if 'body' in event:
        payload = json.loads(event['body'])
    else:
        payload = event

    month = payload['monthQuery']

    mode = 'local' if  payload['mode'] == 'local' else 'pro' # select mode of execution. Affect to place where read keys
    #notion_endpoint, db_key, notion_bearer_token = getKeys(mode, config)


    if not 'user' in payload:
        return {
        'statusCode': status,
        'body': "LOGIN INFO NOT FOUNG"
    }

    name = payload['user']['name']
    token = payload['user']['token']
    db_key, notion_bearer_token = getUserKeys(name, token)

    notion_endpoint_querydb = "https://api.notion.com/v1/databases/" + db_key + "/query"

    if  db_key != "" or notion_bearer_token != "":


        query = payload['query']

        try:
            # return a full month report in string format
            if query == 'monthReport':
                msg = getMonthReport(month, notion_endpoint_querydb, notion_bearer_token)

            # return the sum of total expenses of the current week
            if query == 'weekExpenses':
                msg = getCurrentWeekExpenses(notion_endpoint_querydb, notion_bearer_token)

        except:
            print("Error proccesing request")
            status = 500

        finally:
            print("Returning", msg)

    return {
        'statusCode': status,
        'body': msg
    }