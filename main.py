# main function

import os
import argparse
from mem_reg import *
from single import *
from five import *


#-----------------------------------------
# print metrics 
def format_float(value, precision):
    return f"{value:.{precision}f}".rstrip("0").rstrip(".")

# single cycle metrics: only print single cycle performance
def single_metrics(opFilePath: str, ss: SingleStageCore):
    ss_metrics = [
        "Single Stage Core Performance Metrics: ",
        f"Number of Cycles taken:  {ss.cycle}",
        f"Total Number of Instructions: {ssCore.inst}",
        f"Cycles per instruction:  {format_float(ss.cycle / ss.inst, 16)}",
        f"Instructions per cycle:  {format_float(ss.inst / ss.cycle, 16)}",
    ]

    with open(opFilePath + os.sep + "SingleMetrics.txt", "w") as f:
        f.write("\n".join(ss_metrics))

# five stage metrics: only print five stage performance
def five_metrics(opFilePath: str, fs: FiveStageCore):
    # print after add one instr, no need to add one instr
    fs_metrics = [
        "Five Stage Core Performance Metrics:",
        f"Number of Cycles taken:  {fs.cycle}",
        f"Total Number of Instructions: {fs.num_instr}",
        f"Cycles per instruction:  {format_float(fs.cycle / fs.num_instr, 16)}",
        f"Instructions per cycle:  {format_float(fs.num_instr / fs.cycle, 16)}",
    ]

    with open(opFilePath + os.sep + "FiveMetrics.txt", "w") as f:
        f.write("\n".join(fs_metrics))

# combined performance metrics:
def Performance_metrics(opFilePath: str, ss: SingleStageCore, fs: FiveStageCore):
    ss_metrics = [
        "Single Stage Core Performance Metrics: ",
        f"Number of Cycles taken:  {ss.cycle}",
        f"Total Number of Instructions: {ssCore.inst}",
        f"Cycles per instruction:  {format_float(ss.cycle / ss.inst, 16)}",
        f"Instructions per cycle:  {format_float(ss.inst / ss.cycle, 16)}",
    ]

    
    fs_metrics = [
        "Five Stage Core Performance Metrics:",
        f"Number of Cycles taken:  {fs.cycle}",
        f"Total Number of Instructions: {fs.num_instr}",
        f"Cycles per instruction:  {format_float(fs.cycle / fs.num_instr, 16)}",
        f"Instructions per cycle:  {format_float(fs.num_instr / fs.cycle, 16)}",
    ]

    with open(opFilePath + os.sep + "PerformanceMetrics_Result.txt", "w") as f:
        f.write("\n".join(ss_metrics) + "\n\n" + "\n".join(fs_metrics))

# main  
if __name__ == "__main__":
     
    #parse arguments for input file location

    parser = argparse.ArgumentParser(description='RV32I single and five stage processor')
    parser.add_argument('--iodir', default="", type=str, help='Directory containing the input files.')
    args = parser.parse_args()

    # the current directory for code
    ioDir = os.path.abspath(args.iodir)


    # Show the directory for input files
    print("IO Directory:", ioDir)

    # common imem
    imem = InsMem("Imem", ioDir)

    # single stage processor
    dmem_ss = DataMem("SS", ioDir)
    
    ssCore = SingleStageCore(ioDir, imem, dmem_ss) 

    while(True):
        if not ssCore.halted:
            ssCore.step()

        if ssCore.halted:
            ssCore.myRF.outputRF(ssCore.cycle) # output file of registers after last cycle
            ssCore.printState(ssCore.nextState, ssCore.cycle) # print states after last cycle
            ssCore.cycle += 1
            break
    
    # dump SS data mem.
    dmem_ss.outputDataMem()
    
    # five stages processor
    dmem_fs = DataMem("FS", ioDir)

    fsCore = FiveStageCore(ioDir, imem, dmem_fs)

    while(True):
        if not fsCore.halted:
            fsCore.step()

        if fsCore.halted:
            break
    
    # dump FS data mem.
    dmem_fs.outputDataMem()

    # print in terminal
    print("Single Stage Core Performance Metrics: ")
    print("Number of Cycles taken: ", ssCore.cycle, end=", ")
    print("Number of Instruction in Imem: ", ssCore.inst, end="\n\n")

    print("Five Stage Core Performance Metrics: ")
    print("Number of Cycles taken: ", fsCore.cycle, end=", ")
    # incrementing num of instructions because of an extra HALT instruction which is never decoded
    fsCore.num_instr += 1
    print("Number of Instruction in Imem: ", fsCore.num_instr , end="\n\n")

    # print performance metrics in file
    Performance_metrics(ioDir, ssCore, fsCore)
    
    # seperate performance metrics
    single_metrics(ioDir, ssCore)
    five_metrics(ioDir, fsCore)
