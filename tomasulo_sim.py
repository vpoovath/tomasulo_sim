#!/usr/env/python


import sys
import instruction_reader as ir
import instruction_table as it
import register_file as rf
import reservation_stations as rs
import functional_units as fu
from collections import OrderedDict
from operator import itemgetter
from functional_units import FunctionalUnit
from functional_units import LoadStoreUnit


def get_corresponding_rs_fu(rs_type, rs_list, fu_list):
    switcher = {"load": (rs_list[0], fu_list[0]),
                "store": (rs_list[1], fu_list[1]),
                "add": (rs_list[2], fu_list[2]),
                "mult": (rs_list[3], fu_list[3])
               }

    return switcher.get(rs_type,(None,None))


def summarize_results(clock_cycle, instr_table):
    print("\nClock Cycle: %s " % str(clock_cycle))
    for idx,entry in enumerate(instr_table):
        instr_out = ("Instr index: %s\t\t" % str(idx))
        issue_out = ("Issue: %s\t\t" % str(entry["Issue"]))
        start_out = ("Exec Strt: %s\t\t" % str(entry["Exec Start"]))
        compl_out = ("Exec Comp: %s\t\t" % str(entry["Exec Complete"]))
        write_out = ("Write Res: %s" % str(entry["Write Result"]))
        print(instr_out + issue_out + start_out + compl_out + write_out)


def resolve_contention(broadcast_instr, reg_file):
    stat_indices = [(rf.get_reg_tag(reg_file, write_res[1].dest).idx,
                     broadcast_instr.index(write_res)) for write_res in
                    broadcast_instr]
    sorted(stat_indices, key = itemgetter(1))
    smallest_rs_idx = stat_indices[0][1]
    return broadcast_instr[smallest_rs_idx]


# 
def run_tomasulo_sim(filename=None):
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
    instr_list      = ir.create_instruction_list(filename)
    instr_table     = it.create_instruction_table(instr_list)
    clock_cycle     = 0
    instr_idx       = 0
    curr_instr      = instr_list[instr_idx]
    broadcast_instr = []

    while (not(len(instr_list) == 0) or 
           it.instruction_table_is_incomplete(instr_table)):
        try:
            clock_cycle += 1
            # Write-Result/Broadcast-Block
            # for write_res in broadcast_instr:
            if broadcast_instr:
                if len(broadcast_instr) > 1:
                    write_res = resolve_contention(broadcast_instr, reg_file)
                else:
                    write_res = broadcast_instr[0]

                write_res          = broadcast_instr[0]
                entry_idx          = it.find_entry_idx(instr_table, write_res[1])
                instr              = write_res[1]
                dest_reg           = write_res[1].dest
                try:
                    rs_type        = rf.get_reg_tag(reg_file, dest_reg).rs_type
                    stat_idx       = rf.get_reg_tag(reg_file, dest_reg).idx
                except AttributeError:
                    print("Found a No Tag at Destination Register!")
                    break
                (curr_rs, curr_fu) = get_corresponding_rs_fu(rs_type, rs_list,
                                                             fu_list)
                
                if (curr_fu.fu_type == "add" or curr_fu.fu_type == "mult"):
                    curr_fu.empty_unit()
                else:
                    curr_fu.empty_unit(stat_idx)
    
                it.write_result(instr_table, entry_idx, clock_cycle)
                value = instr.execute_op(reg_file)
                if value: rf.load_register_value(reg_file, dest_reg, value)
                rs.clear_rs_tags(rs_list, rf.get_reg_tag(reg_file, dest_reg))
                rf.clear_register_tag(reg_file, dest_reg)
                rs.clear_station(curr_rs, stat_idx)
                broadcast_instr.remove(write_res)
    
            # Issue-Instruction Block
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
    
                # Start-Execution Block
                for res_stat in rs_list:
                    if res_stat.is_occupied():
                        occupied_stations = res_stat.find_occupied_station_idx()
                        for idx in occupied_stations:
                            busy_stations[idx] = res_stat
    
                for stat_idx,res_stat in busy_stations.items():
                    func_unit = rs.get_corresponding_fu(res_stat.stations[stat_idx])
    
                    if res_stat.stations[stat_idx][8] == "Ready":
                        station = res_stat.stations[stat_idx]
                        exec_instr_idx = it.find_instr_idx(instr_table, station)
    
                        if (instr_table[exec_instr_idx]['Exec Start'] is None and 
                            func_unit.is_available()):
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
    
                # Complete-Execution Block
                for func_unit in fu_list:
                    if func_unit.is_occupied():
                        if (func_unit.fu_type == "load" or func_unit.fu_type == "store"):
                            occupied_slots = func_unit.find_occupied_slots()
                            for slot_idx in occupied_slots:
                                slot = func_unit.buffer_slots[slot_idx]
                                instr = slot["Instruction"]
                                if func_unit.is_instr_complete(slot, clock_cycle):
                                    compl_instr_idx = it.find_entry_idx(instr_table,
                                                                        instr)
                                    it.complete_execution(instr_table, 
                                                          compl_instr_idx, 
                                                          clock_cycle)
                                    broadcast_instr.append((func_unit, instr))
                        else:
                            instr = func_unit.current_instruction
                            if func_unit.is_instr_complete(instr, clock_cycle):
                                compl_instr_idx = it.find_entry_idx(instr_table,
                                                                    instr)
                                it.complete_execution(instr_table, 
                                                      compl_instr_idx, 
                                                      clock_cycle)
                                broadcast_instr.append((func_unit, instr))

            summarize_results(clock_cycle, instr_table)
        except KeyboardInterrupt:
            print("Simulator abruptly interrrupted. Exiting...")
            break

    print("\nFinished at Clock Cycle: %s" % str((clock_cycle)))
    summarize_results(clock_cycle, instr_table)
    for reg,value in reg_file.items():
        print("Register %s: %d" % (reg, value[1]))


if __name__ == '__main__':
    if len(sys.argv) > 1:
        print("Input File: " + str(sys.argv[1]))
        run_tomasulo_sim(sys.argv[1])
    else:
        run_tomasulo_sim()
