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
import pyproj

import obspy.core.event
from obspy.clients.fdsn import Client
from obspy.core.utcdatetime import UTCDateTime

import obspyutils.momenttensor


KM_TO_DEG = 1.0/111.0 # roughly 111 km per latitude degree
HOUR_TO_SECS = 3600.0
DAY_TO_SECS = 24*HOUR_TO_SECS
YEAR_TO_SECS = 365.25*DAY_TO_SECS

# ----------------------------------------------------------------------
class Summary(object):


    def __init__(self, params, now, tz, mainshock, foreshocks, aftershocks, historical, significant):
        self.params = params
        self.now = now
        self.tz = tz
        self.mainshock = mainshock
        self.foreshocks = foreshocks
        self.aftershocks = aftershocks
        self.historical = historical
        self.significant = significant

        self.foreshocks.addDistanceAzimuth(mainshock)
        self.foreshocks.addDistanceAzimuth(mainshock)
        self.historical.addDistanceAzimuth(mainshock)
        self.significant.addDistanceAzimuth(mainshock)
        return


    def show(self):
        (datacenter, catalog) = self.params.get("catalog")
        if datacenter == "USGS":
            datacenter = "ANSS ComCat"
        print("Source: %s %s catalog" % (datacenter, catalog))

        # Mainshock
        self._printMainshock()

        # Foreshocks
        intervals = [HOUR_TO_SECS, DAY_TO_SECS, 7*DAY_TO_SECS]
        self._printCatalog(self.foreshocks, "Foreshocks", intervals, timing="before_mainshock")

        intervals = [DAY_TO_SECS, 7*DAY_TO_SECS, 30*DAY_TO_SECS, YEAR_TO_SECS]

        # Aftershocks
        if not self.aftershocks.events is None and self.aftershocks.events.count() > 0:
            duration = self.aftershocks.events[-1].preferred_origin().time - mainshock.preferred_origin().time
        else:
            duration = None
        self._printCatalog(self.aftershocks, "Aftershocks", intervals, timing="after_mainshock", duration=duration)
            
        # Historical
        self._printCatalog(self.historical, "Historical", intervals, timing="before_mainshock")

        # Significant
        self._printCatalog(self.significant, "Significant", intervals, timing="before_mainshock")

        return


    def _printCatalog(self, catalog, label, intervals, timing, duration=None):
        if catalog.events is None or catalog.events.count() == 0:
            return

        key = label.lower()
        listMinMag = params.get("summary/%s_list_minmag" % key)
        maxDist = params.get("%s/maxdist_km" % key)
        
        print("\n%(label)s within %(dist)3.1f km of mainshock epicenter (as of %(date)s)" % {
                'label': label,
                'dist': maxdist,
                'date': self._localTimestamp(catalog.events.creation_info.creation_time)})

        if not duration is None:
            print("Current duration of %(label)s sequence: %(duration)3.1f days\n" % {
                'label': label,
                'duration': duration/DAY_TO_SECS})

        self._printTally(catalog.events, intervals, timing="after_mainshock")
        if duration > DAY_TO_SECS:
            print("")
            self._printTally(catalog.events, intervals, timing="before_now")

        print("\nMost recent earthquake")
        self._printEvent(catalog.events[-1])

        eventsF = self.events.filter("magnitude >= %3.1f" % listMinMag)
        print("\n%(label)s M >= %(mag)3.1f" % {'label': label, 'mag': listMinMag})
        for event in eventsF:
            self._printEvent(event)

        return
                            

    def _printMainshock(self):
        print("\nMainshock v%s (%s)" % (self.mainshock.creation_info.version, self._localTimestamp(self.mainshock.creation_info.creation_time)))
        self._printEvent(self.mainshock)
        return


    def _printTally(self, events, tintervals, timing):
        maxmag = math.floor(self.mainshock.preferred_magnitude().mag)
        origin = self.mainshock.preferred_origin()
        binsMag = numpy.arange(1.0, maxmag+0.001, 1.0)[::-1]

        if timing == "before_mainshock":
            binsTime = numpy.zeros(len(tintervals), dtype=object)
            for i,t in enumerate(tintervals):
                binsTime[i] = origin.time - t
            op = ">="
            tdescription = "Prior"
        elif timing == "after_mainshock":
            binsTime = numpy.zeros(len(tintervals)+1, dtype=object)
            for i,t in enumerate(tintervals):
                if self.now < origin.time + t:
                    binsTime = binsTime[:i+1]
                    break
                else:
                    binsTime[i] = origin.time + t
            binsTime[-1] = catalog.events[-1].preferred_origin().time
            op = "<="
            tdescription = "First"
        elif timing == "before_now":
            binsTime = numpy.zeros(len(tintervals), dtype=object)
            for i,t in enumerate(tintervals):
                if self.now-t < origin.time:
                    binsTime = binsTime[:i]
                    break
                else:
                    binsTime[i] = self.now - t
            op = ">="
            tdescription = "Past"

        count = numpy.zeros((binsMag.shape[0], binsTime.shape[0]))
        for irow,binMag in enumerate(binsMag):
            eventsM = events.filter('magnitude >= %3.1f' % binMag)
            for icol,binTime in enumerate(binsTime):
                eventsT = eventsM.filter('time %s %s' % (op, binTime))
                count[irow,icol] = eventsT.count()

        # Heading
        hline = "    "
        nintervals = binsTime.shape[0]
        if timing == "after_mainshock":
            nintervals -= 1
        for tinterval in tintervals[:nintervals]:
            if tinterval/YEAR_TO_SECS < 0.999:
                tlabel = "%s %3.1f days" % (tdescription, tinterval/DAY_TO_SECS)
            else:
                tlabel = "%s %3.1f yrs" % (tdescription, tinterval/YEAR_TO_SECS)
            hline += "%16s" % tlabel
        if timing == "after_mainshock":
            tlabel = "Total"
            hline += "%16s" % tlabel
        print(hline)
        for irow,binMag in enumerate(binsMag):
            line = "M>=%1.0f" % binMag
            for icol,binTime in enumerate(binsTime):
                line += "%16d" % count[irow,icol]
            print(line)
        return

    
    def _printEvent(self, event):

        magnitude = event.preferred_magnitude()
        origin = event.preferred_origin()
        if hasattr(event, 'extra') and hasattr(event.extra, 'mainshock_distance'):
            mainshockDist = 1.0e-3*event.extra.mainshock_distance.value
            mainshockAzimuth = event.extra.mainshock_azimuth.value
            directionStr = "(%4.1fkm %s)" % (mainshockDist, self._azimuthToString(mainshockAzimuth))
        else:
            directionStr = "            "
        print("%(tstamp)s   %(lon)8.3f %(lat)6.3f %(dir)s  %(depth)4.1fkm  %(mag)4.2f %(magtype)s" % {
            'tstamp': self._localTimestamp(origin.time),
            'lon': origin.longitude,
            'lat': origin.latitude,
            'dir': directionStr,
            'depth': 1.0e-3*origin.depth,
            'mag': magnitude.mag,
            'magtype': magnitude.magnitude_type})
        return


    def _azimuthToString(self, azimuth):
        lookup = {0: "N ",
                  1: "NE",
                  2: "E ",
                  3: "SE",
                  4: "S ",
                  5: "SW",
                  6: "W ",
                  7: "NW",
                  8: "N ",
                  }
        ilookup = int((azimuth+22.5)/45.0)
        return lookup[ilookup]
    

    def _localTimestamp(self, tstamp):
        if tstamp is None:
            return ""
        tUTC = pytz.utc.localize(tstamp.datetime)
        tL = tUTC.astimezone(self.tz)
        localFmt = "%a %b %d %Y %I:%M:%S %p %Z"
        return tL.strftime(localFmt)


# End of file
