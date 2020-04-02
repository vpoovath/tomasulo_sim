#!/usr/env/python
# Author: Vivek Poovathoor


import os
import sys
import time
import register_file as rf
import functional_units as fu
from collections import OrderedDict as OrderedDict
from tag import Tag


# Cols: [busy status, op name, Qi Tag, op dest, Qj Tag, Vj, Qk Tag, Vk, 
#        ready status, Instruction]
class ReservStation:
    def __init__(self,start_idx,num_stations,rs_type):
        self._rs_type = rs_type
        self._num_stations = num_stations
        self._stations = OrderedDict((key,["No", None, Tag(None,0), None, 
                                           Tag(None,0), None, Tag(None,0),
                                           None,"Not Ready", None]) for key in 
                                     range(start_idx, start_idx+num_stations))
    @property
    def rs_type(self):
        return self._rs_type

    @property
    def stations(self):
        return self._stations

    @property
    def num_stations(self):
        return self._num_stations

    def find_nonoccupied_station_idx(self):
        for station,value in self.stations.items():
            if value[0] == "No": return station
        return None

    def is_occupied(self):
        if any(value[0] == "Yes" for station,value in self.stations.items()):
            return True
        else:
            return False

    def find_occupied_station_idx(self):
        occupied_stations = []
        for station,value in self.stations.items():
            if value[0] == "Yes": occupied_stations.append(station)
        return occupied_stations


NUM_LD_STATIONS     = 3
NUM_SD_STATIONS     = 3
NUM_ADDD_STATIONS   = 3
NUM_MULTD_STATIONS  = 2
LD_STATION_START    = 1
SD_STATION_START    = LD_STATION_START + NUM_LD_STATIONS
ADDD_STATION_START  = LD_STATION_START + NUM_LD_STATIONS + NUM_SD_STATIONS
MULTD_STATION_START = (LD_STATION_START + NUM_LD_STATIONS + NUM_SD_STATIONS +
                       NUM_ADDD_STATIONS)

load_rs  = ReservStation(LD_STATION_START,NUM_LD_STATIONS,"load")
store_rs = ReservStation(SD_STATION_START,NUM_SD_STATIONS,"store")
add_rs   = ReservStation(ADDD_STATION_START,NUM_ADDD_STATIONS,"add")
mult_rs  = ReservStation(MULTD_STATION_START,NUM_MULTD_STATIONS,"mult")


# 
def get_corresponding_fu(station):
    op = station[1]
    switcher = {"LD": fu.load_fu,
                "SD": fu.store_fu,
                "ADDD":fu.add_fu,
                "SUBD":fu.add_fu,
                "MULTD":fu.mult_fu,
                "DIVD":fu.mult_fu,
               }

    return switcher.get(op,-1)


# This function checks to see if the given station is READY
# to be start execution.
def is_station_ready(res_stat, stat_idx, reg_file):
    station = res_stat.stations[stat_idx]
    if (get_corresponding_fu(station) == -1):
        raise ValueError("Invalid instruction operation!")

    func_unit       = get_corresponding_fu(station)
    operand1_ready  = (station[4].rs_type is None and station[4].idx == 0)
    operand2_ready  = (station[6].rs_type is None and station[6].idx == 0)
    dest_ready      = rf.is_register_available(reg_file,
                                               station[3],
                                               station[2].rs_type,
                                               station[2].idx)
    fu_is_available = func_unit.is_available()

    # The load tag here is meant to handle the case when a register is used
    # consecutively as a destination register (e.g. one load and then
    # another load to the same register):w
    if (operand1_ready and operand2_ready and dest_ready and fu_is_available):
        rf.load_register_tag(reg_file, station[3], res_stat.rs_type, 
                             stat_idx)
        return True
    else:
        return False


# 
def clear_station(res_stat, stat_idx):
    res_stat.stations[stat_idx][0] = "No"
    res_stat.stations[stat_idx][1] = None
    res_stat.stations[stat_idx][2].clear_tag()
    res_stat.stations[stat_idx][3] = None
    res_stat.stations[stat_idx][4].clear_tag()
    res_stat.stations[stat_idx][5] = None
    res_stat.stations[stat_idx][6].clear_tag()
    res_stat.stations[stat_idx][7] = None
    res_stat.stations[stat_idx][8] = "Not Ready"


