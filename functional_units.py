#!/usr/env/python
# Author: Vivek Poovathoor
# This module implements two objects - arithmetic functional units
# and store/load buffers. Both are treated as functional units.
# The arithmetic functional unit can only hold one instruction, 
# and the number of 'slots' in the buffer is set to 3 by default.
# No functions are implemented in this file, only methods that
# correspond to the FunctionalUnit and LoadStoreBuffer object classes.
# Some functions use the same name for the different classes - this
# is done in order to reduce the number of logical checks in the 
# Tomasulo simulator's loop.


import os
import sys
import time


NUM_LOAD_SLOTS  = 3 # Default for load buffer
NUM_STORE_SLOTS = 3 # Default for store buffer


# Only one instruction can be stored inside of a FunctionalUnit object. 
# The functional unit type (fu_type) is set upon initialization while 
# the other attributes of this object can be accessed and set freely.
# Methods are in place to check to see if an instruction occcupies
# the instance of the FunctionalUnit and to see if the FunctionalUnit
# is available in order to accept an incoming instruction from a 
# reservation station.
# The instruction start time is set on the clock cycle the instruction
# first starts execution. The instruction is deemed complete when 
# the current instructions duration time equals the time elapsed
# from start time and the current clock cycle. 
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
    def load_unit(self, instr, clock_cycle, stat_idx):
        self.current_instruction = instr
        self.instr_start_time    = clock_cycle
        self.rs_station_idx      = stat_idx

    def empty_unit(self, idx=None):
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


# It is assumed that in physical implementation, the indices
# of a Load/Store buffer is the same as the Load/Store reservation 
# stations. A separate functional unit for a Load/Store buffer is created
# in order to easily handle the instructions in the main simulator loop.
# A LoadStoreUnit can contain a specified amount of 'slots' within itself
# that house load or store instructions. 
# There are methods that have the same name as methods for a FunctionalUnit,
# however their implementations are different due to the presence of a 
# buffer slots list. Appropriate comments are given for each method.
# Checking whether or not an instruction is complete uses the same 
# arithmetic as seen before. 
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

    # Find the next available slot and store the instruction there
    # at the current clock cycle. 
    def load_unit(self,instr,clock_cycle,stat_idx):
        idx = self.find_empty_slot_idx()
        if not(idx is None):
            self.buffer_slots[idx]["Instruction"]   = instr
            self.buffer_slots[idx]["Start Time"]    = clock_cycle
            self.buffer_slots[idx]["Station Index"] = stat_idx

    # Given the slot index, first check it is range, and then empty 
    # the instruction at that slot.
    def empty_slot(self, stat_idx):
        if (stat_idx <= 0):
            raise ValueError("Index %d is out of range for Buffer Unit!" %
                             (stat_idx))
            return None
        elif (stat_idx > self.num_slots):
            idx = stat_idx - self.num_slots
        else:
            idx = stat_idx
            
        self.buffer_slots[idx-1]["Instruction"]   = None
        self.buffer_slots[idx-1]["Start Time"]    = None
        self.buffer_slots[idx-1]["Station Index"] = None

    # Empty all slots in the entire load/store buffer unit.
    def empty_unit(self,buffer_idx=None):
        if buffer_idx is None:
            print("Empty the entire buffer")
            for slot in self.buffer_slots:
                self.empty_slot(slot)
        else:
            self.empty_slot(buffer_idx)

    # Find a slot that is not empty. If such a slot is 
    # found return True. Otherwise return False.
    def is_occupied(self):
        for slot in self.buffer_slots:
            if not(self.slot_is_empty(slot)): return True
        return False

    # If at least 1 slot is empty, return True. Otherwise False.
    def is_available(self):
        if any(self.slot_is_empty(slot) for slot in self.buffer_slots): 
            return True
        else:
            return False

    # Find all the slots that are not empty and return a list
    # of their indices.
    def find_occupied_slots(self):
        occupied_slots = []
        for i in range(self.num_slots):
            if not(self.slot_is_empty(self.buffer_slots[i])):
                occupied_slots.append(i)
        return occupied_slots

    # Clock starts from 1, not 0
    # First find the corresponding slot and determine if the 
    # instruction housed within that slot is finished executing.
    def is_instr_complete(self,slot,curr_time):
        curr_slot = None
        instr = slot["Instruction"]
        for i in range(self.num_slots):
            if self.buffer_slots[i]["Instruction"] == instr:
                curr_slot = self.buffer_slots[i]
        exec_dur = curr_time - curr_slot["Start Time"] + 1
        if instr.latency == exec_dur: return True
        else: return False


# Create the actual functional unit objects for load, store,
# add and mult. These will be used in the simulator's main loop.
load_fu  = LoadStoreUnit("load", NUM_LOAD_SLOTS)
store_fu = LoadStoreUnit("store", NUM_STORE_SLOTS)
add_fu   = FunctionalUnit("add")
mult_fu  = FunctionalUnit("mult")
