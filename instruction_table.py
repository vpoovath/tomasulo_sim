#!/usr/env/python
# Author: Vivek Poovathoor


import os
import sys
import time


# This function requires the list of Instruction objects to be passed in
def create_instruction_table(instruction_list):
    instruction_table = []
    for instr in instruction_list: 
        blank_entry = {"Instruction":instr, "Issue":None, "Exec Start":None,
                       "Exec Complete":None, "Write Result":None}
        instruction_table.append(blank_entry) 

    return instruction_table


# 
def find_instr_idx(instr_table,station):
    for entry in instr_table:
        if (entry['Instruction'].operation == station[1] and 
            entry['Instruction'].dest == station[3] and
            entry['Instruction'].operand1 == station[5] and
            entry['Instruction'].operand2 == station[7]):
            return instr_table.index(entry)
    print("Instruction NOT FOUND") 

    return None


#
def find_entry_idx(instr_table,instruction):
    for entry in instr_table:
        if entry['Instruction'] == instruction:
            return instr_table.index(entry)

    return None


#
def entry_is_incomplete(entry):
    if any(value is None for key,value in entry.items()): return True
    else: return False


#
def instruction_table_is_incomplete(instr_table):
    if any(entry_is_incomplete(entry) for entry in instr_table): return True
    else: return False


#
def issue_instruction(instr_table,idx,clock_cycle):
    instr_table[idx]['Issue'] = clock_cycle


#
def start_execution(instr_table,idx,clock_cycle):
    instr_table[idx]['Exec Start'] = clock_cycle


#
def complete_execution(instr_table,idx,clock_cycle):
    instr_table[idx]['Exec Complete'] = clock_cycle


def write_result(instr_table,idx,clock_cycle):
    instr_table[idx]['Write Result'] = clock_cycle
