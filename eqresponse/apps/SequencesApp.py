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

# :TODO: Looping over sequences

# SummarySequences

# ----------------------------------------------------------------------
class SequencesApp(object):
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
            "title": "Seismicity",
            "catalog": ["USGS", ""],
            "time_zone": "US/Pacific",
            "fault_azimuth": 143.0,
            "qfaults_region": "sf",
            "background": {
                "start": None,
                "end": None,
                "longitude": None,
                "latitude": None,
                "maxdist_km": 100.0,
                "min_mag": 4.0,
                "color": "gray",
                "maxdist_km": None,
                "minmag": 1.0,
                "days": 7.0,
            },
            "sequences": [],
            'summary': {
                "mag_min": 1.0,
                "list_minmag": 5.0,
            },
            'plot_map': {
                "width_pixels": 1200,
                "height_pixels": 1200,
                "zoom_level": None,
                "height_km": 250,
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
                'background': "background.xml",
                'sequence': "sequence_%s.xml",
                },
        }
        return


    def initialize(self):
        self.background = Catalog(self.params.get("files/background"))
        self.sequences = []
        seqparams = self.params.get("sequences")
        for p in seqparams:
            filename = self.params.get("files/sequence") % p['label'].replace(" ","-")
            self.sequences.append(Catalog(filename))
        return

    
    def fetchBackground(self):
        """
        Fetch background event information.
        """
        if self.showProgress:
            print("Fetching background event information from data center...")

        params = self.params.get("background")
        minmag = params['minmag']
        maxdist = params['maxdist_km']*KM_TO_DEG

        self.background.fetch(
            starttime=start,
            endtime=end,
            longitude=longitude,
            latitude=latitude,
            maxdist=maxdist,
            minmag=minmag,
            catalog=self.params.get("catalog"))
        return


    def fetchSequences(self):
        """
        Fetch sequences seismicity information.
        """
        seqparams = self.params.get("sequences")
        for p in seqparams:

            if self.showProgress:
                print("Fetching seismicity information for '%s' from data center..." % p['label'])

            minmag = params['minmag']
            maxdist = params['maxdist_km']*KM_TO_DEG
            starttime = origin.time - params['years']*YEAR_TO_SECS

            sequence.fetch(
                starttime=starttime,
                endtime=origin.time-1,
                longitude=origin.longitude,
                latitude=origin.latitude,
                maxdist=maxdist,
                minmag=minmag,
                catalog=self.params.get("catalog"))
        return


    def printSummary(self):
        summary = SummarySequences()

        self.background.load()
        summary.show(self.background)

        for sequence in self.sequences:
            summary.show(sequence)
        
        return
    

# End of file
