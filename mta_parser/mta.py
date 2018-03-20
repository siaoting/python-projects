import json,time,csv,sys
import re
from threading import Thread

import boto3
from boto3.dynamodb.conditions import Key,Attr
sys.path.append('../utils')
import dynamodata as dynamo
import aws, dynamoParser

DYNAMODB_TABLE_NAME = "mtaData"
STAY = "STAY"
# prompt
def prompt():
    print("")
    print(">Available Commands are : ")
    print("1. plan trip")
    print("2. subscribe to message feed")
    print("3. exit")

def buildStationssDB():
    stations = []
    with open('stops.csv', 'rb') as f:
        reader = csv.reader(f)
        for row in reader:
            stations.append(row[0])
    return stations

def subscribe(client, phoneNumber):
    #Validate the phone number is well formated
    rule = re.compile(r"^\+[0-9]{11}")
    if not(rule.match(phoneNumber)):
        msg = u"Your phone is not well formated: +16462489277 for instance."
        #raise ValueError(msg)
        return False

    # Create the topic and subscription if it doesn't exist (first subscriber)
    topic = client.create_topic(Name="notifications")
    welcomeMessage = "Welcome to the MTA subscription"
    topic_arn = topic['TopicArn']  # get its Amazon Resource Name
    client.subscribe(
        TopicArn=topic_arn,
        Protocol='sms',
        Endpoint=phoneNumber
    )

    #Send a welcome message
    client.publish(Message=welcomeMessage, PhoneNumber=phoneNumber)
    return True

def publishInfo(client, nums, emails, message):
  # Create the topic if it doesn't exist (this is idempotent)
    topic = client.create_topic(Name="notifications")
    topic_arn = topic['TopicArn']  # get its Amazon Resource Name
    
    client.publish(Message=message, TopicArn=topic_arn)

def refreshTable():
    dynamoTable = dynamo.DynamoDB()
    dynamoTable = dynamoTable.dynamoViewAll()

    return dynamoTable

def passThrough96(mtaDic, routeId):
    #1) Get a list of local trains (ie, 1 trains) passing through the 96th station. Print the trip IDs.
    res = []
    for k, v in mtaDic.items():
        if k.routeId == routeId:
            if '120S' in v[0].futureStops:
                res.append(k.tripId)
    return res

def task1(mtaDic):
    res = passThrough96(mtaDic, '1')
    print("1. The 1 Train pass through 96st is ", res)

def task2(mtaDic):
    res = passThrough96(mtaDic, '2')
    res += passThrough96(mtaDic, '3')
    print("2. The is 2 and 3 Train pass through 96st is ", res)

def earilerTrain(startTime, mtaDic, routeId, startStop, endStop):
    if startStop == endStop:
        return (STAY, 0, 0)
    minSrcTime = float('inf')
    minDstTime = None
    tripId = None
    for k, v in mtaDic.items():
        if k.routeId == routeId:
            if startStop in v[0].futureStops and endStop in v[0].futureStops:
                curTime = int(v[0].futureStops[startStop][0])
                #print(tripId, startTime, curTime, int(v[0].futureStops[endStop][0]))
                if startTime <= curTime < minSrcTime:
                    minSrcTime = curTime
                    #destination arrival time = v[0].futureStops[endStop]
                    minDstTime = int(v[0].futureStops[endStop][0])
                    tripId = k.tripId
                    #print("(%s)From %s to %s" % (routeId, startStop, endStop))
                    #print(tripId, startTime, minSrcTime, minDstTime)
    return (tripId, minSrcTime, minDstTime)

def earilerTrainFrom96to42(startTime, mtaDic, routeId):
    return earilerTrain(startTime, mtaDic, routeId, '120S', '127S')

def task34567(mtaDic, snsClient):
    res1 = earilerTrainFrom96to42(0, mtaDic, '1')
    print("3. The earliest 1 train reaching the 96th is ", res1[0])
    print("5. The time spend on train is ", res1[2] - res1[1])
    res2 = earilerTrainFrom96to42(0, mtaDic, '2')
    res3 = earilerTrainFrom96to42(0, mtaDic, '3')
    if res2[1] < res3[1]:
        res23 = res2
    else:
        res23 = res3
    print("4. The earliest 2 or 3 train reaching the 96th is ", res23[0])
    print("5. The time spend on train is ", res23[2] - res23[1])
    
    if res23[2] > res1[2]:
        message = "Stay on the Local Train"
    else:
        message = "Switch to Express Train"
    print("6a. #####From 96st to 42st")
    print("6a. Choosing 1 train, you will arrive at %d. Choosing 2 or 3 train, you will arrive at %d" % (res1[2], res23[2]))
    print("6a. Suggestion: " + message)
    emails = ['sw3092@columbia.edu']
    nums = []
    publishInfo(snsClient, nums, emails, message)

