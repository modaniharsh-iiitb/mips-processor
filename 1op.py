# non-pipelined processor

from stages import *
from clk import *

initReg()
initIMem()
initDMem()

clock = clk()

for i in iMem:
    print(hex(i), iMem[i], sep='\t')

for i in iMem:
    # stage: instruction fetch
    clock.cycle()
    # next instruction
    instr = fetch()
    print(instr)

    # stage: instruction decode
    clock.cycle()
    # control signals
    cRegDst, cAluSrc, cMemReg, cRegWr, cMemRd, cMemWr, cBranch, cAluOp, cHiLoWr, cLoRd, cHiRd = controlUnit(instr)
    print(cRegDst, cAluSrc, cMemReg, cRegWr, cMemRd, cMemWr, cBranch, cAluOp, cHiLoWr, cLoRd, cHiRd)
    # decoded registers and data
    rdData1, rdData2, immed, opcode, func, wReg = decode(instr, cRegDst, cLoRd, cHiRd)
    print(rdData1, rdData2, immed, opcode, func, wReg)

    # stage: ALU execute
    clock.cycle()
    # values obtained from ALU operations (also takes care of branching)
    rdData2, aluRes1, aluRes2 = execute(rdData1, rdData2, immed, opcode, func, cAluOp, cAluSrc, cBranch, cLoRd, cHiRd)
    print(rdData2, aluRes1, aluRes2)

    # stage: memory access
    clock.cycle()
    # values read or written to memory
    wData, aluRes1, aluRes2 = memory(aluRes1, aluRes2, cMemWr, cMemRd, cMemReg)
    print(wData, aluRes1, aluRes2)

    # stage: register writeback
    clock.cycle()
    # values written back into registers if needed
    writeback(wData, aluRes1, aluRes2, wReg, cRegWr, cHiLoWr)
    
    print()

print('Done executing')
print('No. of cycles:', clock.noOfCycles())
print('Value of registers:')
print('$t1:',reg[9])
print('$s0:',reg[16])
print('$s1:',reg[17])
print('$s2:',reg[18])
print('$s3:',reg[19])