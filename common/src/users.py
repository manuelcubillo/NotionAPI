"""
function to manage different users
"""
import boto3
import os
import json
from dataclasses import dataclass
from boto3.dynamodb.conditions import Key, Attr


@dataclass
class User:
    name : str = ""
    authToken : str = ""
    notionAuth : str = ""
    dbID : str = ""
    countReqs : int = 0
    allowed : bool = False

    def checkAuth(self, tkn):
        return self.authToken == tkn

    def isAllowed(self): 
        return self.allowed


def getUser(name):
    """
    get the data user from db and return a user object
    """
    usr = User()

    try:

        dynamodb = boto3.resource('dynamodb')

        # todo check if exits and fetch data from aws
        print("Trying to get", name, "from", os.environ.get('NOTION_USERS_TABLE_NAME'))

        usersTable = dynamodb.Table(os.environ.get('NOTION_USERS_TABLE_NAME')) # type: ignore
        if usersTable == None:
            print("Not table DB found", os.environ.get('NOTION_USERS_TABLE_NAME'))

        dynamoResponse = usersTable.get_item(Key={'name': name})
        if not 'Item' in dynamoResponse:
                print('ERROR: No user found', name)
                return usr
        
        print("dynamoDB answer",dynamoResponse)
        #print(json.dumps(dynamoResponse))
        response = dynamoResponse['Item']
        usr = createUsrFromDB(response)   

    except Exception as err:
        print("A problem fetching user data from cloud occurs")
        print(err)

    return usr

def createUsrFromDB(respone):
    usr = User()
    usr.name = respone['name']
    usr.authToken = respone['authToken']
    usr.dbID = respone['dbID']
    usr.allowed = respone['allowed']
    usr.notionAuth = respone['notionAuth']
    usr.countReqs = respone['countReqs']
    return usr


def updateUser(user):
    try:
        dynamodb = boto3.resource('dynamodb')
        usersTable = dynamodb.Table(os.environ.get('NOTION_USERS_TABLE_NAME')) # type: ignore
        usersTable.put_item(Item = user)
    except:
        print("ERROR: error updating data base")
        print(user)

    return

def getUserKeys(name, token, updateCounter = True):
    """
    function that calls the rest of the apis to access
    this function check and validate the user
    if user is right, database id and notion auth is return, otherwise an exception will occurs
    """
    notionToken, dbId = "", ""

    usr = getUser(name)

    if usr.isAllowed and usr.checkAuth(token):
        notionToken = usr.notionAuth
        dbId = usr.dbID
        if updateCounter:
            usr.countReqs = usr.countReqs + 1
            updateUser(usr) # update counter request
    else:
        print("The user", name, "with token", token, "is not allowed to use the API. Wrong password or access denied.")


    return dbId, notionToken