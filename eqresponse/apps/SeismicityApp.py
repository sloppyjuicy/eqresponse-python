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

from obspy.clients.fdsn import Client
from obspy.core.utcdatetime import UTCDateTime

from eqresponse.seismicity.Catalog import Catalog
from eqresponse.seismicity.Summary import Summary
from eqresponse.core.Parameters import Parameters

KM_TO_DEG = 1.0/111.0 # roughly 111 km per latitude degree
DAY_TO_SECS = 24*3600.0
YEAR_TO_SECS = 365.25*DAY_TO_SECS

# ----------------------------------------------------------------------
class SeismicityApp(object):
    """
    Application for gathering and displaying seismicity information
    related to a mainshock.
    """

    def __init__(self, showProgress=True):
        self.showProgress = showProgress

        self.params = None
        self.tz = None
        self.now = None

        # Default values of None mean the parameter is based on mainshock values (magnitude).
        self.defaults = {
            "title": "YEAR MAGNITUDE LOCATION Earthquake",
            "catalog": ["USGS", ""],
            "time_zone": "US/Pacific",
            "fault_azimuth": 143.0,
            "qfaults_region": "sf",
            "foreshocks": {
                "maxdist_km": 5.0,
                "minmag": 1.0,
                "days": 7.0,
            },
            "aftershocks": {
                "maxdist_km": 10.0,
                "minmag": 0.0,
            },
            "significant": {
                "maxdist_km": 20.0,
                "years": 30.0,
                "minmag": 4.0,
            },
            "historical": {
                "maxdist_km": 20.0,
                "years": 10.0,
                "minmag": 2.0,
            },
            'summary': {
                "mag_min": 4.0,
                "foreshocks_list_minmag": 1.0,
                "aftershocks_list_minmag": 3.0,
                "historical_list_minmag": 3.0,
                "significant_list_minmag": 4.0,
            },
            'plot_map': {
                "width_pixels": 1200,
                "height_pixels": 1200,
                "zoom_level": None,
                "height_km": None,
                "marker_scale": 0.05
            },
            'plot_time': {
                'width': 8.0,
                'height': 6.0,
                'color': 'blue',
                'color_edge': 'fg',
                'marker_scale': 0.08,
                },
            'plot_freqmag': {
                'width': 5.0,
                'height': 5.0,
                },
            'plot_xsections': {
                'width': 5.0,
                'height': 5.0,
                'marker_scale': 40.0,
                },
            'files': {
                'mainshock': "mainshock.xml",
                'foreshocks': "foreshocks.xml",
                'aftershocks': "aftershocks.xml",
                'historical': "historical.xml",
                'significant': "significant.xml",
                },
        }
        return


    def initialize(self):
        self.mainshock = Catalog(self.params.get("files/mainshock"))
        self.foreshocks = Catalog(self.params.get("files/foreshocks"))
        self.aftershocks = Catalog(self.params.get("files/aftershocks"))
        self.historical = Catalog(self.params.get("files/historical"))
        self.significant = Catalog(self.params.get("files/significant"))
        return

    
    def _setDynamicDefaults(self):
        mag = self.mainshock.events[0].preferred_magnitude().mag

        self.params.setDefault("foreshocks/maxdist_km", self.params.maxRounded(5.0, (0.5+mag-2)*5.0, 5.0))
        self.params.setDefault("aftershocks/maxdist_km", self.params.maxRounded(5.0, (0.5+mag-2)*5.0, 5.0))

        self.params.setDefault("historical/maxdist_km", self.params.maxRounded(10.0, (0.5+mag-2)*10.0, 10.0))
        self.params.setDefault("historical/minmag", self.params.maxRounded(2.0, mag-2, 0.5))

        self.params.setDefault("significant/maxdist_km", self.params.maxRounded(50.0, 2.0*(mag-5)*50.0, 50.0))
        self.params.setDefault("significant/minmag", self.params.maxRounded(4.0, mag-1, 0.5))
        
        self.params.setDefault("summary/aftershocks_list_minmag", self.params.maxRounded(1.0, mag-1.5, 0.5))
        self.params.setDefault("summary/historical_list_minmag", self.params.maxRounded(3.0, mag-1.0, 0.5))
        self.params.setDefault("summary/significant_list_minmag", self.params.maxRounded(3.0, mag-1.0, 0.5))

        self.params.setDefault("plot_map/height_km", self.params.maxRounded(50.0, 3*self.params.get("historical/maxdist_km"), 50.0))
        self.params.setDefault("plot_map/zoom_level", int(12-math.floor(self.params.get("plot_map/height_km")/75.0)))

        return


    def fetchMainshock(self):
        """
        Fetch event information.
        """
        if self.showProgress:
            print("Fetching mainshock information from data center...")

        datacenter = self.params.get("catalog")[0]
        if datacenter == "USGS":
            services = {'station': None,
                        'event': "http://earthquake.usgs.gov/fdsnws/event/1",
                        'dataselect': None}
            client = Client(datacenter, service_mappings=services, debug=False)
        else:
            client = Client(datacenter)
        catalog = client.get_events(eventid=self.params.get("mainshock"))
        event = catalog.events[0]

        event.write(self.params.get("files/mainshock"), format="QUAKEML")

        return


    def fetchAftershocks(self):
        """
        Fetch event information.
        """
        if self.showProgress:
            print("Fetching aftershock event information from data center...")

        mainshock = self._loadMainshock()
        origin = mainshock.preferred_origin()

        params = self.params.get("aftershocks")
        minmag = params['minmag']
        maxdist = params['maxdist_km']*KM_TO_DEG
        if "max_duration_days" in params.keys():
            endtime = origin.time + params['max_duration_days']*DAY_TO_SECS
        else:
            endtime = self.now

        self.aftershocks.fetch(
            starttime=origin.time+1, 
            endtime=endtime,
            longitude=origin.longitude,
            latitude=origin.latitude,
            maxdist=maxdist,
            minmag=minmag,
            catalog=self.params.get("catalog"))
        return


    def fetchSignificant(self):
        """
        Fetch significant historical seismicity information.
        """
        if self.showProgress:
            print("Fetching significant historical seismicity information from data center...")

        mainshock = self._loadMainshock()
        origin = mainshock.preferred_origin()

        params = self.params.get("significant")
        minmag = params['minmag']
        maxdist = params['maxdist_km']*KM_TO_DEG
        starttime = origin.time - params['years']*YEAR_TO_SECS

        self.significant.fetch(
            starttime=starttime,
            endtime=origin.time-1,
            longitude=origin.longitude,
            latitude=origin.latitude,
            maxdist=maxdist,
            minmag=minmag,
            catalog=self.params.get("catalog"))
        return


    def fetchForeshocks(self):
        """
        Fetch foreshock event information.
        """
        if self.showProgress:
            print("Fetching foreshock event information from data center...")

        mainshock = self._loadMainshock()
        origin = mainshock.preferred_origin()

        params = self.params.get("foreshocks")
        minmag = params['minmag']
        maxdist = params['maxdist_km']*KM_TO_DEG
        starttime = origin.time - params['days']*DAY_TO_SECS

        self.foreshocks.fetch(
            starttime=starttime,
            endtime=origin.time-1,
            longitude=origin.longitude,
            latitude=origin.latitude,
            maxdist=maxdist,
            minmag=minmag,
            catalog=self.params.get("catalog"))
        return


    def fetchHistorical(self):
        """
        Fetch historical seismicity information.
        """
        if self.showProgress:
            print("Fetching historical seismicity information from data center...")

        mainshock = self._loadMainshock()
        origin = mainshock.preferred_origin()

        params = self.params.get("historical")
        minmag = params['minmag']
        maxdist = params['maxdist_km']*KM_TO_DEG
        starttime = origin.time - params['years']*YEAR_TO_SECS

        self.historical.fetch(
            starttime=starttime,
            endtime=origin.time-1,
            longitude=origin.longitude,
            latitude=origin.latitude,
            maxdist=maxdist,
            minmag=minmag,
            catalog=self.params.get("catalog"))
        return


    def printSummary(self):

        mainshock = self._loadMainshock()
        self.foreshocks.load()
        self.aftershocks.load()
        self.historical.load()
        self.significant.load()
        
        summary = Summary(self.params, self.now, self.tz, mainshock, self.foreshocks, self.aftershocks, self.historical, self.significant)
        summary.show()
        return
    

    def _loadMainshock(self):
        self.mainshock.load()
        self._setDynamicDefaults()
        return self.mainshock.events[0]


# End of file
