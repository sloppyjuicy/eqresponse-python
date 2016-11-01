#!/usr/bin/env python
#
# ======================================================================
#
#                           Brad T. Aagaard
#                        U.S. Geological Survey
#
# ======================================================================
#

# Setup script for the obspyutils package

from distutils.core import setup

setup(name='eqresponse',
      version='0.1.0',
      description='Applications for collecting and visualizing information for earthquake response.',
      author='Brad Aagaard',
      packages=[
          'eqresponse',
          'eqresponse/apps',
          'eqresponse/seismicity',
          'eqresponse/core',
          ],
      scripts=[
          'bin/eqresponse_identify',
          'bin/eqresponse_seismicity',
          #'bin/eqresponse_sequences',
          ]
      )


# End of file
