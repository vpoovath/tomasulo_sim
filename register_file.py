# Author: Vivek Poovathoor


import os
import sys
from tag import Tag


DEFAULT_REG_VALUE = 0


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


def load_register_value(register_file, reg_name,value=None):
    if not(value is None): value = DEFAULT_REG_VALUE
    if not(isinstance(reg_name,int)):
        register_file[reg_name][1] = reg_name


def load_register_tag(reg_file, reg_name, rs_type, stat_idx):
    tag_list = reg_file[reg_name][0]
    if not(len(tag_list) == 0):
        if (tag_list[0].rs_type == rs_type and tag_list[0].idx == stat_idx):
            return 
        else:
            reg_file[reg_name][0].append(Tag(rs_type,stat_idx))
    else:
        reg_file[reg_name][0].append(Tag(rs_type,stat_idx))


def get_reg_tag(register_file, reg_name):
    tag = register_file[reg_name][0][0]

    return tag


def clear_register_tag(reg_file, reg_name,tag_idx=None):
    if tag_idx is None: idx = 0
    else: idx = tag_idx
    tag_list = reg_file[reg_name][0]
    del tag_list[idx]


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


register_file = create_register_file()
