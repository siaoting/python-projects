from collections import OrderedDict
import vehicle, alert, tripupdate, trip
import json

class tmpTime():
    def __init__(self, time):
        self.time = time

class tmpStop():
    def __init__(self, stop_id, arrival, departure):
        self.stop_id = stop_id
        self.arrival = tmpTime(arrival)
        self.departure = tmpTime(departure)

class dynamoParser():
    #def __init__():
    def dynamoTomta(self, items):
        mtaData = OrderedDict()
        for item in items:
            mytrip = trip.trip(item['tripId'], item['routeId'], item['startDate'])
            dynamostops = item['futureStopData']
            mystop = []
            for dynamostop in dynamostops:
                for k, v in dynamostop.items():
                    stop = tmpStop(k, v[0]['arrivaltime'], v[1]['departuretime'])
                mystop.append(stop)
            mytripupdate = tripupdate.tripupdate(None, mystop)
            myVehicle = vehicle.vehicle(0,
                            item["currentStopId"],
                            item["vehicleTimeStamp"],
                            item["currentStopStatus"])
            mtaData[mytrip] = [mytripupdate, myVehicle]
        return mtaData