#
def clear_rs_tags(rs_list, tag):
    for res_stat in rs_list:
        for stat_idx, station in res_stat.stations.items():
            if (station[2].rs_type == tag.rs_type and 
                station[2].idx == tag.idx):
                station[2].clear_tag()
            if (station[4].rs_type == tag.rs_type and 
                station[4].idx == tag.idx):
                station[4].clear_tag()
            if (station[6].rs_type == tag.rs_type and 
                station[6].idx == tag.idx):
                station[6].clear_tag()


#
def get_station_instr_idx(station):
    print(station[9].instr_index)
    return station[9].instr_index


#
def get_station_vj(station):
    return station[5]


#
def get_station_vk(station):
    return station[7]


#
def update_station_vj(station, instr, reg_file):
    if isinstance(instr.operand1,int): station[5] = instr.operand1
    else: station[5] = reg_file[instr.operand1][1]

    return station


#
def update_station_vk(station, instr, reg_file):
    if isinstance(instr.operand1,int): station[7] = instr.operand1
    else: station[7] = reg_file[instr.operand1][1]


    return station


#
def execute_station_op(station, reg_file):
    operand1 = get_station_vj(station)
    operand2 = get_station_vk(station)
    operation = station[1]
    if operation == "ADDD": return (operand1 + operand2)
    elif operation == "SUBD": return (operand1 - operand2)
    elif operation == "MULTD": return (1.0*(operand1*operand2))
    elif operation == "DIVD": return (operand1/(1.0*operand2))
    elif operation == "LD": return None
    elif operation == "SD": return None
    else: raise ValueError("Invalid instruction operation")

# Assume that stat_idx is valid index of a non-busy station
def populate_rs(res_stat, stat_idx, instr, reg_file):
    res_stat.stations[stat_idx][0] = "Yes"
    res_stat.stations[stat_idx][1] = instr.operation
    res_stat.stations[stat_idx][3] = instr.dest
    res_stat.stations[stat_idx][9] = instr
    #res_stat.stations[stat_idx][5] = instr.operand1
    #res_stat.stations[stat_idx][7] = instr.operand2

    if type(instr.operand1) == int:
        res_stat.stations[stat_idx][4].clear_tag()
        res_stat.stations[stat_idx][5] = instr.operand1
    else:
        if rf.is_register_available(reg_file,instr.operand1):
            res_stat.stations[stat_idx][4].clear_tag()
            res_stat.stations[stat_idx][5] = reg_file[instr.operand1][1]
        else:
            res_stat.stations[stat_idx][4].rs_type = rf.get_reg_tag(reg_file, 
                                                      instr.operand1).rs_type
            res_stat.stations[stat_idx][4].idx = rf.get_reg_tag(reg_file, 
                                                     instr.operand1).idx
    if type(instr.operand2) == int:
        res_stat.stations[stat_idx][6].clear_tag()
        res_stat.stations[stat_idx][7] = instr.operand2
    else:
        if rf.is_register_available(reg_file, instr.operand2):
            res_stat.stations[stat_idx][6].clear_tag()
            res_stat.stations[stat_idx][7] = reg_file[instr.operand2][1]
        else:
            res_stat.stations[stat_idx][4].rs_type = rf.get_reg_tag(reg_file,
                                                      instr.operand2).rs_type
            res_stat.stations[stat_idx][4].idx = rf.get_reg_tag(reg_file,
                                                      instr.operand2).idx
    
    rf.load_register_tag(reg_file, instr.dest, res_stat.rs_type, stat_idx)
    res_stat.stations[stat_idx][2].rs_type = res_stat.rs_type
    res_stat.stations[stat_idx][2].idx = stat_idx

    if is_station_ready(res_stat, stat_idx, reg_file):
        res_stat.stations[stat_idx][2].rs_type = res_stat.rs_type
        res_stat.stations[stat_idx][2].idx = stat_idx
        res_stat.stations[stat_idx][8] = "Ready"
