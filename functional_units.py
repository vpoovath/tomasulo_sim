#!/usr/env/python
# Author: Vivek Poovathoor


import os
import sys
import time


NUM_LOAD_SLOTS  = 3
NUM_STORE_SLOTS = 3


class FunctionalUnit:
    def __init__(self,fu_type):
        self._fu_type             = fu_type
        self._current_instruction = None
        self._instr_start_time    = None
        self._rs_station_idx      = None

    @property
    def current_instruction(self):
        return self._current_instruction

    @current_instruction.setter
    def current_instruction(self,instr):
        self._current_instruction = instr

    @property
    def fu_type(self):
        return self._fu_type

    @property
    def instr_start_time(self):
        return self._instr_start_time

    @instr_start_time.setter
    def instr_start_time(self,clock_cycle):
        self._instr_start_time = clock_cycle

    @property 
    def rs_station_idx(self):
        return self._rs_station_idx

    @rs_station_idx.setter
    def rs_station_idx(self,idx):
        self_rs_station_idx = idx

    # This is using the built-in assumption that stat_idx 
    # is the same as the load/store buffer idx. 
    def load_unit(self,instr,clock_cycle,stat_idx):
        self.current_instruction = instr
        self.instr_start_time    = clock_cycle
        self.rs_station_idx      = stat_idx

    def empty_unit(self,idx=None):
        if idx is not None:
            raise AttributeError("Attempting to access MULT or ADD FP" + 
                                 "using invalid index!")
            return None
        self.current_instruction = None
        self.instr_start_time    = None
        self.rs_station_idx      = None

    def is_occupied(self):
        if self.current_instruction is None: return False
        else: return True

    def is_available(self):
        if self.current_instruction is None: return True
        else: return False

    # Clock starts from 1, not 0
    def is_instr_complete(self,instr,curr_time):
        exec_dur = curr_time - self.instr_start_time + 1
        if instr.latency == exec_dur: return True
        else: return False


# Since these are treated like the reservations stations 
# Major assumption - these buffers and the load/store reservations are 
# physically the same thing so they have the same indices 
class LoadStoreUnit():
    def __init__(self,fu_type,num_slots):
        self._fu_type      = fu_type
        self._num_slots    = num_slots
        self._buffer_slots = []
        for i in range(num_slots):
            blank_slot = {"Instruction":None, "Start Time":None,
                          "Station Index": None}
            self._buffer_slots.append(blank_slot)

    @property
    def buffer_slots(self):
        return self._buffer_slots

    @property
    def fu_type(self):
        return self._fu_type

    @property
    def num_slots(self):
        return self._num_slots

    def slot_is_empty(self, slot):
        if (slot["Instruction"] is None and slot["Start Time"] is None and
            slot["Station Index"] is None):
            return True
        else: 
            return False
    
    def find_empty_slot_idx(self):
        for i in range(self.num_slots):
            slot = self.buffer_slots[i]
            if self.slot_is_empty(slot): return i 
        return None

    def load_unit(self,instr,clock_cycle,stat_idx):
        idx = self.find_empty_slot_idx()
        if not(idx is None):
            self.buffer_slots[idx]["Instruction"]   = instr
            self.buffer_slots[idx]["Start Time"]    = clock_cycle
            self.buffer_slots[idx]["Station Index"] = stat_idx

    def empty_slot(self,idx):
        if (idx <= 0 or idx > self.num_slots):
            raise ValueError("Index %d is out of range for Buffer Unit!" %
                             (idx))
            return None
        self.buffer_slots[idx-1]["Instruction"]   = None
        self.buffer_slots[idx-1]["Start Time"]    = None
        self.buffer_slots[idx-1]["Station Index"] = None

    def empty_unit(self,buffer_idx=None):
        if buffer_idx is None:
            print("Empty the entire buffer")
            for slot in self.buffer_slots:
                self.empty_slot(slot)
        else:
            self.empty_slot(buffer_idx)

    def is_occupied(self):
        for slot in self.buffer_slots:
            if not(self.slot_is_empty(slot)): return True
        return False

    def is_available(self):
        if any(self.slot_is_empty(slot) for slot in self.buffer_slots): 
            return True
        else:
            return False

    def find_occupied_slots(self):
        occupied_slots = []
        for i in range(self.num_slots):
            if not(self.slot_is_empty(self.buffer_slots[i])):
                occupied_slots.append(i)
        return occupied_slots

    # Clock starts from 1, not 0
    def is_instr_complete(self,slot,curr_time):
        curr_slot = None
        instr = slot["Instruction"]
        for i in range(self.num_slots):
            if self.buffer_slots[i]["Instruction"] == instr:
                curr_slot = self.buffer_slots[i]
        exec_dur = curr_time - curr_slot["Start Time"] + 1

        if instr.latency == exec_dur: return True
        else: return False


load_fu  = LoadStoreUnit("load", NUM_LOAD_SLOTS)
store_fu = LoadStoreUnit("store", NUM_STORE_SLOTS)
add_fu   = FunctionalUnit("add")
mult_fu  = FunctionalUnit("mult")


def negotiate_bus_contention(fu_list):
    print("Yeah we'll cross that bridge when we get there")