def processPlanTripCmd(stations):
    sys.stdout.write(">Enter source : ")
    sourceStop = sys.stdin.readline().strip()
    if sourceStop not in stations:
        sys.stdout.write(">Invalid stop id. Enter a valid stop id")
        sys.stdout.flush()
        return (False, None, None, None)

    sys.stdout.write(">Enter destination : ")
    destinationStop = sys.stdin.readline().strip()
    if destinationStop not in stations:
        sys.stdout.write(">Invalid stop id. Enter a valid stop id")
        sys.stdout.flush()
        return (False, None, None, None)

    sys.stdout.write(">Type N for uptown, S for downtown: ")
    direction = sys.stdin.readline().strip()

    # Validate direction
    if direction not in ['N','S']:
        sys.stdout.write(">Invalid direction. Enter a valid direction")
        sys.stdout.flush()
        return (False, None, None, None)

    if direction not in destinationStop or direction not in sourceStop:
        sys.stdout.write(">Direction does not match source and destination stop id")
        sys.stdout.flush()
        return (False, None, None, None)

    return (True, sourceStop, destinationStop, direction)

def planTrip(mtaDic, srcStop, dstStop, direction):
    #(tripId, minSrcTime, minDstTime)
    res1 = earilerTrain(0, mtaDic, '1', srcStop, dstStop)

    #A->96, 96->42, 42->B
    #A->42, 42->96, 96->B
    while True:
        #1. A->96
        dirEndStop = '120S' if direction == 'S' else '127N'
        resExp = earilerTrain(0, mtaDic, '1', srcStop, dirEndStop)
        if not resExp[0]:
            break
        #2.96->42
        dirStartStop = '120S' if direction == 'S' else '127N'
        dirEndStop = '127S' if direction == 'S' else '120N'
        res2 = earilerTrain(resExp[2], mtaDic, '2', dirStartStop, dirEndStop)
        res3 = earilerTrain(resExp[2], mtaDic, '3', dirStartStop, dirEndStop)
        if not res2[0] and not res3[0]:
            resExp = res2    
            break;
        elif not res2[0]:
            resExp = res3
        elif not res3[0]:
            resExp = res2
        else:
            if res2[1] < res3[1]:
                resExp = res2
            else:
                resExp = res3
        #3.42->B
        dirStartStop = '127S' if direction == 'S' else '120N'
        if dstStop != dirStartStop:
            resExp = earilerTrain(resExp[2], mtaDic, '1', dirStartStop, dstStop)
        break
    print("8. #####From %s to %s" % (srcStop, dstStop))
    if not res1[2] and not resExp[2]:
        message = "8. No route"
    if not resExp[2]:
        message = "8. No express route. Stay on the Local Train"
    elif not res1[2]:
        message = "8. No local route. Switch to Express Train"
    else:
        print("8. Choosing 1 train, you will arrive at %d. Choosing 2 or 3 train, you will arrive at %d" % (res1[2], resExp[2]))
        if resExp[2] > res1[2]:
            message = "Stay on the Local Train"
        else:
            message = "Switch to Express Train"
        
    print("8. Suggestion: " + message)

def main():
    dynamodb = aws.getResource('dynamodb','us-east-1')
    snsClient = aws.getClient('sns','us-east-1')
    snsResource = aws.getResource('sns','us-east-1')
    mtaData = refreshTable()
    mtaDic = dynamoParser.dynamoParser().dynamoTomta(mtaData)
    '''for k, v in mtaDic.items():
        #print("trip", k.tripId)
        for k_update, v_update in v[0].futureStops.items():
            if k.routeId == '2' and k_update == '120S':
                print("trip", k.tripId)
                print("<futureStops>id:%s, time:%s" % (k_update, v_update))
        #if v[1]:
        #    print("<vehicle>stopId:%s, timestamp:%s, status:%s" %
        #         (v[1].currentStopId, v[1].timestamp, v[1].currentStatus))
    '''
    # Get list of all stopIds
    stations = buildStationssDB()

    while True:
        prompt()
        sys.stdout.write(">select a command : ")
        userIn = sys.stdin.readline().strip()
        if len(userIn) < 1 :
            print("Command not recognized")
        else:
            if userIn == '1':
                success, sourceStop, destinationStop, direction = processPlanTripCmd(stations)
                if not success:
                    continue
                task1(mtaDic)
                task2(mtaDic)
                task34567(mtaDic, snsClient)
                planTrip(mtaDic, sourceStop, destinationStop, direction);
            elif userIn == '2':
                sys.stdout.write(">Enter phonenumber : ")
                phoneNumber = sys.stdin.readline().strip()
                #  Add a user's phone number to MTA subscription service.
                subscribe(snsClient, phoneNumber)

            else:
                sys.exit()

        # check how if there are any 2 or
if __name__ == "__main__":
    main()
