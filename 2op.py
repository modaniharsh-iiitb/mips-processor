# pipelined processor

from stages import *
from clk import *

initReg()
initIMem()
initDMem()

# clock of 250 microsecond time period
clock = clk(0.25)

#queue for instructions(with max length 5)

class instrBuffer:
    def __init__(self):
        self.q = [0, 0, 0, 0, 0]
    def add(self, stage):
        self.q.pop()
        self.q.insert(0, stage)
    def bufferDecode(self, IFIDReg):
        instr = self.q[1]
        if instr != 0:
            # stage: instruction decode
            # control signals
            cRegDst, cAluSrc, cMemReg, cRegWr, cMemRd, cMemWr, cBranch, cAluOp, cHiLoWr, cLoRd, cHiRd, cJmp, cLink, cJr = controlUnit(instr)
            # decoded registers and data
            jTarget, rdData1, rdData2, immed, opcode, func, wReg = decode(instr, cRegDst, cLoRd, cHiRd, cJr, cLink)
            return cRegDst, cAluSrc, cMemReg, cRegWr, cMemRd, cMemWr, cBranch, cAluOp, cHiLoWr, cLoRd, cHiRd, cJmp, cLink, cJr, jTarget, rdData1, rdData2, immed, opcode, func, wReg
    def bufferExecute(self, IDEXReg):
        instr = self.q[2]
        if instr != 0:
            cRegDst, cAluSrc, cMemReg, cRegWr, cMemRd, cMemWr, cBranch, cAluOp, cHiLoWr, cLoRd, cHiRd, cJmp, cLink, cJr, jTarget, rdData1, rdData2, immed, opcode, func, wReg = IDEXReg
            jTarget, rdData2, aluRes1, aluRes2 = execute(jTarget, rdData1, rdData2, immed, opcode, func, cAluOp, cAluSrc, cBranch, cLoRd, cHiRd)
            return cRegDst, cAluSrc, cMemReg, cRegWr, cMemRd, cMemWr, cBranch, cAluOp, cHiLoWr, cLoRd, cHiRd, cJmp, cLink, cJr, jTarget, rdData1, rdData2, immed, opcode, func, wReg

#IF/ID pipeline register
IFIDReg = [] #has only instr

#ID/EX pipeline register
IDEXReg = [] #has cRegDst, cAluSrc, cMemReg, cRegWr, cMemRd, cMemWr, cBranch, cAluOp, cHiLoWr, cLoRd, cHiRd, cJmp, cLink, cJr, jTarget, rdData1, rdData2, immed, opcode, func, wReg

#EX/MEM pipeline register
EXMEMReg = []

#MEM/WB pipeline register
MEMWBReg = []

IB = instrBuffer()

while True:
    if (getPC() not in iMem.keys()):
        break
    
    #IF
    instr = fetch()
    IB.add(instr)

    #put necessary buffers in the IF/ID pipeline register

    #ID
    IB.bufferDecode()