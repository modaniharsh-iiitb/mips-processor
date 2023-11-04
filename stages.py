# register file
reg = []
# instruction memory
iMem = {}
# data memory
dMem = {}
# program counter
pc = 0
# hi, lo registers (depends on whether we're implementing mult and div)
hi, lo = 0, 0

##### initializations

def initReg():
    for _ in range(32):
        reg.append(0)

def initIMem():
    # instruction memory starts at location 0x04000000
    i = 0x04000000
    with open('bincode', 'r') as f:
        for line in f.readlines():
            iMem[i] = int(line, 2)
            i += 4

def initDMem():
    # data memory starts at location 0x10000000
    i = 0x10000000
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
    # function is last 6 bits of instruction
    func = instr << 26 >> 26
    cRegDst1 = int(func == 8 or func == 16 or func == 18)
    cRegDst2 = int(opcode == 0)
    cRegDst2 = 0 if cRegDst1 else cRegDst2
    cRegDst = 2*cRegDst1+cRegDst2
    cAluSrc = int(opcode == 35 or opcode == 43)
    cMemReg = int(opcode != 0)
    cRegWr = int(opcode == 0 or opcode == 35)
    cMemRd = int(opcode == 35)
    cMemWr = int(opcode == 43)
    cBranch = int(opcode == 4)
    cAluOp1 = int(opcode == 0)
    cAluOp2 = int(opcode == 4)
    cAluOp = 2*cAluOp1+cAluOp2
    cHiLoWr = int(func == 24 or func == 26)
    # CU returns 9 signals - of which cAluOp and cRegDst are 2 bits wide
    return cRegDst, cAluSrc, cMemReg, cRegWr, cMemRd, cMemWr, cBranch, cAluOp, cHiLoWr

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
        elif (func == 37):
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
        # xor
        elif (func == 38):
            cAluContr = 5
        # mul
        elif (func == 24):
            cAluContr = 6
        # div
        elif (func == 26):
            cAluContr = 7
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
    # xor
    elif (cAluContr == 5):
        return val1 ^ val2
    # mul
    elif (cAluContr == 6):
        return val1 * val2
    # div
    elif (cAluContr == 7):
        return (val1 % val2, val1 // val2)

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
    # however, immediate must be sign-extended
    immed = (instr << 16) >> 16
    # in the event that the leading bit of the immediate is 1,
    # the immediate has a sign extension with 1s padded to the 
    # left instead of 0s
    if ((immed >> 15) == 1):
        immed = 0x10000-immed
    # func = instr[5:0]
    func = (instr << 26) >> 26
    wReg = rdReg3
    if (cRegDst == 0):
        wReg = rdReg2
    elif (cRegDst == 2):
        wReg = rdReg1
    rdData1 = reg[rdReg1]
    rdData2 = reg[rdReg2]
    # this stage returns the two register read data, the immediate value, 
    # the function value and writeback register (will be ignored
    # by the next stage if not needed)
    return rdData1, rdData2, immed, func, wReg

def execute(rdData1, rdData2, immed, func, cAluOp, cAluSrc, cBranch):
    global pc
    cAluContr = aluControlUnit(cAluOp, func)
    val1 = rdData1
    val2 = immed if cAluSrc else rdData2
    aluResult = alu(val1, val2, cAluContr)
    if (type(aluResult) == 'int'):
        aluRes1 = aluResult >> 32
        aluRes2 = aluResult - (aluRes1 << 32)
    else:
        aluRes1 = aluResult[0]
        aluRes2 = aluResult[1]
    cZero = int(aluResult == 0)
    bTarget = pc+(immed << 2)
    if (cBranch & cZero):
        pc = bTarget
    # this stage returns the result of ALU calculation and whether it
    # is equal to zero, and also checks if the new PC should be equal to
    # the branch target
    return rdData2, aluRes1, aluRes2

def memory(rdData2, aluRes1, aluRes2, cMemWr, cMemRd, cMemReg):
    global dMem
    address = aluRes1
    wData = rdData2
    # reading
    if (cMemRd):
        rData = 0
        # piecing together the 32-bit integer using the different
        # byte-wide values at each address
        for i in range(4):
            rData += (dMem[address+i] << (24-8*(i)))
        wData = rData if cMemReg else rdData2
    # writing
    elif (cMemWr):
        # splitting the 32-bit integer into byte-wide values
        # and storing them at each address
        for i in range(4):
            dMem[address+i] = (rData << (8*i)) >> 24
    # this stage only returns the content to be written back into a register
    # (will be ignored by the next stage if not needed)
    return wData, aluRes1, aluRes2

def writeback(wData, aluRes1, aluRes2, wReg, cRegWr, cHiLoWr):
    global reg, hi, lo
    if (cRegWr):
        # writes data into the register
        reg[wReg] = wData
    if (cHiLoWr):
        hi = aluRes1
        lo = aluRes2

##### testing

# function to print the data memory (by word, not by bytes)
def printDMem():
    for k in dMem.keys():
        if (k%4 == 0):
            address = hex(k)
            data = 0
            # piecing together the 32-bit integer using the different
            # byte-wide values at each address
            for i in range(4):
                data += (dMem[k+i] << (24-8*(i)))
            print(address, data, sep='\t')