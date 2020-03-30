#!/usr/env/python


import instruction_reader as ir
import instruction_table as it
import register_file as rf
import reservation_stations as rs
import functional_units as fu
from collections import OrderedDict
from functional_units import FunctionalUnit
from functional_units import LoadStoreUnit


NUM_LD_STATIONS     = 3
NUM_SD_STATIONS     = 3
NUM_ADDD_STATIONS   = 3
NUM_MULTD_STATIONS  = 2
LD_STATION_START    = 0
SD_STATION_START    = LD_STATION_START + NUM_LD_STATIONS
ADDD_STATION_START  = LD_STATION_START + NUM_LD_STATIONS + NUM_SD_STATIONS
MULTD_STATION_START = (LD_STATION_START + NUM_LD_STATIONS + NUM_SD_STATIONS +
                       NUM_ADDD_STATIONS)

load_rs         = rs.load_rs
store_rs        = rs.store_rs
add_rs          = rs.add_rs
mult_rs         = rs.mult_rs
load_fu         = fu.load_fu
store_fu        = fu.store_fu
add_fu          = fu.add_fu
mult_fu         = fu.mult_fu
rs_list         = [load_rs, store_rs, add_rs, mult_rs]
fu_list         = [load_fu, store_fu, add_fu, mult_fu]
reg_file        = rf.create_register_file()
instr_list      = ir.create_instruction_list()
instr_table     = it.create_instruction_table(instr_list)
clock_cycle     = 0
instr_idx       = 0
curr_instr      = instr_list[instr_idx]
broadcast_instr = []

