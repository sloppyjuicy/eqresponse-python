# ======================================================================
#
#                           Brad T. Aagaard
#                        U.S. Geological Survey
#
# ======================================================================
#


from obspy.clients.fdsn import Client
from obspy.core.utcdatetime import UTCDateTime

from eqresponse.seismicity.Catalog import Catalog

import re

KM_TO_DEG = 1.0/111.0 # roughly 111 km per latitude degree

# ----------------------------------------------------------------------
class IdentifyApp(object):
    """Application for quickly listing earthquakes near a location over a
    specific time period.

    """

    def __init__(self, showProgress=True):
        self.showProgress = showProgress

        return


    def run(self, starttime, endtime, longitude, latitude, distkm, minmag, datacenter):
        if self.showProgress:
            print("Fetching earthquake information from data center...")

        (datacenterName, datacenterCatalog) = datacenter.split("/")

        catalog = Catalog()
        catalog.fetch(
            starttime=UTCDateTime(starttime), 
            endtime=UTCDateTime(endtime),
            longitude=longitude,
            latitude=latitude,
            maxdist=distkm*KM_TO_DEG,
            minmag=minmag,
            catalog=(datacenterName, datacenterCatalog)
        )

        print("Earthquakes M>=%3.1f:" % minmag)
        for event in catalog.events:
            self._printEvent(event)
        return

    
    def _printEvent(self, event):
        """
        """
        magnitude = event.preferred_magnitude()
        origin = event.preferred_origin()
        evstr = event.resource_id.id
        eventid = re.search("eventid=([A-Za-z]*[0-9]+)", evstr).groups()[0]
        print("%(tstamp)s   %(lon)8.3f %(lat)6.3f %(depth)4.1fkm  %(mag)4.2f %(magtype)s  %(evid)s" % {
            'tstamp': origin.time,
            'lon': origin.longitude,
            'lat': origin.latitude,
            'depth': 1.0e-3*origin.depth,
            'mag': magnitude.mag,
            'magtype': magnitude.magnitude_type,
            'evid': eventid})
        return


# End of file
