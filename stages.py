# register file
reg = []
# instruction memory
iMem = {}
# data memory
dMem = {}
# program counter
pc = 0

##### initializations

def initReg():
    for _ in range(32):
        reg.append(0)

def initIMem():
    # instruction memory starts at location 0x0
    i = 0
    with open('bincode', 'r') as f:
        for line in f.readlines():
            iMem[i] = int(line, 2)
            i += 4

def initDMem():
    # data memory starts at location 0x90000000
    i = 0x90000000
    with open('bindata', 'r') as f:
        for line in f.readlines():
            # for byte addressibility
            dMem[i] = int(line[0:8], 2)
            dMem[i+1] = int(line[8:16], 2)
            dMem[i+2] = int(line[16:24], 2)
            dMem[i+3] = int(line[24:32], 2)
            i += 4

##### units

def controlUnit(instr):
    # opcode is first 6 bits of instruction
    opcode = instr >> 26
    cRegDst = int(opcode == 0)
    cAluSrc = int(opcode == 35 or opcode == 43)
    cMemReg = int(opcode != 0)
    cRegWr = int(opcode == 0 or opcode == 35)
    cMemRd = int(opcode == 35)
    cMemWr = int(opcode == 43)
    cBranch = int(opcode == 4)
    cAluOp1 = int(opcode == 0)
    cAluOp2 = int(opcode == 4)
    cAluOp = 2*cAluOp1+cAluOp2
    cJmp = int(opcode == 2)
    # CU returns 9 signals - of which cAluOp is 2 bits wide
    return cRegDst, cAluSrc, cMemReg, cRegWr, cMemRd, cMemWr, cBranch, cAluOp, cJmp

def aluControlUnit(cAluOp, func):
    cAluContr = 0
    # lw or sw - uses addition only
    if (cAluOp == 0):
        cAluContr = 2
    # branch - uses subtraction only
    elif (cAluOp == 1):
        cAluContr = 3
    # r-format instruction - evaluates cAluContr using func
    else:
        # and
        if (func == 36):
            cAluContr = 0
        # or
        elif (func == 38):
            cAluContr = 1
        # add
        elif (func == 32):
            cAluContr = 2
        # sub
        elif (func == 34):
            cAluContr = 3
        # slt
        elif (func == 42):
            cAluContr = 4
    return cAluContr

def alu(val1, val2, cAluContr):
    # and
    if (cAluContr == 0):
        return val1 & val2
    # or
    elif (cAluContr == 1):
        return val1 | val2
    # add
    elif (cAluContr == 2):
        return val1 + val2
    # sub
    elif (cAluContr == 3):
        return val1 - val2
    # slt
    elif (cAluContr == 4):
        return int(val1 < val2)

##### stages

def fetch():
    global pc, iMem
    # the instruction to be executed
    instr = iMem[pc]
    # this stage returns the instruction
    return instr

def decode(instr, cRegDst):
    global reg
    # opcode = instr[31:26]
    opcode = instr >> 26
    # rdReg1 = instr[25:21]
    rdReg1 = (instr << 6) >> 27
    # rdReg2 = instr[20:16]
    rdReg2 = (instr << 11) >> 27
    # rdReg3 = instr[15:11]
    rdReg3 = (instr << 16) >> 27
    # immed = instr[15:0]
    immed = (instr << 16) >> 16
    # func = instr[5:0]
    func = (instr << 26) >> 26
    wReg = rdReg3 if cRegDst else rdReg2
    rdData1 = reg[rdReg1]
    rdData2 = reg[rdReg2]
    # this stage returns the two register read data, the immediate value, 
    # the function value and writeback register (will be ignored
    # by the next stage if unneeded)
    return rdData1, rdData2, immed, func, wReg

def execute(rdData1, rdData2, immed, func, cAluOp, cAluSrc):
    global pc
    cAluContr = aluControlUnit(cAluOp, func)
    val1 = rdData1
    val2 = immed if cAluSrc else rdData2
    aluResult = alu(val1, val2, cAluContr)
    cZero = int(aluResult == 0)
    bTarget = pc+(immed << 2)
    # this stage returns the result of ALU calculation and whether it
    # is equal to zero, and also the branch target (will be ignored
    # by the next stage if unneeded)
    return aluResult, cZero, bTarget

def memory(aluResult, cMemWr, cMemRd, cMemReg):
    global dMem

def writeback():
    pass

##### testing

def printDMem():
    for k in dMem.keys():
        if (k%4 == 0):
            address = hex(k)
            data = 0
            for i in range(4):
                data += (dMem[k+i] << (32-8*(i+1)))
            print(address, data, sep='\t')

initDMem()
printDMem()