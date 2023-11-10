# non-pipelined processor

from stages_op import *
from clk import *

initReg()
initIMem()
initDMem()

# clock of 950 microsecond time period
clock = clk(0.95)

while True:

    # stage: instruction fetch
    clock.cycle()
    print('Instruction no:',(i+1))
    lineNo = ((getPC()-0x00400000)//4)+1
    print('Line no:',lineNo)
    # next instruction
    instr = fetch()
    # invalid pc fetch; therefore terminate the program
    if (instr == 0):
        break
    print(bin(instr)[2:].zfill(32))

    # stage: instruction decode
    # control signals
    cRegDst, cAluSrc, cMemReg, cRegWr, cMemRd, cMemWr, cBranch, cAluOp, cHiLoWr, cLoRd, cHiRd, cJmp, cLink, cJr = controlUnit(instr)
    print(cRegDst, cAluSrc, cMemReg, cRegWr, cMemRd, cMemWr, cBranch, cAluOp, cHiLoWr, cLoRd, cHiRd, cJmp, cLink, cJr)
    # decoded registers and data
    instr, pcTemp, rdData1, rdData2, immed, opcode, func, wReg, bTarget = decode(instr, cRegDst, cLoRd, cHiRd, cJmp, cJr, cLink)
    print(instr, pcTemp, rdData1, rdData2, immed, opcode, func, wReg)

    # stage: ALU execute
    # values obtained from ALU operations (also takes care of branching)
    instr, pcTemp, rdData2, aluRes1, aluRes2, wReg = execute(instr, pcTemp, rdData1, rdData2, immed, opcode, func, wReg, bTarget, cAluOp, cAluSrc, cBranch, cLoRd, cHiRd)
    print(instr, pcTemp, rdData2, aluRes1, aluRes2, wReg)

    # stage: memory access
    # values read or written to memory
    instr, wData, aluRes1, aluRes2, wReg = memory(instr, pcTemp, rdData2, aluRes1, aluRes2, wReg, cMemWr, cMemRd, cMemReg, cLink)
    print(instr, wData, aluRes1, aluRes2, wReg)

    # stage: register writeback
    # values written back into registers if needed
    writeback(wData, aluRes1, aluRes2, wReg, cRegWr, cHiLoWr)
    
    print()

print('Done executing')
print('No. of cycles:', clock.noOfCycles())
print('Time taken:',round(clock.getTimeTaken(), 2),'ms')
print()
print('Value of registers:')
printReg()
print()
print('Value of data memory:')
printDMem()

commitToMem()