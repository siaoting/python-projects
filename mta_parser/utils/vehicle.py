#import trip
# Storing vehicle related data
class vehicle(object):
    def __init__(self, stopNumber, stopId, timestamp, status):
        #self.trip = trip.trip(tripId, routeId, startDate)
        self.currentStopNumber = stopNumber
        self.currentStopId = stopId
        self.timestamp = timestamp
        if status == 0:
            status = "INCOMING_AT"
        elif status == 1:
            status = "STOPPED_AT"
        elif status == 2:
            status = "IN_TRANSIT_TO"
        self.currentStatus = status
    
