# register file
reg = []
# instruction memory
iMem = {}
# data memory
dMem = {}
# program counter
pc = 0x04000000
# hi, lo registers (depends on whether we're implementing mult and div)
hi, lo = 0, 0

##### getters

def getPC():
    global pc
    return pc

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
    i = bin(instr)[2:].zfill(32)
    # opcode is first 6 bits of instruction
    opcode = int(i[0:6], 2)
    # function is last 6 bits of instruction
    func = int(i[26:], 2)
    cRegDst1 = int(opcode in [2, 3])
    cRegDst2 = int(opcode == 0)
    cRegDst2 = 0 if cRegDst1 else cRegDst2
    cRegDst = 2*cRegDst1+cRegDst2
    cAluSrc = int(opcode not in [0, 4])
    cMemReg = int(opcode == 35)
    cRegWr = int(opcode != 43 and func not in [24, 26])
    cMemRd = int(opcode == 35)
    cMemWr = int(opcode == 43)
    cBranch = int(opcode == 4)
    cAluOp = int(opcode == 0)
    cHiLoWr = int(func in [24, 26])
    cLoRd = int(func == 18)
    cHiRd = int(func == 16)
    # CU returns 11 signals - of which cRegDst is 2 bits wide
    return cRegDst, cAluSrc, cMemReg, cRegWr, cMemRd, cMemWr, cBranch, cAluOp, cHiLoWr, cLoRd, cHiRd

def aluControlUnit(cAluOp, opcode, func):
    cAluCont = 0
    # i-format or j-format instruction - uses opcode to determine cAluCont
    if (cAluOp == 0):
        # addi, lw or sw - use addition
        if (opcode in [8, 35, 43]):
            cAluCont = 0
        # beq and bne - use subtraction
        elif (opcode in [4, 5]):
            cAluCont = 1
        # lui - uses left shifting by 16
        elif (opcode == 15):
            cAluCont = 9
        # j and jal - use left shifting by 2
        elif (opcode in [2, 3]):
            cAluCont = 10
    # r-format instruction - evaluates cAluCont using func
    else:
        # add
        if (func == 32):
            cAluCont = 0
        # sub
        elif (func == 34):
            cAluCont = 1
        # and
        elif (func == 36):
            cAluCont = 2
        # or
        elif (func == 37):
            cAluCont = 3
        # xor
        elif (func == 38):
            cAluCont = 4
        # nor
        elif (func == 39):
            cAluCont = 5
        # slt
        elif (func == 42):
            cAluCont = 6
        # mult
        elif (func == 24):
            cAluCont = 7
        # div
        elif (func == 26):
            cAluCont = 8
    return cAluCont

def alu(val1, val2, cAluCont):
    # add
    if (cAluCont == 0):
        return val1 + val2
    # sub
    elif (cAluCont == 1):
        return val1 - val2
    # and
    elif (cAluCont == 2):
        return val1 & val2
    # or
    elif (cAluCont == 3):
        return val1 | val2
    # xor
    elif (cAluCont == 4):
        return val1 ^ val2
    # nor
    elif (cAluCont == 5):
        return ~(val1 | val2)
    # slt
    elif (cAluCont == 6):
        return int(val1 < val2)
    # mult
    elif (cAluCont == 7):
        return val1 * val2
    # div
    elif (cAluCont == 8):
        return (val1 % val2) << 32 + (val1 // val2)
    # sll by 16
    elif (cAluCont == 9):
        return val1 << 16
    # sll by 2
    elif (cAluCont == 10):
        return val1 << 2

##### stages

def fetch():
    global pc, iMem
    # the instruction to be executed
    instr = iMem[pc]
    # program counter incremented
    pc += 4
    # this stage returns the instruction
    return instr

def decode(instr, cRegDst, cLoRd, cHiRd):
    i = bin(instr)[2:].zfill(32)
    global reg
    # opcode = instr[31:26]
    opcode = int(i[0:6], 2)
    # rdReg1 = instr[25:21]
    rdReg1 = int(i[6:11], 2)
    # rdReg2 = instr[20:16]
    rdReg2 = int(i[11:16], 2)
    # rdReg3 = instr[15:11]
    rdReg3 = int(i[16:21], 2)
    # immed = instr[15:0]
    # however, immediate must be sign-extended
    immed = int(i[16:], 2)
    # in the event that the leading bit of the immediate is 1,
    # the immediate has a sign extension with 1s padded to the 
    # left instead of 0s
    if ((immed >> 15) == 1):
        immed = -(0x10000-immed)
    # func = instr[5:0]
    func = int(i[26:], 2)
    wReg = rdReg3
    if (cRegDst == 0):
        wReg = rdReg2
    elif (cRegDst == 2):
        wReg = rdReg1
    rdData1 = reg[rdReg1]
    rdData2 = reg[rdReg2]
    if (cLoRd):
        rdData2 = lo
    elif (cHiRd):
        rdData2 = hi
    # this stage returns the two register read data, the immediate value, 
    # the function value and writeback register (will be ignored
    # by the next stage if not needed)
    return rdData1, rdData2, immed, opcode, func, wReg

def execute(rdData1, rdData2, immed, opcode, func, cAluOp, cAluSrc, cBranch, cLoRd, cHiRd):
    global pc
    cAluCont = aluControlUnit(cAluOp, opcode, func)
    val1 = rdData1
    val2 = immed if cAluSrc else rdData2
    aluResult = alu(val1, val2, cAluCont)
    aluRes1 = aluResult >> 32
    aluRes2 = aluResult - (aluRes1 << 32)
    if (cLoRd or cHiRd):
        aluRes2 = rdData2
    cZero = int(aluResult == 0)
    bTarget = pc+(immed << 2)
    if (cBranch and cZero):
        print('My manz looped')
        pc = bTarget
    # this stage returns the result of ALU calculation and whether it
    # is equal to zero, and also checks if the new PC should be equal to
    # the branch target
    return rdData2, aluRes1, aluRes2

def memory(rdData2, aluRes1, aluRes2, cMemWr, cMemRd, cMemReg):
    global dMem
    # forming the address out of aluRes2
    address = aluRes2
    wData = aluRes2
    # reading from memory
    if (cMemRd):
        rData = 0
        for i in range(4):
            rData += (dMem[address+i] << (24-8*i))
        wData = rData if cMemReg else rdData2
    # writing to memory
    elif (cMemWr):
        wData = rdData2
        wDStr = bin(wData)[2:].zfill(32)
        for i in range(4):
            dMem[address+i] = int(wDStr[8*i:8*i+8])

    return wData, aluRes1, aluRes2

def writeback(wData, aluRes1, aluRes2, wReg, cRegWr, cHiLoWr):
    global reg, hi, lo
    if (cRegWr):
        # writes data into the register
        reg[wReg] = wData
    if (cHiLoWr):
        # writes data into hi and lo
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