# register file
reg = []
# instruction memory
iMem = {}
# data memory
dMem = {}
# program counter
pc = 0x00400000
# hi, lo registers
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
    i = 0x00400000
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
    cRegDst = int(opcode == 0)
    cAluSrc = int(opcode not in [0, 4, 5])
    cMemReg = int(opcode == 35)
    cRegWr = int(opcode not in [2, 4, 5, 43] and 
                 (func not in [8, 24, 26] if opcode == 0 else 1))
    cMemRd = int(opcode == 35)
    cMemWr = int(opcode == 43)
    cBranch = int(opcode in [4, 5])
    cAluOp = int(opcode == 0)
    cHiLoWr = int(func in [24, 26])
    cLoRd = int(func == 18)
    cHiRd = int(func == 16)
    cJmp = int((opcode == 0 and func == 8) or (opcode in [2, 3]))
    cLink = int(opcode == 3)
    cJr = int(opcode == 0 and func == 8)
    # CU returns 14 signals
    return (cRegDst, cAluSrc, cMemReg, cRegWr, cMemRd, cMemWr, cBranch, 
            cAluOp, cHiLoWr, cLoRd, cHiRd, cJmp, cLink, cJr)

def aluControlUnit(opcode, func, cAluOp):
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
    if (val1 > (1 << 31)):
        val1 = -(0x10000000-val1)
    if (val2 > (1 << 31)):
        val2 = -(0x10000000-val2)
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
        return val2 << 16
    # sll by 2
    elif (cAluCont == 10):
        return val2 << 2

##### stages

def fetch():
    #resolve comments
    global pc, iMem
    
    # the instruction to be executed
    if (pc in iMem.keys()):
        instr = iMem[pc]
        pc += 4
        return instr
    else:
        return 0
    # program counter incremented
    # this stage returns the instruction

def decode(instr, cRegDst, cLoRd, cHiRd, cJmp, cJr, cLink):
    global reg, pc

    # instruction in binary string format - useful for 
    # extracting components
    i = bin(instr)[2:].zfill(32)
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
    # jTarget = instr[26:0] << 2
    jTarget = int(i[6:], 2) << 2
    wReg = rdReg2
    if (cRegDst):
        wReg = rdReg3
    rdData1 = reg[rdReg1]
    rdData2 = reg[rdReg2]
    # in the event that the leading bit of the data is 1,
    # the immediate has a sign extension with 1s padded to the 
    # left instead of 0s
    if (rdData1 > (1 << 31)):
        rdData1 = -(0x10000000-rdData1)
    if (rdData2 > (1 << 31)):
        rdData2 = -(0x10000000-rdData2)
    if (cJr):
        jTarget = rdData1
    # if the instruction is jal, then the $ra register
    # needs to be written back to
    if (cLink):
        wReg = 31
    if (cLoRd):
        rdData2 = lo
    elif (cHiRd):
        rdData2 = hi
    # jumping is evaluated in the decode stage for the sake of 
    # better pipelining
    pcTemp = 0
    if (cJmp):
        pcTemp = pc
        pc = jTarget
    
    bTarget = pc+(immed << 2)

    # this stage returns the two register read data, the immediate value, 
    # the function value and writeback register (will be ignored
    # by the next stage if not needed)
    return instr, pcTemp, rdData1, rdData2, immed, opcode, func, wReg, bTarget

def execute(instr, pcTemp, rdData1, rdData2, immed, opcode, func, wReg, bTarget, cAluOp, 
            cAluSrc, cBranch, cLoRd, cHiRd):
    global pc

    cAluCont = aluControlUnit(opcode, func, cAluOp)
    # 1st value of ALU operations always comes from the rs register
    val1 = rdData1
    # 2nd value of ALU operations is either the immediate for I-format 
    # instructions or the rt register value for R-format instructions
    val2 = immed if cAluSrc else rdData2
    aluResult = alu(val1, val2, cAluCont)
    if (aluResult > 0):
        # split into two results, because mult and div give longer than
        # 32-bit answers
        aluRes1 = aluResult >> 32
        aluRes2 = aluResult - (aluRes1 << 32)
    else:
        aluRes1 = 0
        aluRes2 = aluResult

    # if the instruction is mflo or mfhi, then the result is just what is
    # read from HI or LO respectively
    if (cLoRd or cHiRd):
        aluRes2 = rdData2
    cZero = int(aluResult == 0)
    if (cBranch and cZero):
        pc = bTarget
    # this stage returns the result of ALU calculation and whether it
    # is equal to zero, and also checks if the new PC should be equal to
    # the branch target
    return instr, pcTemp, rdData2, aluRes1, aluRes2, wReg

def memory(instr, pcTemp, rdData2, aluRes1, aluRes2, wReg, cMemWr, cMemRd, cMemReg, cLink):
    global dMem, pc

    # forming the address out of aluRes2
    address = aluRes2
    wData = aluRes2 if (not cLink) else pcTemp
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
            dMem[address+i] = int(wDStr[(8*i):(8*i+8)], 2)
    
    
    return instr, wData, aluRes1, aluRes2, wReg

def writeback(wData, aluRes1, aluRes2, wReg, cRegWr, cHiLoWr):
    global reg, hi, lo

    if (cRegWr):
        # writes data into the register
        reg[wReg] = wData
    if (cHiLoWr):
        # writes data into hi and lo
        hi = aluRes1
        lo = aluRes2

##### utility

# function to s the data memory (by word, not by bytes)
def printDMem():
    global dMem

    for k in dMem.keys():
        if (k%4 == 0):
            address = hex(k)
            data = 0
            # piecing together the 32-bit integer using the different
            # byte-wide values at each address
            for i in range(4):
                data += (dMem[k+i] << (24-8*(i)))
            print(address, data, sep='\t')
    
# function to print the register values
def printReg():
    global reg

    for i in range(32):
        print(f'${i}:\t{reg[i]}')

# function to write the data memory into the file
def commitToMem():
    global dMem

    maxAddress = max(list(dMem.keys()))
    with open('bindata', 'w') as f:
        address = 0x10000000
        while True:
            if (address > maxAddress):
                break
            if (address not in dMem.keys()):
                f.write('0'*32+'\n')
            else:
                if (address != 0x10000000):
                    f.write('\n')
                for i in range(4):
                    f.write(bin(dMem[address+i])[2:].zfill(8))
            address += 4