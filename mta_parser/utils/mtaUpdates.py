import urllib2,contextlib
from datetime import datetime
from collections import OrderedDict

from pytz import timezone
import gtfs_realtime_pb2
import google.protobuf

import vehicle, alert, tripupdate, trip

class mtaUpdates(object):
    # Do not change Timezone
    TIMEZONE = timezone('America/New_York')

    # feed url depends on the routes to which you want updates
    # here we are using feed 1 , which has lines 1,2,3,4,5,6,S
    # While initializing we can read the API Key and add it to the url
    feedurl = 'http://datamine.mta.info/mta_esi.php?feed_id=1&key='

    VCS = {1:"INCOMING_AT", 2:"STOPPED_AT", 3:"IN_TRANSIT_TO"}
    def __init__(self,apikey):
        self.feedurl = self.feedurl + apikey
        self.database = OrderedDict()
        self.myAlerts = []
        #self.myVehicles = []
        self.timestmap = 0

    # Method to get trip updates from mta real time feed
    def getTripUpdates(self):
        feed = gtfs_realtime_pb2.FeedMessage()
        try:
            with contextlib.closing(urllib2.urlopen(self.feedurl)) as response:
                d = feed.ParseFromString(response.read())
        except (urllib2.URLError, google.protobuf.message.DecodeError) as e:
            print "Error while connecting to mta server " +str(e)


        self.timestamp = feed.header.timestamp
        nytime = datetime.fromtimestamp(self.timestamp,self.TIMEZONE)

        for entity in feed.entity:
            # Trip update represents a change in timetable
            if entity.trip_update and entity.trip_update.trip.trip_id:
                    trip_update = entity.trip_update
                    mytrip = trip.trip(trip_update.trip.trip_id,
                                       trip_update.trip.route_id,
                                       trip_update.trip.start_date)
                    mytripupdate = tripupdate.tripupdate(trip_update.vehicle,
                                                   trip_update.stop_time_update)

                    if mytrip not in self.database:
                        self.database[mytrip] = [None, None]
                    item = self.database[mytrip]
                    item[0] = mytripupdate
            if entity.vehicle and entity.vehicle.trip.trip_id:
                v = entity.vehicle
                mytrip = trip.trip(v.trip.trip_id,
                                       v.trip.route_id,
                                       v.trip.start_date)

                myVehicle = vehicle.vehicle(v.current_stop_sequence,
                                            v.stop_id,
                                            v.timestamp,
                                            v.current_status)
                if mytrip not in self.database:
                    self.database[mytrip] = [None, None]
                item = self.database[mytrip]
                item[1] = myVehicle
            if entity.HasField('alert'):
                a = entity.alert
                myalert = alert.alert(a.header_text, a.informed_entity)
                self.myAlerts.append(myalert)

    # END OF getTripUpdates method
def get_key(key):
    with open(key, 'rb') as keyfile:
        APIKEY = keyfile.read().rstrip('\n')
    return APIKEY

def main_loop():
    mta = mtaUpdates(get_key("../key.txt"))
    mta.getTripUpdates()

    print(mta.timestamp)
    for k, v in mta.database.items():
        print("trip", k.tripId)
        for k_update, v_update in v[0].futureStops.items():
            print("<stop_time_update>id:%s, time:%s" % (k_update, v_update))
        if v[1]:
            print("<vehicle>stopNum:%s, stopId:%s, timestamp:%s, status:%s" %
                 (v[1].currentStopNumber, v[1].currentStopId, v[1].timestamp, v[1].currentStatus))


if __name__ == "__main__":
    main_loop()
