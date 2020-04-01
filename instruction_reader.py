# Author: Vivek Poovathoor


import sys
import os


# Helper function to check if strings are integers
def is_int(value):
    try:
        int(value)
        return True
    except ValueError:
        return False


# This function acts like a switch-case statement to determine the 
# appropriate latency to assign to each instruction given the instruction's
# op-name. 
def latency_switcher(op,load_late=3,store_late=3,add_late=2,mult_late=10,
                     div_late=40):
    switcher = {"LD"    : load_late,
                "SD"    : store_late,
                "ADDD"  : add_late,
                "SUBD"  : add_late,
                "MULTD" : mult_late,
                "DIVD"  : div_late,
               }
    return switcher.get(op,-1)


# Instructions can only be LOAD, MULT, ADD, or DIVIDE
# Assumption: These instructions are placed in a text file
# and consist of an instruction, dest, and two operands. 
# Immediate addressing values take the form of, for example,
# 34+ or 34-. The range of immediate addresses is assumed to 
# be from 0-99.
class Instruction:
    def __init__(self,op,dest,operand1,operand2):
        self._operation = op
        self._dest = dest

        if is_int(operand1[0:2]):
            num = int(operand1[0:2])
            if operand1[2] == "-": num *= -1
            self._operand1 = num
        else:
            self._operand1  = operand1

        if is_int(operand2[0:2]):
            num = int(operand2[0:2])
            if operand2[2] == "-": num *= -1
            self._operand2 = num
        else:
            self._operand2  = operand2

        self._latency = latency_switcher(op)

    @property
    def operation(self):
        return self._operation

    @property
    def dest(self):
        return self._dest

    @property
    def operand1(self):
        return self._operand1

    @property
    def operand2(self):
        return self._operand2
    
    @property
    def latency(self):
        return self._latency


# Directly read the instructions from the text file. 
# If no text file is specified, the one within project's directory is used.
def read_text_input(filename):
    text_list = []
    with open(filename,'r') as fp:
        line = fp.readline()
        while line:
            text_list.append(line.split())
            line = fp.readline()

    return text_list


# Using the instructions from the text file, generate a list of Instruction
# objects that will be used in actual simulation.
def create_instruction_list(filename=None):
    if filename is None: filename = "instruction_input.txt"
    lines        = read_text_input(filename)
    instructions = [Instruction(line[0],line[1],line[2],line[3]) for line in
                    lines]

    return instructions
