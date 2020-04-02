#!/usr/env/python
# Author: Vivek Poovathoor
# This module solely implements a Tag object. 


import os
import sys
import time


# This object is used to store the type of reservation station and 
# the index of the specific station within the reseration station.
# This tag object is used by the reservation_station.py and 
# register_file.py modules.
class Tag:
    def __init__(self,rs_type,idx):
        self._rs_type = rs_type
        self._idx = idx
    
    @property
    def rs_type(self):
        return self._rs_type

    @rs_type.setter
    def rs_type(self,rs_type):
        self._rs_type = rs_type

    @property
    def idx(self):
        return self._idx

    @idx.setter
    def idx(self,idx):
        self._idx = idx

    def clear_tag(self):
        self.rs_type = None
        self.idx = 0
