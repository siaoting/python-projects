from collections import OrderedDict
#import trip
# Storing trip related data
# Note : some trips wont have vehicle data
class tripupdate(object):
    def __init__(self, vehicleData, stops):
        #self.trip = trip.trip(tripId, routeId, startDate)
        self.vehicleData = vehicleData
        self.futureStops = OrderedDict() # Format {stopId : [arrivalTime,departureTime]}
        for stop in stops:
            self.futureStops[stop.stop_id] = (stop.arrival.time, stop.departure.time)
        #print(self.futureStops)
        
       


