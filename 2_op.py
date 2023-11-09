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
IFIDReg = {'valid': 0, 'stall': 0, 'instr': 0} # has only instr

# ID/EX pipeline register
IDEXReg = {'valid': 0, 'stall': 0, 'instr': 0} # has cRegDst, cAluSrc, cMemReg, cRegWr, cMemRd, cMemWr, cBranch, cAluOp, cHiLoWr, cLoRd, cHiRd, cJmp, cLink, cJr, jTarget, rdData1, rdData2, immed, opcode, func, wReg

# EX/MEM pipeline register
EXMEMReg = {'valid': 0, 'stall': 0, 'instr': 0}

# MEM/WB pipeline register
MEMWBReg = {'valid': 0, 'stall': 0, 'instr': 0}

class instrBuffer:
    def __init__(self):
        pass

    def bufferFetch(self):
        global IFIDReg
        # fetch new instruction
        IFIDReg.update({'instr': (getPC()-int(0x400000))//4+1})
        instr = fetch()
        # put fetch result in IFIDReg
        content = [instr]
        IFIDReg.update({'valid': 1, 'content': content})
        print('IF:')
        print(bin(IFIDReg['content'][0])[2:].zfill(32))
        print(IFIDReg)
        return instr
    
    def bufferDecode(self):
        global IFIDReg, IDEXReg
        # decode on instr in IFIDReg
        if IFIDReg['valid']:
            instr, = IFIDReg['content'] # unpack instr
            if instr != 0:
                # stage: instruction decode
                # control signals
                cRegDst, cAluSrc, cMemReg, cRegWr, cMemRd, cMemWr, cBranch, cAluOp, cHiLoWr, cLoRd, cHiRd, cJmp, cLink, cJr = controlUnit(instr)
                controlUnitOutput = list([cRegDst, cAluSrc, cMemReg, cRegWr, cMemRd, cMemWr, cBranch, cAluOp, cHiLoWr, cLoRd, cHiRd, cJmp, cLink, cJr])
                # decoded registers and data
                decodeOutput = list(decode(instr, cRegDst, cLoRd, cHiRd, cJmp, cJr, cLink))
                IDEXReg.update({'valid': 1, 'controlUnitOutput': controlUnitOutput, 'decodeOutput': decodeOutput})
                print('ID:')
                IDEXReg.update({'instr': IFIDReg['instr']})
                print(IDEXReg)
            # if decodeOutput[4] == lw ka opcode:
            # 
        else:
            print('ID: invalid')
            IDEXReg['valid'] = 0
        
    def bufferExecute(self):
        global IFIDReg, IDEXReg, EXMEMReg
        # execute on instr in IDEXReg
        if IDEXReg['valid']:
            cRegDst, cAluSrc, cMemReg, cRegWr, cMemRd, cMemWr, cBranch, cAluOp, cHiLoWr, cLoRd, cHiRd, cJmp, cLink, cJr = IDEXReg['controlUnitOutput']
            pcTemp, rdData1, rdData2, immed, opcode, func, wReg, bTarget = IDEXReg['decodeOutput']
            pcTemp, rdData2, aluRes1, aluRes2, wReg = execute(pcTemp, rdData1, rdData2, immed, opcode, func, wReg, bTarget, cAluOp, cAluSrc, cBranch, cLoRd, cHiRd)
            if cBranch and (aluRes2 == 0):
                IFIDReg['valid'] = 0
                IDEXReg['valid'] = 0
            executeOutput = list([pcTemp, rdData2, aluRes1, aluRes2, wReg])
            EXMEMReg.update({'valid': 1, 'controlUnitOutput': IDEXReg['controlUnitOutput'], 'executeOutput': executeOutput})
            print('EX:')
            EXMEMReg.update({'instr': IDEXReg['instr']})
            print(EXMEMReg)
        else:
            print('EX: invalid')
            EXMEMReg['valid'] = 0

    def bufferMemory(self):
        global EXMEMReg, MEMWBReg
        # memory stage on instr in EXMEMReg
        if EXMEMReg['valid']:
            cRegDst, cAluSrc, cMemReg, cRegWr, cMemRd, cMemWr, cBranch, cAluOp, cHiLoWr, cLoRd, cHiRd, cJmp, cLink, cJr = EXMEMReg['controlUnitOutput']
            pcTemp, rdData2, aluRes1, aluRes2, wReg = EXMEMReg['executeOutput']
            wData, aluRes1, aluRes2, wReg = memory(pcTemp, rdData2, aluRes1, aluRes2, wReg, cMemWr, cMemRd, cMemReg, cLink)
            memoryOutput = list([wData, aluRes1, aluRes2, wReg])
            MEMWBReg.update({'valid': 1, 'controlUnitOutput': EXMEMReg['controlUnitOutput'], 'memoryOutput': memoryOutput})
            print('MEM:')
            MEMWBReg.update({'instr': EXMEMReg['instr']})
            print(MEMWBReg)
        else:
            print('MEM: invalid')
            MEMWBReg['valid'] = 0

    def bufferWriteback(self):
        global MEMWBReg
        # writeback stage on instr in MEMWBReg
        if MEMWBReg['valid']:
            cRegDst, cAluSrc, cMemReg, cRegWr, cMemRd, cMemWr, cBranch, cAluOp, cHiLoWr, cLoRd, cHiRd, cJmp, cLink, cJr = MEMWBReg['controlUnitOutput']
            wData, aluRes1, aluRes2, wReg = MEMWBReg['memoryOutput']
            writeback(wData, aluRes1, aluRes2, wReg, cRegWr, cHiLoWr)
            print('WB:')
            print(MEMWBReg)
        else:
            print('WB: invalid')

    def forwardRegisters(self):
        global IDEXReg, EXMEMReg, MEMWBReg
        if MEMWBReg['valid']:
            IDEXinstr = IDEXReg['instr']
            MEMWBcRegDst, MEMWBcMemReg, MEMWBcRegWr = MEMWBReg['controlUnitOutput'][0], MEMWBReg['controlUnitOutput'][2], MEMWBReg['controlUnitOutput'][3]
            MEMWBwData = MEMWBReg['memoryOutput'][0]
            MEMWBinstr = MEMWBReg['instr']
            if (MEMWBcRegWr and MEMWBcMemReg):
                a, b = (16, 21) if MEMWBcRegDst else (11, 16)
                if bin(MEMWBinstr)[2:].zfill(32)[a:b] == bin(IDEXinstr)[2:].zfill(32)[6:11]:
                    IDEXrdData1 = MEMWBwData
                    IDEXReg['decodeOutput'][1] = IDEXrdData1
                    print(bin(MEMWBinstr)[2:].zfill(32)[a:b], bin(IDEXinstr)[2:].zfill(32)[6:11])
                    print('Forwarding used LW style')
                if bin(MEMWBinstr)[2:].zfill(32)[a:b] == bin(IDEXinstr)[2:].zfill(32)[11:16]:
                    IDEXrdData2 = MEMWBwData
                    IDEXReg['decodeOutput'][2] = IDEXrdData2
                    print(bin(MEMWBinstr)[2:].zfill(32)[a:b], bin(IDEXinstr)[2:].zfill(32)[11:16])
                    print('Forwarding used LW style')
        if EXMEMReg['valid']:
            IDEXinstr = IDEXReg['instr']
            EXMEMcRegDst, EXMEMcMemReg, EXMEMcRegWr = EXMEMReg['controlUnitOutput'][0], EXMEMReg['controlUnitOutput'][2], EXMEMReg['controlUnitOutput'][3]
            aluRes2 = EXMEMReg['executeOutput'][3]
            EXMEMinstr = EXMEMReg['instr']
            if (EXMEMcRegWr and not EXMEMcMemReg):
                a, b = (16, 21) if EXMEMcRegDst else (11, 16)
                if bin(EXMEMinstr)[2:].zfill(32)[a:b] == bin(IDEXinstr)[2:].zfill(32)[6:11]:
                    IDEXrdData1 = aluRes2
                    IDEXReg['decodeOutput'][1] = IDEXrdData1
                    print(bin(EXMEMinstr)[2:].zfill(32)[a:b], bin(IDEXinstr)[2:].zfill(32)[6:11])
                    print('Forwarding used other style')
                if bin(EXMEMinstr)[2:].zfill(32)[a:b] == bin(IDEXinstr)[2:].zfill(32)[11:16]:
                    IDEXrdData2 = aluRes2
                    IDEXReg['decodeOutput'][2] = IDEXrdData2
                    print(bin(EXMEMinstr)[2:].zfill(32)[a:b], bin(IDEXinstr)[2:].zfill(32)[11:16])
                    print('Forwarding used LW style')


IB = instrBuffer()

while True:

    # WB
    IB.bufferWriteback()

    # MEM
    IB.bufferMemory()

    # EX
    IB.bufferExecute()
    
    # ID
    IB.bufferDecode()

    # IF
    if (IB.bufferFetch() == 0):
        break

    IB.forwardRegisters()

    clock.cycle()
    print()
    print()

print('No. of cycles:', clock.noOfCycles())
print('Time taken:',round(clock.getTimeTaken(), 2),'ms')

printDMem()

commitToMem()