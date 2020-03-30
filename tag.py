#!/usr/env/python


import os
import sys
import time


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
