# non-pipelined processor

from stages import *
from clk import *

initReg()
initIMem()
initDMem()

# clock of 950 microsecond time period
clock = clk(0.95)
i = 1

# f = open('notes1.txt', 'w')

for i in range(200):

    # stage: instruction fetch
    clock.cycle()
    # next instruction
    # print('PC:',hex(getPC())[2:])
    print('Instruction no:',(i+1))
    # f.write(f'Instruction no: {str(i+1)} \n')
    lineNo = ((getPC()-0x00400000)//4)+1
    print('Line no:',lineNo,end='')
    # f.write(f'Line no: {lineNo}\n')
    if (lineNo in range(18, 26)):
        print(' ########################################')
    else:
        print()
    instr = fetch()
    if (instr == 0):
        break
    print(bin(instr)[2:].zfill(32))
    # f.write(bin(instr)[2:].zfill(32)+'\n')

    # stage: instruction decode
    # control signals
    cRegDst, cAluSrc, cMemReg, cRegWr, cMemRd, cMemWr, cBranch, cAluOp, cHiLoWr, cLoRd, cHiRd, cJmp, cLink, cJr = controlUnit(instr)
    print(cRegDst, cAluSrc, cMemReg, cRegWr, cMemRd, cMemWr, cBranch, cAluOp, cHiLoWr, cLoRd, cHiRd, cJmp, cLink, cJr)
    # decoded registers and data
    pcTemp, rdData1, rdData2, immed, opcode, func, wReg = decode(instr, cRegDst, cLoRd, cHiRd, cJmp, cJr, cLink)
    print(pcTemp, rdData1, rdData2, immed, opcode, func, wReg)

    # stage: ALU execute
    # values obtained from ALU operations (also takes care of branching)
    pcTemp, rdData2, aluRes1, aluRes2, wReg = execute(pcTemp, rdData1, rdData2, immed, opcode, func, wReg, cAluOp, cAluSrc, cBranch, cLoRd, cHiRd)
    print(pcTemp, rdData2, aluRes1, aluRes2, wReg)

    # stage: memory access
    # values read or written to memory
    wData, aluRes1, aluRes2, wReg = memory(pcTemp, rdData2, aluRes1, aluRes2, wReg, cMemWr, cMemRd, cMemReg, cLink)
    print(wData, aluRes1, aluRes2, wReg)

    # stage: register writeback
    # values written back into registers if needed
    writeback(wData, aluRes1, aluRes2, wReg, cRegWr, cHiLoWr)
    
    # f.write(f'$t5: {reg[13]}\n')
    # f.write(f'$0: {reg[0]}\n')
    print()

print('Done executing')
print('No. of cycles:', clock.noOfCycles())
print('Time taken:',round(clock.getTimeTaken(), 2),'ms')
print('Value of registers:')
print()
printReg()
print()
print('Value of data memory:')
printDMem()

commitToMem()