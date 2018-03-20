import trip
# Storing alerts from the feed
class alert(object):
    def __init__(self, texts, informed_entities):
        self.alertMessage = []
        for text in texts.translation:
            self.alertMessage.append(text)
        self.trip = []
        if informed_entities:
            #print(informed_entities)
            for entity in informed_entities:
                if entity.HasField('trip'):
                    t = entity.trip
                    self.trip.append(
                        trip.trip(t.trip_id, t.route_id, t.start_date))
