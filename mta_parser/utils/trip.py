from collections import OrderedDict
# Storing trip related data
# Note : some trips wont have vehicle data
class trip(object):
    def __init__(self, tripId, routeId, startDate):
        self.tripId = tripId
        self.routeId = routeId
        self.startDate = startDate
        dirs = tripId.split(".");
        self.direction = dirs[-1][0]

    def __eq__(self, other):
        return ((self.tripId, self.routeId, self.startDate) ==
                (other.tripId, other.routeId, other.startDate))

    def __hash__(self):
        return hash((self.tripId, self.routeId, self.startDate))        
       