#or it.instruction_table_is_incomplete(instr_table))
while (not(len(instr_list) == 0) or it.instruction_table_is_incomplete(instr_table)):
    try:
        clock_cycle += 1
        # Write-Result/Broadcast Block
        for broadcast_tuple in broadcast_instr:
            entry_idx = it.find_entry_idx(instr_table, broadcast_tuple[1])
            dest_reg = broadcast_tuple[1].dest
            rs_type = rf.get_reg_tag(reg_file, dest_reg).rs_type
            stat_idx = rf.get_reg_tag(reg_file, dest_reg).idx

            if rs_type == "load":
                curr_rs = load_rs
                curr_fu = load_fu
            elif rs_type == "add":
                curr_rs = add_rs
                curr_fu = add_fu
            elif rs_type == "mult":
                curr_rs = mult_rs
                curr_fu = mult_fu
            else:
                curr_rs = store_rs
                curr_fu = store_fu

            it.write_result(instr_table, entry_idx, clock_cycle)
            if (curr_fu.fu_type == "add" or curr_fu.fu_type == "mult"): 
                curr_fu.empty_unit()
            else:
                curr_fu.empty_unit(stat_idx)
            rs.clear_rs_tags(rs_list, rf.get_reg_tag(reg_file, dest_reg))
            rf.clear_register_tag(reg_file, dest_reg)
            rs.clear_station(curr_rs, stat_idx)
            broadcast_instr.remove(broadcast_tuple)

        # Issue Instruction Block
        if not(len(instr_list) == 0):
            op = curr_instr.operation
            if (op == "ADDD" or op == "SUBD"):    curr_rs = rs.add_rs
            elif (op == "MULTD" or op == "DIVD"): curr_rs = rs.mult_rs
            elif op == "LD":                      curr_rs = rs.load_rs
            else:                                 curr_rs = rs.store_rs

            if not (curr_rs.find_nonoccupied_station_idx() is None):
                rs_idx = curr_rs.find_nonoccupied_station_idx()
                it.issue_instruction(instr_table, instr_idx, clock_cycle)
                rs.populate_rs(curr_rs, rs_idx, curr_instr, reg_file)
                instr_list.remove(curr_instr)
                instr_idx += 1
                if not(len(instr_list) == 0): curr_instr = instr_list[0]

        if it.instruction_table_is_incomplete(instr_table):
            busy_stations = OrderedDict(())

            # Start Execution Block
            for res_stat in rs_list:
                if res_stat.is_occupied():
                    occupied_stations = res_stat.find_occupied_station_idx()
                    for idx in occupied_stations:
                        busy_stations[idx] = res_stat

            # Here we're servicing the busy stations - an instruction leaves the
            # busy_station when it is ready to execute. Note this is different from
            # the instruction leaving the RESERVATION STATION (which occurs when 
            # it is ready to broadcaset to the CDB)
            for stat_idx,res_stat in busy_stations.items():
                func_unit = rs.get_corresponding_fu(res_stat.stations[stat_idx])

                if res_stat.stations[stat_idx][8] == "Ready":
                    station = res_stat.stations[stat_idx]
                    exec_instr_idx = it.find_instr_idx(instr_table, station)

                    if instr_table[exec_instr_idx]['Exec Start'] is None:
                        it.start_execution(instr_table,exec_instr_idx, clock_cycle)
                        func_unit.load_unit(instr_table[exec_instr_idx]['Instruction'],
                                            clock_cycle, stat_idx)
                else:
                    if (rs.is_station_ready(res_stat, stat_idx, reg_file)):
                        res_stat.stations[stat_idx][8] = "Ready"
                        rf.load_register_tag(reg_file,
                                             res_stat.stations[stat_idx][3],
                                             res_stat.rs_type,
                                             stat_idx)
                    else:
                        res_stat.stations[stat_idx][8] = "Not Ready"

            # Complete Execution Block
            # TODO: Replace with simpler for-loop
            for func_unit in fu_list:
                if func_unit.is_occupied():
                    if (func_unit.fu_type == "load" or func_unit.fu_type == "store"):
                        occupied_slots = func_unit.find_occupied_slots()
                        for slot_idx in occupied_slots:
                            slot = func_unit.buffer_slots[slot_idx]
                            instr = slot["Instruction"]
                            if func_unit.is_instr_complete(slot, clock_cycle):
                                compl_instr_idx = it.find_entry_idx(instr_table, instr)
                                it.complete_execution(instr_table, compl_instr_idx, clock_cycle)
                                broadcast_instr.append((func_unit, instr))
                    else:
                        instr = func_unit.current_instruction
                        if func_unit.is_instr_complete(instr, clock_cycle):
                            compl_instr_idx = it.find_entry_idx(instr_table, instr)
                            it.complete_execution(instr_table, compl_instr_idx, clock_cycle)
                            broadcast_instr.append((func_unit, instr))
                            

            ########################################################################################
            #if load_fu.is_occupied():
            #    occupied_slots = load_fu.find_occupied_slots()
            #    for slot_idx in occupied_slots:
            #        if load_fu.is_instr_complete(load_fu.buffer_slots[slot_idx], clock_cycle):
            #            complete_instr_idx = it.find_entry_idx(instr_table,
            #                                                   load_fu.buffer_slots[slot_idx]["Instruction"])
            #            it.complete_execution(instr_table, complete_instr_idx, clock_cycle)
            #            broadcast_instr.append((load_fu,
            #                                    load_fu.buffer_slots[slot_idx]["Instruction"]))
            #if store_fu.is_occupied():
            #    occupied_slots = store_fu.find_occupied_slots()
            #    for slot_idx in occupied_slots:
            #        if store_fu.is_instr_complete(store_fu.buffer_slots[slot_idx], clock_cycle):
            #            complete_instr_idx = it.find_entry_idx(instr_table,
            #                                                   store_fu.buffer_slots[slot_idx]["Instruction"])
            #            it.complete_execution(instr_table, complete_instr_idx, clock_cycle)
            #            broadcast_instr.append((store_fu,
            #                                    store_fu.buffer_slots[slot_idx]["Instruction"]))

            ## TODO: Replace with simpler for-loop, separate from the load and store 
            ## buffers
            #if fu.add_fu.is_occupied():
            #    if fu.add_fu.is_instr_complete(fu.add_fu.current_instruction, clock_cycle):
            #        complete_instr_idx = it.find_entry_idx(instr_table,
            #                                               fu.add_fu.current_instruction)
            #        it.complete_execution(instr_table, complete_instr_idx, clock_cycle)
            #        broadcast_instr.append((add_fu, add_fu.current_instruction))

            #if fu.mult_fu.is_occupied():
            #    if fu.mult_fu.is_instr_complete(fu.mult_fu.current_instruction, clock_cycle):
            #        complete_instr_idx = it.find_entry_idx(instr_table,
            #                                               fu.mult_fu.current_instruction)
            #        it.complete_execution(instr_table, complete_instr_idx, clock_cycle)
            #        broadcast_instr.append((mult_fu, mult_fu.current_instruction))
            ########################################################################################

    except KeyboardInterrupt:
        print("Clock cycle finished at: %d" % (clock_cycle))
        for idx,entry in enumerate(instr_table):
            print(entry)
        break


print("Clock cycle finished at: %d" % (clock_cycle))
for idx,entry in enumerate(instr_table):
    instr_out = ("Instr index: %d" % idx)
    issue_out = ("\t Issue: %d" % entry["Issue"])
    start_out = ("\t Exec Start %d" % entry["Exec Start"])
    compl_out = ("\t Exec Complete %d" % entry["Exec Complete"])
    write_out = ("\t Write Result %d" % entry["Write Result"])
    print(instr_out + issue_out + start_out + compl_out + write_out)

#for load_station in load_rs.stations:
#    print(load_rs.stations[load_station])
#print("***********************************************************************")
#for store_station in store_rs.stations:
#    print(store_rs.stations[store_station])
#print("***********************************************************************")
#for add_station in add_rs.stations:
#    print(add_rs.stations[add_station])
#print("***********************************************************************")
#for mult_station in mult_rs.stations:
#    print(mult_rs.stations[mult_station])
#print("***********************************************************************")
