import cgi
import urllib
import json
from datetime import datetime
from google.appengine.api import users
from google.appengine.ext import ndb

import webapp2


DEFAULT_RECEPTIONSTORE_NAME = 'default_receptionstore'

# We set a parent key on the 'Receptions' to ensure that they are all
# in the same entity group. Queries across the single entity group
# will be consistent.  However, the write rate should be limited to
# ~1/second.

def receptionstore_key(receptionstore_name=DEFAULT_RECEPTIONSTORE_NAME):
    """Constructs a Datastore key for a Receptionstore entity.

    We use receptionstore_name as the key.
    """
    return ndb.Key('Receptionstore', receptionstore_name)


class Reception(ndb.Model):
    """A main model for representing an individual Receptionstore entry."""

    #author = ndb.StructuredProperty(Author)
    # content = ndb.StringProperty(indexed=False)
    latitude = ndb.FloatProperty(indexed=False)
    longitude = ndb.FloatProperty(indexed=False)

    serviceProvider = ndb.StringProperty()
    serviceType = ndb.StringProperty()
    signalStrength = ndb.IntegerProperty()

    make = ndb.StringProperty()
    model = ndb.StringProperty()
    timestamp = ndb.DateTimeProperty()
    uploadDate = ndb.DateTimeProperty(auto_now_add=True)
    def toDictionary(self):
        latitude = str(self.latitude)
        longitude = str(self.longitude)
        serviceProvider = str(self.serviceProvider)
        serviceType = str(self.serviceType)
        signalStrength = str(self.signalStrength)
        make = str(self.make)
        model = str(self.model)
        timestamp = str(self.timestamp)
        uploadDate = str(self.uploadDate)
        dictionary = {'Latitude':latitude,'Longitude':longitude,'Service Provider':serviceProvider,'Service Type':serviceType,'Signal Strength':signalStrength,'Make':make,'Model':model,'Timestamp':timestamp,'Upload Date':uploadDate}
        return dictionary
    def toString(self):
        dict = self.toDictionary()
        return dict.__str__()




class MainPage(webapp2.RequestHandler):
    def get(self):
        receptionstore_name = self.request.get('receptionstore_name',
                                          DEFAULT_RECEPTIONSTORE_NAME)

        # Ancestor Queries, as shown here, are strongly consistent
        # with the High Replication Datastore. Queries that span
        # entity groups are eventually consistent. If we omitted the
        # ancestor from this query there would be a slight chance that
        # Reception that had just been written would not show up in a
        # query.
        receptions_query = Reception.query(
            ancestor=receptionstore_key(receptionstore_name)).order(-Reception.timestamp)
        receptions = receptions_query.fetch()
        receptionsList = []
        for reception in receptions:
            receptionsList.append(reception.toDictionary())

        data = {'receptions':receptionsList}
        receptionsJsonResponse = json.dumps(data,separators=(',',':'),indent=1)
        self.response.write(receptionsJsonResponse)


class UploadHandler(webapp2.RequestHandler):
    def post(self):
        # We set the same parent key on the 'Reception' to ensure each
        # Reception is in the same entity group. Queries across the
        # single entity group will be consistent. However, the write
        # rate to a single entity group should be limited to
        # ~1/second.

        lat = self.request.get('latitude')
        long = self.request.get('longitude')
        serviceProvider = self.request.get('service_provider')
        serviceType = self.request.get('service_type')
        signalStrength = self.request.get('signal_strength')
        make = self.request.get('make')
        model = self.request.get('model')
        timestamp = self.request.get('timestamp')

        atts = [lat,long,serviceProvider,serviceType,signalStrength,make,timestamp]
        if(atts.__contains__('')):
            missingAttributes = ''
            if lat == '':
                missingAttributes += 'latitude, '
            if long == '':
                missingAttributes += 'long, '
            if serviceProvider == '':
                missingAttributes += 'serviceProvider, '
            if serviceType == '':
                missingAttributes += 'serviceType, '
            if signalStrength == '':
                missingAttributes += 'signalStrength, '
            if make == '':
                missingAttributes += 'make, '
            if model == '':
                missingAttributes += 'model, '
            if timestamp == '':
                missingAttributes += 'timestamp'

            missingAttributes = missingAttributes.rstrip(", ")
            response = 'Reception not saved due to an error, Missing attributes: ' + missingAttributes
            self.response.write(response)
        else:
            receptionstore_name = self.request.get('receptionstore_name',DEFAULT_RECEPTIONSTORE_NAME)
            reception = Reception(parent=receptionstore_key(receptionstore_name))
            datetimeFormat = '%Y-%m-%d %H:%M:%S.%f'
            try:
                reception.latitude = float(lat)
                reception.longitude = float(long)
                reception.serviceProvider = unicode(serviceProvider)
                reception.serviceType = unicode(serviceType)
                reception.signalStrength = int(signalStrength)
                reception.make = unicode(make)
                reception.model = unicode(model)
                reception.timestamp = datetime.strptime(timestamp,datetimeFormat)

                reception.put()
                self.response.write("Reception saved successfully: " + reception.toString())
            except(ValueError):
                self.response.write('Exception Raised: Value Error')
            except(TypeError): #This is not raised ever during testing but writing to be on safe side coz who knows what might happen
                self.response.write('Exception Raised: Type Error')


application = webapp2.WSGIApplication([
    ('/', MainPage), #MainPage will return all data from datastore
    ('/upload', UploadHandler),#Guestbook(UploadHandler will extract contents
                          #and put into datastore
], debug=False)
