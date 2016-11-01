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
from eqresponse.seismicity.SummarySequences import SummarySequences
from eqresponse.core.Parameters import Parameters

KM_TO_DEG = 1.0/111.0 # roughly 111 km per latitude degree
DAY_TO_SECS = 24*3600.0
YEAR_TO_SECS = 365.25*DAY_TO_SECS

# :TODO: Remove sequences events from background.

# :TODO: Consider optimizing retrieval by splitting background retrieval into 
# time windows between sequences

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
            },
            "sequences": [],
            'summary': {
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
        setattr(self.background, "params", self.params.get("background"))

        self.sequences = []
        seqparams = self.params.get("sequences")
        for p in seqparams:
            filename = self.params.get("files/sequence") % p['label'].replace(" ","-")
            sequence = Catalog(filename)
            setattr(sequence, "params", p)
            self.sequences.append(sequence)
        return

    
    def fetchBackground(self):
        """
        Fetch background event information.
        """
        if self.showProgress:
            print("Fetching background event information from data center...")

        params = self.params.get("background")
        self.background.fetch(
            starttime=params['start'],
            endtime=params['end'],
            longitude=params['longitude'],
            latitude=params['latitude'],
            maxdist=params['maxdist_km']*KM_TO_DEG,
            minmag=params['minmag'],
            catalog=self.params.get("catalog"))
        return


    def fetchSequences(self):
        """
        Fetch sequences seismicity information.
        """
        for sequence in self.sequences:
            params = sequence.params
            if self.showProgress:
                print("Fetching seismicity information for '%s' from data center..." % params['label'])

            sequence.fetch(
                starttime=params['start'],
                endtime=params['end'],
                longitude=self.params.get("background/longitude"),
                latitude=self.params.get("background/latitude"),
                maxdist=self.params.get("background/maxdist_km")*KM_TO_DEG,
                minmag=params['minmag'],
                catalog=self.params.get("catalog"),
            )
        return


    def printSummary(self):
        self.background.load()
        for sequence in self.sequences:
            sequence.load()

        summary = SummarySequences(self.params, self.now, self.tz)
        summary.show(self.background, self.sequences)
        return
    

# End of file
