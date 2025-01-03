# single cycle processor states, functions

from mem_reg import *

#-----------------------------------------
# single cycle processor states, functions

class State(object):        # model pipeline stages for the processor
    def __init__(self):
        self.IF = {"nop": bool(False), "PC": int(0), "taken": bool(False)}
        self.ID = {"nop": bool(False), "instr": str("0"*32), "PC": int(0), "hazard_nop": bool(False)}
        self.EX = {"nop": bool(False), "instr": str("0"*32), "Read_data1": str("0"*32), "Read_data2": str("0"*32), "Imm": str("0"*32), "Rs": str("0"*5), "Rt": str("0"*5), "Wrt_reg_addr": str("0"*5), "is_I_type": bool(False), "rd_mem": bool(False), 
                   "wrt_mem": bool(False), "alu_op": str("00"), "wrt_enable": bool(False)} # alu_op 00 -> add, 01 -> and, 10 -> or, 11 -> xor
        self.MEM = {"nop": bool(False), "ALUresult": str("0"*32), "Store_data": str("0"*32), "Rs": str("0"*5), "Rt": str("0"*5), "Wrt_reg_addr": str("0"*5), "rd_mem": bool(False), 
                   "wrt_mem": bool(False), "wrt_enable": bool(False)}
        self.WB = {"nop": bool(False), "Wrt_data": str("0"*32), "Rs": str("0"*5), "Rt": str("0"*5), "Wrt_reg_addr": str("0"*5), "wrt_enable": bool(False)}


class Core(object):         # initialize reg file, cycle counter, etc. 
    def __init__(self, ioDir, imem, dmem):
        self.myRF = RegisterFile(ioDir)     # initialize reg file myRF
        self.cycle = 0                      # initialize cycle counter self.cycle
        self.inst = 0                       # initialize ins counter self.inst
        self.halted = False
        self.ioDir = ioDir
        self.state = State()
        self.nextState = State()
        self.ext_imem = imem                # ins obj for fetching data
        self.ext_dmem = dmem                # data mem object for storing data



#------------------------------------
# single cycle functions   # define ALU ops

def Calculate_R(funct7, funct3, rs1, rs2):          
    # define R-Type calculations (e.x. add, sub) Calculate_R
    # based on:
    # funct7 and funct3 bits in the ins, which specify the o
    # registers rs1 and rs2, holding op vals.

    rd = 0
    # ADD
    if funct7 == 0b0000000 and funct3 == 0b000:
        rd = rs1 + rs2

    # SUB
    if funct7 == 0b0100000 and funct3 == 0b000:
        rd = rs1 - rs2

    # XOR
    if funct7 == 0b0000000 and funct3 == 0b100:
        rd = rs1 ^ rs2

    # OR
    if funct7 == 0b0000000 and funct3 == 0b110:
        rd = rs1 | rs2

    # AND
    if funct7 == 0b0000000 and funct3 == 0b111:
        rd = rs1 & rs2

    return rd

# compute sign extended immediate, sign bit:most significant bit location
def sign_extend(val, sign_bit):

    if (val & (1 << sign_bit)) != 0:        # get sign bit, if is set 
        val = val - (1 << (sign_bit + 1))   # negative value complement
    return val  

def Calculate_I(funct3, rs1, imm):
    # define I-Type calculations (Calculate_I)
    # funct3 for the op type
    # imm represents the imm val in the ins
    # imm is sign-extended to handle negative vals

    rd = 0
    # ADDI
    if funct3 == 0b000:
        rd = rs1 + sign_extend(imm, 11)

    # XORI
    if funct3 == 0b100:
        rd = rs1 ^ sign_extend(imm, 11)

    # ORI
    if funct3 == 0b110:
        rd = rs1 | sign_extend(imm, 11)

    # ANDI
    if funct3 == 0b111:
        rd = rs1 & sign_extend(imm, 11)

    return rd

    
