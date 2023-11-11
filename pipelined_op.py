# pipelined processor

from stages_op import *
from clk import *

initReg()
initIMem()
initDMem()

# clock of 250 microsecond time period
clock = clk(0.25)

# IF/ID pipeline register
IFIDReg = {'valid': 0, 'stall': 0, 'lineNo': 0}

# ID/EX pipeline register
IDEXReg = {'valid': 0, 'stall': 0, 'lineNo': 0}

# EX/MEM pipeline register
EXMEMReg = {'valid': 0, 'stall': 0, 'lineNo': 0}

# MEM/WB pipeline register
MEMWBReg = {'valid': 0, 'stall': 0, 'lineNo': 0}

# a class used to simulate the pipeline register
class instrBuffer:
    def __init__(self):
        pass

    # simulating the fetch stage of the pipelined operation
    def bufferFetch(self):
        global IFIDReg, IDEXReg

        if not IDEXReg['valid'] or (IDEXReg['valid'] and not IDEXReg['stall']):
            IFIDReg.update({'lineNo': (getPC()-int(0x400000))//4+1})
            # new instruction
            instr = fetch()
            # put fetch result in IFIDReg
            fetchOutput = [instr]
            IFIDReg.update({'valid': 1, 'fetchOutput': fetchOutput})
            print('IF:')
            print(bin(IFIDReg['fetchOutput'][0])[2:].zfill(32))
            print(IFIDReg)
            # returns instr to check for program termination
            return instr
        
        elif IDEXReg['stall']:
            IDEXReg['stall'] = 0

        return IFIDReg['fetchOutput'][0]
    
    def bufferDecode(self):
        global IFIDReg, IDEXReg, EXMEMReg

        # decode on instr in IFIDReg
        if IFIDReg['valid']:
            instr, = IFIDReg['fetchOutput'] # unpack instr
            if instr != 0:
                # control signals
                cRegDst, cAluSrc, cMemReg, cRegWr, cMemRd, cMemWr, cBranch, cAluOp, cHiLoWr, cLoRd, cHiRd, cJmp, cLink, cJr = controlUnit(instr)
                controlUnitOutput = list([cRegDst, cAluSrc, cMemReg, cRegWr, cMemRd, cMemWr, cBranch, cAluOp, cHiLoWr, cLoRd, cHiRd, cJmp, cLink, cJr])
                # decoded registers and data
                decodeOutput = list(decode(instr, cRegDst, cLoRd, cHiRd, cJmp, cJr, cLink))
                # put decode result in IDEXReg
                IDEXReg.update({'valid': 1, 'controlUnitOutput': controlUnitOutput, 'decodeOutput': decodeOutput})

                # this stage (the stalling unit) determines whether the pipelined registers need to stall, 
                # based on the values of instructions and control signals received from pipeline registers
                #  in the front
                if EXMEMReg['valid']:
                    EXMEMcMemReg = EXMEMReg['controlUnitOutput'][2]
                    EXMEMinstr = EXMEMReg['executeOutput'][0]
                    # turns on stall if the EXMEM instruction is lw
                    if EXMEMcMemReg:
                        EXMEMRd = bin(EXMEMinstr)[2:].zfill(32)[11:16]
                        IDEXRs = bin(instr)[2:].zfill(32)[6:11]
                        IDEXRt = bin(instr)[2:].zfill(32)[11:16]
                        if EXMEMRd in (IDEXRs, IDEXRt):
                            IDEXReg['stall'] = 1
                            print(f'Turned on stall bcoz {EXMEMRd} and {IDEXRs} and also {IDEXRt}')
                    
                print('ID:')
                IDEXReg.update({'lineNo': IFIDReg['lineNo']})
                print(IDEXReg)
            
        else:
            print('ID: invalid')
            IDEXReg['valid'] = 0
        
    def bufferExecute(self):
        global IFIDReg, IDEXReg, EXMEMReg

        # execute on instr in IDEXReg
        if IDEXReg['valid'] and not IDEXReg['stall']:
            # control signals
            cRegDst, cAluSrc, cMemReg, cRegWr, cMemRd, cMemWr, cBranch, cAluOp, cHiLoWr, cLoRd, cHiRd, cJmp, cLink, cJr = IDEXReg['controlUnitOutput']
            instr, pcTemp, rdData1, rdData2, immed, opcode, func, wReg, bTarget = IDEXReg['decodeOutput']
            instr, pcTemp, rdData2, aluRes1, aluRes2, wReg = execute(instr, pcTemp, rdData1, rdData2, immed, opcode, func, wReg, bTarget, cAluOp, cAluSrc, cBranch, cLoRd, cHiRd)
            if cBranch and (aluRes2 == 0):
                IFIDReg['valid'] = 0
                IDEXReg['valid'] = 0
            # executed data and registers
            executeOutput = list([instr, pcTemp, rdData2, aluRes1, aluRes2, wReg])
            # put execute result in EXMEMReg
            EXMEMReg.update({'valid': 1, 'controlUnitOutput': IDEXReg['controlUnitOutput'], 'executeOutput': executeOutput})
            print('EX:')
            EXMEMReg.update({'lineNo': IDEXReg['lineNo']})
            print(EXMEMReg)

        elif IDEXReg['stall']:
            EXMEMReg['stall'] = 1
            IDEXReg['stall'] = 0
            print('EX: stalled')

        else:
            print('EX: invalid')
            EXMEMReg['valid'] = 0

    def bufferMemory(self):
        global EXMEMReg, MEMWBReg

        # memory stage on instr in EXMEMReg
        if EXMEMReg['valid'] and not EXMEMReg['stall']:
            # control signals
            cRegDst, cAluSrc, cMemReg, cRegWr, cMemRd, cMemWr, cBranch, cAluOp, cHiLoWr, cLoRd, cHiRd, cJmp, cLink, cJr = EXMEMReg['controlUnitOutput']
            instr, pcTemp, rdData2, aluRes1, aluRes2, wReg = EXMEMReg['executeOutput']
            instr, wData, aluRes1, aluRes2, wReg = memory(instr, pcTemp, rdData2, aluRes1, aluRes2, wReg, cMemWr, cMemRd, cMemReg, cLink)
            # memory data and registers
            memoryOutput = list([instr, wData, aluRes1, aluRes2, wReg])
            # put execute results in MEMWBReg
            MEMWBReg.update({'valid': 1, 'controlUnitOutput': EXMEMReg['controlUnitOutput'], 'memoryOutput': memoryOutput})
            print('MEM:')
            MEMWBReg.update({'lineNo': EXMEMReg['lineNo']})
            print(MEMWBReg)

        elif EXMEMReg['stall']:
            MEMWBReg['stall'] = 1
            EXMEMReg['stall'] = 0
            print('MEM: stalled')

        else:
            print('MEM: invalid')
            MEMWBReg['valid'] = 0

    def bufferWriteback(self):
        global MEMWBReg

        # writeback stage on instr in MEMWBReg
        if MEMWBReg['valid'] and not MEMWBReg['stall']:
            # control signals
            cRegDst, cAluSrc, cMemReg, cRegWr, cMemRd, cMemWr, cBranch, cAluOp, cHiLoWr, cLoRd, cHiRd, cJmp, cLink, cJr = MEMWBReg['controlUnitOutput']
            instr, wData, aluRes1, aluRes2, wReg = MEMWBReg['memoryOutput']
            writeback(wData, aluRes1, aluRes2, wReg, cRegWr, cHiLoWr)
            print('WB:')
            print(MEMWBReg)

        else:
            MEMWBReg['stall'] = 0
            print('WB: invalid or stalled')

    # the forwarding unit is the mechanism that enables data to be forwarded from one instruction to the other if any 
    # dependencies are found. it resolves dependencies coming from both the EXMEM and MEMWB registers, and does so by checking 
    # if the destination register of the past instruction is the same as one of the source registers in the current IDEX 
    # register. 
    # 
    # it also gives a preference to the more recently updated EXMEM register, as from the perspective of the binary code, it
    # is a more recently executed instruction that will have a more recently updated value.
    def forwardingUnit(self):
        global IDEXReg, EXMEMReg, MEMWBReg
        if IDEXReg['valid']:
            IDEXinstr = IDEXReg['decodeOutput'][0]

            if MEMWBReg['valid']:
                MEMWBcRegDst, MEMWBcRegWr = MEMWBReg['controlUnitOutput'][0], MEMWBReg['controlUnitOutput'][3]
                MEMWBinstr, MEMWBwData = MEMWBReg['memoryOutput'][0], MEMWBReg['memoryOutput'][1]
                if (MEMWBcRegWr):
                    a, b = (16, 21) if MEMWBcRegDst else (11, 16)
                    if bin(MEMWBinstr)[2:].zfill(32)[a:b] == bin(IDEXinstr)[2:].zfill(32)[6:11]:
                        IDEXrdData1 = MEMWBwData
                        IDEXReg['decodeOutput'][2] = IDEXrdData1
                        print(int(bin(IDEXinstr)[2:].zfill(32)[6:11], 2))
                        print('Forwarding used from two instructions before')
                        print('New value of register:',IDEXrdData1)
                    if bin(MEMWBinstr)[2:].zfill(32)[a:b] == bin(IDEXinstr)[2:].zfill(32)[11:16]:
                        IDEXrdData2 = MEMWBwData
                        IDEXReg['decodeOutput'][3] = IDEXrdData2
                        print(int(bin(IDEXinstr)[2:].zfill(32)[11:16], 2))
                        print('Forwarding used from two instructions before')
                        print('New value of register:',IDEXrdData2)

            if EXMEMReg['valid']:
                EXMEMcRegDst, EXMEMcMemReg, EXMEMcRegWr = EXMEMReg['controlUnitOutput'][0], EXMEMReg['controlUnitOutput'][2], EXMEMReg['controlUnitOutput'][3]
                EXMEMinstr, EXMEMaluRes2 = EXMEMReg['executeOutput'][0], EXMEMReg['executeOutput'][4]
                if (EXMEMcRegWr and not EXMEMcMemReg):
                    a, b = (16, 21) if EXMEMcRegDst else (11, 16)
                    if bin(EXMEMinstr)[2:].zfill(32)[a:b] == bin(IDEXinstr)[2:].zfill(32)[6:11]:
                        IDEXrdData1 = EXMEMaluRes2
                        IDEXReg['decodeOutput'][2] = IDEXrdData1
                        print(int(bin(IDEXinstr)[2:].zfill(32)[6:11], 2))
                        print('Forwarding used from one instruction before')
                        print('New value of register:',IDEXrdData1)
                    if bin(EXMEMinstr)[2:].zfill(32)[a:b] == bin(IDEXinstr)[2:].zfill(32)[11:16]:
                        IDEXrdData2 = EXMEMaluRes2
                        IDEXReg['decodeOutput'][3] = IDEXrdData2
                        print(int(bin(IDEXinstr)[2:].zfill(32)[11:16], 2))
                        print('Forwarding used from one instruction before')
                        print('New value of register:',IDEXrdData2)


IB = instrBuffer()
c = 0

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
        c += 1
    else:
        c = 0
    if (c == 5):
        break

    IB.forwardingUnit()

    clock.cycle()
    print()
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