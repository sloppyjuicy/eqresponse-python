# ======================================================================
#
#                           Brad T. Aagaard
#                        U.S. Geological Survey
#
# ======================================================================
#

import math

class Parameters(object):

    def __init__(self):
        self.parameters = {}
        return


    def get(self, label):
        keys = label.split("/")
        param = self.parameters[keys[0]]
        for key in keys[1:]:
            param = param[key]
        return param
    

    def load(self, filename):
        import os
        import json
        if os.path.isfile(filename):
            fin = open(filename, 'r')
            self.parameters = json.load(fin)
        return

    
    def initialize(self, defaults):
        self.parameters = Parameters._merge(defaults, self.parameters)
        return


    def setDefault(self, label, value):
        keys = label.split("/")
        d = self.parameters
        for key in keys:
            dP = d
            d = d[key]

        if dP[key] is None:
            dP[key] = value
            print("Setting '%s' to '%s', result: %s." % (label, value, self.get(label)))
        return
    
    
    @staticmethod
    def _merge(dst, src):
        from copy import deepcopy

        if isinstance(dst, dict) and isinstance(src, dict):
            keysOverlap = src.viewkeys() & dst.viewkeys()
            keysAll = src.viewkeys() | dst.viewkeys()
            return {k: Parameters._merge(dst[k], src[k]) if k in keysOverlap else
                             deepcopy(src[k] if k in src else dst[k]) for k in keysAll}
        return deepcopy(src)

    
    @staticmethod
    def maxRounded(value1, value2, scale):
        v = max(value1, value2)
        r = scale*math.floor(v/scale)
        return r


# End of file
