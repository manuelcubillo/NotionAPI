"""
function to manage different users
"""
import boto3
import os
import json


@dataclass
class User:
    name : str = ""
    authToken : str = ""
    notionAuth : str = ""
    dbID : str = ""
    countReqs : int = 0
    allowed : bool = False
    notionEndPoint : str = ""

    def checkAuth(self, tkn):
        return self.authToken == tkn

    def isAllowed(self): 
        return self.allowed


def getUser(name):
    """
    get the data user from db and return a user object
    """

    dynamodb = boto3.resource('dynamodb')
    usr = User()

    try:
        # todo check if exits and fetch data from aws
        usersTable = dynamodb.Table(os.environ.get('NOTION_USERS_TABLE_NAME'))
        dynamoResponse = usersTable.get_item(Key={'name': name})
        if not 'Item' in dynamoResponse:
                print('ERROR: No user found', name)
                return usr
        
        print(json.dumps(dynamoResponse))
        response = dynamoResponse['Item']
        usr = createUsrFromDB(response)   

    except:
        print("A problem fetching user data from cloud occurs")

    return usr

def createUsrFromDB(respone):
    usr = User()
    usr.name = usr['name']
    usr.authToken = usr['authToken']
    usr.dbID = usr['dbID']
    usr.allowed = usr['allowed']
    usr.notionEndPoint = usr['notionEndPoint']
    usr.notionAuth = usr['notionAuth']
    usr.countReqs = usr['countReqs']
    return usr


def updateUser(user):
    #todo upload / modify user
    try:
        dynamodb = boto3.resource('dynamodb')
        usersTable = dynamodb.Table(os.environ.get('NOTION_USERS_TABLE_NAME'))
        usersTable.put_item(Item = user)
    except:
        print("ERROR: error updating data base")
        print(user)

    return

def getUserKeys(name, token):
    """
    function that calls the rest of the apis to access
    this function check and validate the user
    if user is right, database id and notion auth is return, otherwise an exception will occurs
    """
    notionToken, notionEndPoint, dbId = "", "", ""

    usr = getUser(name)

    if usr.isAllowed and usr.checkAuth(token):
        notionToken = usr.notionAuth
        notionEndPoint = usr.notionEndPoint
        dbId = usr.dbID
        usr.countReqs = usr.countReqs + 1
        updateUser(usr) # update counter request
    else:
        print("The user", name, "with token", token, "is not allowed to use the API. Wrong password or access denied.")


    return notionEndPoint, dbId, notionToken