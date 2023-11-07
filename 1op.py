# non-pipelined processor

from stages import *
from clk import *

initReg()
initIMem()
initDMem()

clock = clk()
i = 1

while True:
    if (getPC() not in iMem.keys()):
        break

    # stage: instruction fetch
    clock.cycle()
    # next instruction
    # print('PC:',hex(getPC())[2:])
    lineNo = ((getPC()-0x00400000)//4)+1
    # print('Line no:',lineNo)
    instr = fetch()
    # print(bin(instr)[2:].zfill(32))

    # stage: instruction decode
    # control signals
    cRegDst, cAluSrc, cMemReg, cRegWr, cMemRd, cMemWr, cBranch, cAluOp, cHiLoWr, cLoRd, cHiRd, cJmp, cLink, cJr = controlUnit(instr)
    # print(cRegDst, cAluSrc, cMemReg, cRegWr, cMemRd, cMemWr, cBranch, cAluOp, cHiLoWr, cLoRd, cHiRd, cJmp, cLink, cJr)
    # decoded registers and data
    jTarget, rdData1, rdData2, immed, opcode, func, wReg = decode(instr, cRegDst, cLoRd, cHiRd, cJmp, cJr, cLink)
    # print(jTarget, rdData1, rdData2, immed, opcode, func, wReg)

    # stage: ALU execute
    # values obtained from ALU operations (also takes care of branching)
    jTarget, rdData2, aluRes1, aluRes2, wReg = execute(jTarget, rdData1, rdData2, immed, opcode, func, wReg, cAluOp, cAluSrc, cBranch, cLoRd, cHiRd)
    # print(jTarget, rdData2, aluRes1, aluRes2, wReg)

    # stage: memory access
    # values read or written to memory
    wData, aluRes1, aluRes2, pcTemp, wReg = memory(jTarget, rdData2, aluRes1, aluRes2, wReg, cMemWr, cMemRd, cMemReg)
    # print(wData, aluRes1, aluRes2, pcTemp, wReg)

    # stage: register writeback
    # values written back into registers if needed
    writeback(wData, aluRes1, aluRes2, pcTemp, wReg, cRegWr, cHiLoWr, cLink)
    
    # print()

print('Done executing')
print('No. of cycles:', clock.noOfCycles())
print('Value of registers:')
print()
printReg()
print()
print('Value of data memory:')
printDMem()

commitToMem()