# single cycle CPU
class SingleStageCore(Core):
    # SingleStageCore class inherits from Core, setting up a single-cycle processor with:
    # an output file path for logging states after each cycle.
    # a step func to fetch, decode, and execte ins in one cycle.
    def __init__(self, ioDir, imem, dmem):
        super(SingleStageCore, self).__init__(ioDir + os.sep + "SS_", imem, dmem)
        self.opFilePath = ioDir + os.sep + "StateResult_SS.txt"

    def step(self):                                 # fetch-decode-execte cycle (step function)
        # implementation of each instruction

        # fetch the ins at self.state.IF["PC"] using imem.
        fetchedInstr = int(self.ext_imem.readInstr(self.state.IF["PC"]), 16) # hex into integer
        opcode = fetchedInstr & (2 ** 7 - 1)        # least significant 7 bits

        # decode the ins: opcode determines the ins type, then calls Decode. 
        self.Decode(opcode, fetchedInstr)
        
        # if no branch is take, PC advances by 4 (next ins).
        # if a branch is taken, PC updates based on the br target.
        self.halted = False
        if self.state.IF["nop"]:
            self.halted = True
        
        if not self.state.IF["taken"] and self.state.IF["PC"] + 4 < len(self.ext_imem.IMem):
            self.nextState.IF["PC"] = self.state.IF["PC"] + 4
        else:
            self.state.IF["taken"] = False          # take branch, then set taken to False again
            
        self.myRF.outputRF(self.cycle)              # output file of registers after each cycle
        self.printState(self.nextState, self.cycle) # print states after each cycle
            
        self.state = self.nextState                 #The end of the cycle and updates the current state with the values calculated in this cycle
        self.cycle += 1
        self.inst += 1                              # instruction counter

    def Decode(self, opcode, fetchedInstr):         # ins decode and execute (Deocde function)
        # the Decode func identifies the ins type using opcode and performs the specified ops:
        
        # R-type
        if opcode == 0b0110011:
            # extract fields: funct7, funct3, rs1, rs2, and rd. 
            # perform ALU op using Calculate_R.
            # store result in reg rd. 

            # get funct7
            funct7 = fetchedInstr >> 25
            # get funct3
            funct3 = (fetchedInstr >> 12) & ((1 << 3) - 1)
            # get rs2
            rs2 = (fetchedInstr >> 20) & ((1 << 5) - 1)
            # get rs1
            rs1 = (fetchedInstr >> 15) & ((1 << 5) - 1)
            # get rd
            rd = (fetchedInstr >> 7) & ((1 << 5) - 1)

            # get data in rs1
            data_rs1 = self.myRF.readRF(rs1)
            # get data in rs2
            data_rs2 = self.myRF.readRF(rs2)

            # get result data
            data_rd = Calculate_R(funct7, funct3, data_rs1, data_rs2)
            
            # store all fetched and computed data
            self.myRF.writeRF(rd, data_rd)

        # I Type
        elif opcode == 0b0010011:
            # extract fields: imm, funct3, rs1, rd. 
            # perform ALU op using Calculate_I.
            # store result in reg rd. 

            # get immediate
            imm = fetchedInstr >> 20 & ((1 << 12) - 1)
            # get funct3
            funct3 = (fetchedInstr >> 12) & ((1 << 3) - 1)
            # get rs1
            rs1 = (fetchedInstr >> 15) & ((1 << 5) - 1)
            # get rd
            rd = (fetchedInstr >> 7) & ((1 << 5) - 1)

            # get data in rs1
            data_rs1 = self.myRF.readRF(rs1)

            # get result data
            data_rd = Calculate_I(funct3, data_rs1, imm)
            # store result data in rd register
            self.myRF.writeRF(rd, data_rd)

        # J Type (JAL)
        elif opcode == 0b1101111:
            # J-Type (Jump and Link)
            # compute target add from imm and set PC to the target.
            # store return add (current PC+4) in reg rd.

            # get imm
            imm19_12 = (fetchedInstr >> 12) & ((1 << 8) - 1)
            imm11 = (fetchedInstr >> 20) & 1
            imm10_1 = (fetchedInstr >> 21) & ((1 << 10) - 1)
            imm20 = (fetchedInstr >> 31) & 1
            imm = (imm20 << 20) | (imm10_1 << 1) | (imm11 << 11) | (imm19_12 << 12)

            # get rd
            rd = (fetchedInstr >> 7) & ((1 << 5) - 1)

            self.myRF.writeRF(rd, self.state.IF["PC"] + 4)
            self.nextState.IF["PC"] = self.state.IF["PC"] + sign_extend(imm, 20)
            self.state.IF["taken"] = True

        # B Type (Branch, BEQ/BNE)
        elif opcode == 0b1100011:
            # read rs1, rs2, and funct3, check conditions, and perform branch if conditions are met. 

            # get imm
            imm11 = (fetchedInstr >> 7) & 1
            imm4_1 = (fetchedInstr >> 8) & ((1 << 4) - 1)
            imm10_5 = (fetchedInstr >> 25) & ((1 << 6) - 1)
            imm12 = (fetchedInstr >> 31) & 1
            imm = (imm11 << 11) | (imm4_1 << 1) | (imm10_5 << 5) | (imm12 << 12)

            # get rs2
            rs2 = (fetchedInstr >> 20) & ((1 << 5) - 1)
            # get rs1
            rs1 = (fetchedInstr >> 15) & ((1 << 5) - 1)
            # get funct3
            funct3 = (fetchedInstr >> 12) & ((1 << 3) - 1)

            # BEQ
            if funct3 == 0b000:
                data_rs1 = self.myRF.readRF(rs1)
                data_rs2 = self.myRF.readRF(rs2)
                if data_rs1 == data_rs2:
                    self.nextState.IF["PC"] = self.state.IF["PC"] + sign_extend(imm, 12)
                    self.state.IF["taken"] = True

            # BNE
            else:
                data_rs1 = self.myRF.readRF(rs1)
                data_rs2 = self.myRF.readRF(rs2)
                if data_rs1 != data_rs2:
                    self.nextState.IF["PC"] = self.state.IF["PC"] + sign_extend(imm, 12)
                    self.state.IF["taken"] = True

        # LW
        elif opcode == 0b0000011:
            # load data from dmem based on an address formed by adding rs1 and imm. 

            # get imm
            imm = fetchedInstr >> 20
            # get rs1
            rs1 = (fetchedInstr >> 15) & ((1 << 5) - 1)
            # get rd
            rd = (fetchedInstr >> 7) & ((1 << 5) - 1)

            self.myRF.writeRF(Reg_addr=rd,
                              Wrt_reg_data=int(self.ext_dmem.readDataMem(
                                  ReadAddress=self.myRF.readRF(rs1) + sign_extend(imm, 11)), 16))

        # SW
        elif opcode == 0b0100011:
            # store data from rs2 to an address formed by adding rs1 and imm. 

            # get imm
            imm11_5 = fetchedInstr >> 25
            imm4_0 = (fetchedInstr >> 7) & ((1 << 5) - 1)
            imm = (imm11_5 << 5) | imm4_0

            # get funct3
            funct3 = fetchedInstr & (((1 << 3) - 1) << 12)
            # get rs1
            rs1 = (fetchedInstr >> 15) & ((1 << 5) - 1)
            # get rd
            rs2 = (fetchedInstr >> 20) & ((1 << 5) - 1)

            self.ext_dmem.writeDataMem(Address=(rs1 + sign_extend(imm, 11)) & ((1 << 32) - 1),
                                       WriteData=self.myRF.readRF(rs2))

        # HALT
        else:
            # stop execution by setting nop to True. 
            self.state.IF["nop"] = True

    # print StateResult_SS.txt
    def printState(self, state, cycle):
        # state output: printState
        # write state after each cycle to StateResult_ss.txt

        printstate = ["State after executing cycle: " + str(cycle) + "\n"] # "-"*70+"\n",    dividing line
        printstate.append("IF.PC: " + str(state.IF["PC"]) + "\n")
        printstate.append("IF.nop: " + str(state.IF["nop"]) + "\n")
        
        if(cycle == 0): 
            perm = "w"
        else: 
            perm = "a"

        with open(self.opFilePath, perm) as wf:
            wf.writelines(printstate)
