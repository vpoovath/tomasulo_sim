# Author: Vivek Poovathoor
# This module consists of functions that allow for the creation 
# of a register file as well interacting with it and individual registers
# and their tags. 


import os
import sys
from tag import Tag


DEFAULT_REG_VALUE = 2 # Set to 2 to make arithmetic operations interesting.


# The register file by default has 32 registers [0,...,30].
# The keys are the register names and the values a list containing Q_i tuple
# and actual register value. 
# Upon intialization the Q_i tuple for the registers are left at "(None,None)".
# Similarly, the value inside each register is 0 upon initialization.
# Q_i values are represented as a tuple, e.g. (mult,0) or (load,2). 
def create_register_file(max_num_regs=30):
    register_file = {"R"+str(k):[[],DEFAULT_REG_VALUE]
                             for k in range(0,max_num_regs+2,1)}
    float_point_registers = {"F"+str(k):[[],DEFAULT_REG_VALUE]
                             for k in range(0,max_num_regs+2,1)}
    register_file.update(float_point_registers)

    return register_file

# Load a value into a given register. This function could also
# be used to reset the register to its default value. 
def load_register_value(register_file, reg_name,value=None):
    if value is None: value = DEFAULT_REG_VALUE
    if isinstance(reg_name,str): register_file[reg_name][1] = value


# Append a Tag object into a register given the register's name.
# A tag requires the reservation station type and station's index.
# Checks are put in place to make sure that the Tag does not already
# exist in the list. Otherwise, the Tag object is added to the list. 
def load_register_tag(reg_file, reg_name, rs_type, stat_idx):
    tag_list = reg_file[reg_name][0]
    if not(len(tag_list) == 0):
        if (tag_list[0].rs_type == rs_type and tag_list[0].idx == stat_idx):
            return 
        else:
            reg_file[reg_name][0].append(Tag(rs_type,stat_idx))
    else:
        reg_file[reg_name][0].append(Tag(rs_type,stat_idx))


# Find and return the Tag object at the given register in the 
# register file.
def get_reg_tag(reg_file, reg_name):
    try:
        tag = reg_file[reg_name][0][0]
    except IndexError:
        return None

    return tag


#
def clear_register_tag(reg_file, reg_name,tag_idx=None):
    if tag_idx is None: idx = 0
    else: idx = tag_idx
    tag_list = reg_file[reg_name][0]
    del tag_list[idx]


# 
def is_register_available(register_file, reg_name, exp_type=None, exp_idx=None):
    try:
        if not(exp_type is None) and not(exp_idx is None):
            if (register_file[reg_name][0][0].rs_type == exp_type and 
                register_file[reg_name][0][0].idx == exp_idx):
                return True
            elif len(register_file[reg_name][0]) == 0:
                return True
            else:
                return False
        else:
            if len(register_file[reg_name][0]) == 0:
                return True
            else:
                return False
    except IndexError:
        return True
