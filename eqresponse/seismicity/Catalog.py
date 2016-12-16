# ======================================================================
#
#                           Brad T. Aagaard
#                        U.S. Geological Survey
#
# ======================================================================
#

import os
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
class Catalog(object):


    def __init__(self, filename=None):
        self.events = None
        self.filename = filename
        return


    def fetch(self, starttime, endtime, longitude, latitude, maxdist, minmag, catalog):
        datacenter = catalog[0]
        if datacenter == "USGS":
            services = {'station': None,
                        'event': "http://earthquake.usgs.gov/fdsnws/event/1",
                        'dataselect': None}
            client = Client(datacenter, service_mappings=services, debug=False)
        else:
            client = Client(datacenter, debug=False)
        kwds = {}
        if catalog[1] != "":
            kwds = {"catalog": catalog[1]}
        if not self.filename is None:
            kwds['filename'] = self.filename
            
        self.events = client.get_events(
            starttime=starttime, 
            endtime=endtime, 
            longitude=longitude, 
            latitude=latitude, 
            maxradius=maxdist,
            minmagnitude=minmag,
            orderby="time-asc",
            **kwds)
        return


    def load(self):
        if self.events is None:
            if not os.path.isfile(self.filename):
                return
            
            catalog = obspy.core.event.read_events(self.filename, format="QUAKEML")
            catalogF = catalog.filter("magnitude >= -2.0")
            catalogF = obspy.core.event.Catalog(catalogF, description=catalog.description, comments=catalog.comments, creation_info=catalog.creation_info)
            self.events = catalogF
        return


    def addDistanceAzimuth(self, mainshock):
        if self.events is None:
            return
        
        from obspy.core import AttribDict
        ns = "http://earthquake.usgs.gov/xmlns/1.0"
        
        origin = mainshock.preferred_origin()
        utmZone = int(math.floor((origin.longitude+180)/6)+1)
        proj = pyproj.Proj(proj="utm", zone=utmZone, ellps='WGS84')
        x0,y0 = proj(origin.longitude, origin.latitude)

        for event in self.events:
            origin = event.preferred_origin()
            xE,yE = proj(origin.longitude, origin.latitude)
            dx = xE-x0
            dy = yE-y0

            dist = ((xE-x0)**2 + (yE-y0)**2)**0.5                
            distAttrib = AttribDict({'type': "attribute", 'namespace': ns, 'value': dist})

            azimuth = 180.0*math.atan2(dx, dy)/math.pi
            if azimuth < 0.0:
                azimuth += 360.0
            
            azimuthAttrib = AttribDict({'type': "attribute", 'namespace': ns, 'value': azimuth})

            if hasattr(event, 'extra'):
                extraAttrib = event.extra
            else:
                extraAttrib = AttribDict()
                event.extra = extraAttrib
                
            extraAttrib.mainshock_distance = distAttrib
            extraAttrib.mainshock_azimuth = azimuthAttrib

        return
    
    
    def getHypocenterMag(self):

        from matplotlib.dates import date2num
        
        nevents = self.events.count()
        hypocenters = numpy.zeros((nevents, 3), dtype=numpy.float)
        mag = numpy.zeros((nevents,), dtype=numpy.float)
        t = numpy.zeros((nevents,), dtype=numpy.float)
        for i,event in enumerate(self.events):
            origin = event.preferred_origin()
            hypocenters[i,:] = (origin.longitude, origin.latitude, origin.depth)
            t[i] = date2num(origin.time)
            mag[i] = event.preferred_magnitude().mag
        return (hypocenters, mag, t)


    def printSummary(self, mainshock, label, maxdist, detail_minmag=1.0):

        if label == "foreshocks":
            intervals = [HOUR_TO_SECS, DAY_TO_SECS, 7*DAY_TO_SECS]
        else:
            intervals = [DAY_TO_SECS, 7*DAY_TO_SECS, 30*DAY_TO_SECS, YEAR_TO_SECS]
        
        if self.events.count() > 0:
            print("\n%(label)s within %(dist)3.1f km of mainshock epicenter (as of %(date)s)" % {
                'label': label,
                'dist': maxdist,
                'date': self._localTimestamp(self.aftershocks.creation_info.creation_time)})
            if label == "aftershocks":
                duration = self.events[-1].preferred_origin().time - self.mainshock.preferred_origin().time
                print("Current duration of aftershock sequence: %3.1f days\n" % (duration/DAY_TO_SECS))

                self._printTally(self.events, intervals, timing="after_first")
                if duration > DAY_TO_SECS:
                    print("")
                    self._printTally(self.events, intervals, timing="after_recent")

                print("\nMost recent aftershock")
                self._printEvent(self.aftershocks[-1])
            else:
                timespan = self.params['historical']['years']*YEAR_TO_SECS
                self._printTally(self.events, intervals+[timespan], timing="before")

            eventsF = self.events.filter("magnitude >= %3.1f" % detail_minmag)
            print("\n%(label)s M >= %(mag)3.1f" % {'label': label, 'mag': detail_minmag})
            for event in eventsF:
                self._printEvent(event)

        return
                            

    @staticmethod
    def printMainshock(mainshock):
        print("\nMainshock v%s (%s)" % (mainshock.creation_info.version, self._localTimestamp(mainshock.creation_info.creation_time)))
        self._printEvent(self.mainshock)
        return


    
    def _printTally(self, events, tintervals, timing):
        params = self.params['summary']
        maxmag = math.floor(self.mainshock.preferred_magnitude().mag)
        origin = self.mainshock.preferred_origin()
        binsMag = numpy.arange(params['mag_min'], maxmag+0.001, 1.0)[::-1]

        if timing == "before":
            binsTime = numpy.zeros(len(tintervals), dtype=object)
            for i,t in enumerate(tintervals):
                binsTime[i] = origin.time - t
            op = ">="
            tdescription = "Prior"
        elif timing == "after_first":
            binsTime = numpy.zeros(len(tintervals)+1, dtype=object)
            for i,t in enumerate(tintervals):
                if self.now < origin.time + t:
                    binsTime = binsTime[:i+1]
                    break
                else:
                    binsTime[i] = origin.time + t
            binsTime[-1] = self.aftershocks[-1].preferred_origin().time

            op = "<="
            tdescription = "First"
        elif timing == "after_recent":
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
        if timing == "after_first":
            nintervals -= 1
        for tinterval in tintervals[:nintervals]:
            if tinterval/YEAR_TO_SECS < 0.999:
                tlabel = "%s %3.1f days" % (tdescription, tinterval/DAY_TO_SECS)
            else:
                tlabel = "%s %3.1f yrs" % (tdescription, tinterval/YEAR_TO_SECS)
            hline += "%16s" % tlabel
        if timing == "after_first":
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
        print("%s   %8.3f %6.3f %s  %4.1fkm  %4.2f %s" % (self._localTimestamp(origin.time), origin.longitude, origin.latitude, directionStr, 1.0e-3*origin.depth, magnitude.mag, magnitude.magnitude_type))
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
    

    @staticmethod
    def _localTimestamp(self, tstamp):
        if tstamp is None:
            return ""
        tUTC = pytz.utc.localize(tstamp.datetime)
        tL = tUTC.astimezone(self.tz)
        localFmt = "%a %b %d %Y %I:%M:%S %p %Z"
        return tL.strftime(localFmt)


# End of file
