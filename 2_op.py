# pipelined processor

from stages_op import *
from clk import *

initReg()
initIMem()
initDMem()

# clock of 250 microsecond time period
clock = clk(0.25)

# queue for instructions(with max length 5)

# IF/ID pipeline register
IFIDReg = {'valid' : 0} # has only instr

# ID/EX pipeline register
IDEXReg = {'valid' : 0} # has cRegDst, cAluSrc, cMemReg, cRegWr, cMemRd, cMemWr, cBranch, cAluOp, cHiLoWr, cLoRd, cHiRd, cJmp, cLink, cJr, jTarget, rdData1, rdData2, immed, opcode, func, wReg

# EX/MEM pipeline register
EXMEMReg = {'valid' : 0}

# MEM/WB pipeline register
MEMWBReg = {'valid' : 0}

class instrBuffer:
    def __init__(self):
        pass

    def bufferFetch(self):
        global IFIDReg
        # fetch new instruction
        instr = fetch()
        # put fetch result in IFIDReg
        content = [instr]
        IFIDReg.update({'valid' : 1, 'content' : content})
    
    def bufferDecode(self):
        # decode on instr in IFIDReg
        if IFIDReg['valid']:
            instr, = IFIDReg['content']
            if instr != 0:
                # stage: instruction decode
                # control signals
                cRegDst, cAluSrc, cMemReg, cRegWr, cMemRd, cMemWr, cBranch, cAluOp, cHiLoWr, cLoRd, cHiRd, cJmp, cLink, cJr = controlUnit(instr)
                controlUnitOutput = list(cRegDst, cAluSrc, cMemReg, cRegWr, cMemRd, cMemWr, cBranch, cAluOp, cHiLoWr, cLoRd, cHiRd, cJmp, cLink, cJr)
                # decoded registers and data
                decodeOutput = list(decode(instr, cRegDst, cLoRd, cHiRd, cJmp, cJr, cLink))
                IDEXReg.udpate({'valid' : 1, 'controlUnitOutput' : controlUnitOutput, 'decodeOutput': decodeOutput})
        
    def bufferExecute(self):
        # execute on instr in IDEXReg
        if IDEXReg['valid']:
            cRegDst, cAluSrc, cMemReg, cRegWr, cMemRd, cMemWr, cBranch, cAluOp, cHiLoWr, cLoRd, cHiRd, cJmp, cLink, cJr = IDEXReg['controlUnitOutput']
            pcTemp, rdData1, rdData2, immed, opcode, func, wReg = IDEXReg['decodeOutput']
            pcTemp, rdData2, aluRes1, aluRes2, wReg = execute(pcTemp, rdData1, rdData2, immed, opcode, func, wReg, cAluOp, cAluSrc, cBranch, cLoRd, cHiRd)
            executeOutput = list(pcTemp, rdData2, aluRes1, aluRes2, wReg)
            EXMEMReg.update({'valid' : 1, 'controlUnitOutput' : IDEXReg['controlUnitOutput'], 'executeOutput' : executeOutput})

    def bufferMemory(self):
        # memory stage on instr in EXMEMReg
        if EXMEMReg['valid']:
            cRegDst, cAluSrc, cMemReg, cRegWr, cMemRd, cMemWr, cBranch, cAluOp, cHiLoWr, cLoRd, cHiRd, cJmp, cLink, cJr = EXMEMReg['controlUnitOutput']
            pcTemp, rdData2, aluRes1, aluRes2, wReg = EXMEMReg['executeOutput']
            wData, aluRes1, aluRes2, wReg = memory(pcTemp, rdData2, aluRes1, aluRes2, wReg, cMemWr, cMemRd, cMemReg, cLink)
            memoryOutput = list(wData, aluRes1, aluRes2, wReg)
            MEMWBReg.update({'valid' : 1, 'controlUnitOutput' : EXMEMReg['controlUnitOutput'], 'memoryOutput' : memoryOutput})

    def bufferWriteback(self):
        # writeback stage on instr in MEMWBReg
        if MEMWBReg['valid']:
            cRegDst, cAluSrc, cMemReg, cRegWr, cMemRd, cMemWr, cBranch, cAluOp, cHiLoWr, cLoRd, cHiRd, cJmp, cLink, cJr = MEMWBReg['controlUnitOutput']
            wData, aluRes1, aluRes2, wReg = MEMWBReg['memoryOutput']
            writeback(wData, aluRes1, aluRes2, wReg, cRegWr, cHiLoWr)

IB = instrBuffer()

while True:
    if (getPC() not in iMem.keys()):
        break
    
    # IF
    IB.bufferFetch(IFIDReg)
    
    # ID
    IB.bufferDecode()