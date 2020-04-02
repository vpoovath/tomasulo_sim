#!/usr/env/python
# Author: Vivek Poovathoor


import os
import sys
import time


# This function requires the list of Instruction objects to be passed in.
# Using that list of instructions (presumable read from a text file), 
# it generates a the instruction (summary) table in which the status
# of all instructions is maintained.
def create_instruction_table(instruction_list):
    instruction_table = []
    for instr in instruction_list: 
        blank_entry = {"Instruction":instr, "Issue":None, "Exec Start":None,
                       "Exec Complete":None, "Write Result":None}
        instruction_table.append(blank_entry) 

    return instruction_table


# This function is used to retrieve the instruction index
# from the instruction (summary) table based off of contents
# loaded inside a station of a Reservation Station. 
# If the station's fields match that of the entry inside the 
# table, then return the corresponding Instruction's index which
# is indicative of its location within the program.
def find_instr_idx(instr_table,station):
    for entry in instr_table:
        if (entry['Instruction'].operation == station[1] and 
            entry['Instruction'].dest == station[3] and
            entry['Instruction'].operand1 == station[5] and
            entry['Instruction'].operand2 == station[7]):
            return instr_table[entry]['Instruction'].instr_index
    print("Instruction NOT FOUND") 

    return None


# Determine if the given entry in the instruction (summary) 
# table is incomplete or not. 
def entry_is_incomplete(entry):
    if any(value is None for key,value in entry.items()): return True
    else: return False


# Determine if there is an entry within the entire
# instruction table that is incomplete, thereby implying
# that the instruction table is incomplete.
def instruction_table_is_incomplete(instr_table):
    if any(entry_is_incomplete(entry) for entry in instr_table): return True
    else: return False


# Access the entry of the instruction_table corresponding
# to the given index and update the entry's Issue field
# to the value of clock_cycle.
def issue_instruction(instr_table,idx,clock_cycle):
    instr_table[idx]['Issue'] = clock_cycle


# Access the entry of the instruction_table corresponding
# to the given index and update the entry's Start Exec field
# to the value of clock_cycle.
def start_execution(instr_table,idx,clock_cycle):
    instr_table[idx]['Exec Start'] = clock_cycle


# Access the entry of the instruction_table corresponding
# to the given index and update the entry's Exec Complete field
# to the value of clock_cycle.
def complete_execution(instr_table,idx,clock_cycle):
    instr_table[idx]['Exec Complete'] = clock_cycle


# Access the entry of the instruction_table corresponding
# to the given index and update the entry's Write Result field
# to the value of clock_cycle.
def write_result(instr_table,idx,clock_cycle):
    instr_table[idx]['Write Result'] = clock_cycle
