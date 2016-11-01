# ======================================================================
#
#                           Brad T. Aagaard
#                        U.S. Geological Survey
#
# ======================================================================
#

import numpy
import pytz
import datetime
import math

from obspy.core.utcdatetime import UTCDateTime

# ----------------------------------------------------------------------
class SummarySequences(object):


    def __init__(self, params, now, tz):
        self.params = params
        self.now = now
        self.tz = tz
        return


    def show(self, background, sequences):
        (datacenter, catalog) = self.params.get("catalog")
        if datacenter == "USGS":
            datacenter = "ANSS ComCat"
        print("Source: %s %s catalog" % (datacenter, catalog))

        print("Seismicity within %(dist)3.1f km of %(lon)8.3f %(lat)7.3f (as of %(date)s)." % {
            'dist': self.params.get("background/maxdist_km"),
            'lon': self.params.get("background/longitude"),
            'lat': self.params.get("background/latitude"),
            'date': self._localTimestamp(background.events.creation_info.creation_time),
        })

        # Background
        self._printCatalog(background, "Background")

        # Sequences
        for sequence in sequences:
            self._printCatalog(sequence, sequence.params['label'])

        return


    def _printCatalog(self, catalog, label):
        if catalog.events is None or catalog.events.count() == 0:
            return

        listMinMag = self.params.get("summary/list_minmag")
        
        print("\n%(label)s M >= %(minmag)3.1f, %(start)s to %(end)s" % {
            'label': label,
            'minmag': catalog.params['minmag'],
            'start': self._localTimestamp(UTCDateTime(catalog.params['start'])),
            'end': self._localTimestamp(UTCDateTime(catalog.params['end'])),
        })

        self._printTally(catalog.events, minmag=math.floor(catalog.params['minmag']))

        eventsF = catalog.events.filter("magnitude >= %3.1f" % listMinMag)
        print("\nM >= %3.1f" % listMinMag)
        for event in eventsF:
            self._printEvent(event)

        return
                            

    def _printTally(self, events, minmag=1.0):
        maxmag = 0.0
        for event in events:
            mag = event.preferred_magnitude().mag
            if mag > maxmag:
                maxmag = mag
        maxmag = math.floor(maxmag)
        binsMag = numpy.arange(minmag, maxmag+0.001, 1.0)[::-1]

        count = numpy.zeros((binsMag.shape[0],))
        for irow,binMag in enumerate(binsMag):
            eventsM = events.filter('magnitude >= %3.1f' % binMag)
            count[irow] = eventsM.count()

        # Heading
        hline = "    "
        print(hline)
        for irow,binMag in enumerate(binsMag):
            line = "M>=%1.0f" % binMag
            line += "%16d" % count[irow]
            print(line)
        return

    
    def _printEvent(self, event):

        magnitude = event.preferred_magnitude()
        origin = event.preferred_origin()
        print("%(tstamp)-32s   %(lon)8.3f %(lat)6.3f %(depth)4.1fkm  %(mag)4.2f %(magtype)s" % {
            'tstamp': self._localTimestamp(origin.time),
            'lon': origin.longitude,
            'lat': origin.latitude,
            'depth': 1.0e-3*origin.depth,
            'mag': magnitude.mag,
            'magtype': magnitude.magnitude_type})
        return


    def _localTimestamp(self, tstamp):
        if tstamp is None:
            return ""
        tUTC = pytz.utc.localize(tstamp.datetime)
        tL = tUTC.astimezone(self.tz)
        localFmt = "%a %b %d %Y %I:%M:%S %p %Z"
        return tL.strftime(localFmt)


# End of file
