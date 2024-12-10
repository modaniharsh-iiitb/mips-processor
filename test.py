#program to test mips processor 
import unittest
from stages_op import *
import pipelined_op as op
from clk import clk

class TestStagesOp(unittest.TestCase):

    #Initializes the registers, instruction memory, data memory, and sets the program counter.
    def setUp(self):
        initReg()
        initIMem()
        initDMem()
        setPC(0x00400000)

    #Tests the control unit for an R-format instruction (e.g., add).
    def test_controlUnit(self):
        self.setUp()
        # Test R-format instruction (e.g., add)
        instr = 0x012A4020  # add $t0, $t1, $t2
        expected_signals = (1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0) # cRegDst, cAluSrc, cMemReg, cRegWr, cMemRd, cMemWr, cBranch, cAluOp, cHiLoWr, cLoRd, cHiRd, cJmp, cLink, cJr
        result = controlUnit(instr)
        self.assertEqual(result, expected_signals)

    def test_aluControlUnit(self):  #Tests the ALU control unit for an addition operation.
        self.setUp()
        # Test addition operation
        opcode = 0
        func = 32  # add
        cAluOp = 1
        expected = 0
        result = aluControlUnit(opcode, func, cAluOp)
        self.assertEqual(result, expected)

    #Tests the ALU control unit for an addition operation.
    def test_alu(self):
        self.setUp()
        # Test addition
        val1 = 5
        val2 = 3
        cAluCont = 0  # add
        expected = 8
        result = alu(val1, val2, cAluCont)
        self.assertEqual(result, expected)

    #Tests the instruction fetch stage.
    def test_fetch(self):
        self.setUp()
        # Test instruction fetch
        instr = fetch()
        self.assertNotEqual(instr, 0)

    #Tests the decoding of an instruction.
    def test_decode(self):
        self.setUp()
        # Test decoding an instruction
        instr = 0x8C890004  # lw $t1, 4($a0)
        cRegDst, cLoRd, cHiRd, cJmp, cJr, cLink = 0, 0, 0, 0, 0, 0
        result = decode(instr, cRegDst, cLoRd, cHiRd, cJmp, cJr, cLink)
        self.assertEqual(result, (0x8C890004, 0, 0, 0, 4, 35, 4, 9, 4194320))

    #Tests the execution of an instruction.
    def test_execute(self):
        self.setUp()
        # Test executing an instruction
        instr = 0x012A4020  # add $t0, $t1, $t2
        reg[9] = 5  # $t1
        reg[10] = 3  # $t2
        cRegDst, cAluSrc, cMemReg, cRegWr, cMemRd, cMemWr, cBranch, cAluOp, cHiLoWr, cLoRd, cHiRd, cJmp, cLink, cJr = controlUnit(instr)
        decoded = decode(instr, cRegDst, cLoRd, cHiRd, cJmp, cJr, cLink)
        instr, pcTemp, rdData1, rdData2, immed, opcode, func, wReg, bTarget = decoded
        result = execute(instr, pcTemp, rdData1, rdData2, immed, opcode, func, wReg, bTarget, cAluOp, cAluSrc, cBranch, cLoRd, cHiRd)
        self.assertEqual(result, (0x012A4020, 0, 3, 0, 8, 8))

    #Tests the memory access stage.
    def test_memory(self):
        self.setUp()
        # Test memory access
        instr = 0xAC890004  # sw $t1, 4($a0)
        reg[8] = 0x10000000
        reg[9] = 64
        cRegDst, cAluSrc, cMemReg, cRegWr, cMemRd, cMemWr, cBranch, cAluOp, cHiLoWr, cLoRd, cHiRd, cJmp, cLink, cJr = controlUnit(instr)
        decoded = decode(instr, cRegDst, cLoRd, cHiRd, cJmp, cJr, cLink)
        instr, pcTemp, rdData1, rdData2, immed, opcode, func, wReg, bTarget = decoded
        instr, pcTemp, rdData2, aluRes1, aluRes2, wReg = execute(instr, pcTemp, rdData1, rdData2, immed, opcode, func, wReg, bTarget, cAluOp, cAluSrc, cBranch, cLoRd, cHiRd)

        result = memory(instr, pcTemp, rdData2, aluRes1, aluRes2, wReg, cMemWr, cMemRd, cMemReg, cLink)
        self.assertEqual(dMem[aluRes2], 0)
        self.assertEqual(dMem[aluRes2 + 1], 0)
        self.assertEqual(dMem[aluRes2 + 2], 0)
        self.assertEqual(dMem[aluRes2 + 3], 64)

    # Tests the register writeback stage.
    def test_writeback(self):
        self.setUp()
        # Test register writeback
        wData = 8
        aluRes1 = 8
        aluRes2 = 0
        wReg = 8  # $t0
        cRegWr = 1
        cHiLoWr = 0
        writeback(wData, aluRes1, aluRes2, wReg, cRegWr, cHiLoWr)
        self.assertEqual(reg[wReg], 8)  #checking if the value is written to the register

    #Tests the store word (sw) instruction.
    def test_store_instruction(self):
        self.setUp()
        # Test store word (sw) instruction
        # sw $t1, 4($t0)
        reg[8] = 0x10010000  # $t0
        reg[9] = 1000         # $t1
        instr = 0xAD090004   # opcode: 43 (sw), base: $t0, rt: $t1, offset: 4
        # Control signals
        cRegDst, cAluSrc, cMemReg, cRegWr, cMemRd, cMemWr, cBranch, \
            cAluOp, cHiLoWr, cLoRd, cHiRd, cJmp, cLink, cJr = controlUnit(instr)
        # Decode
        decoded = decode(instr, cRegDst, cLoRd, cHiRd, cJmp, cJr, cLink)
        instr, pcTemp, rdData1, rdData2, immed, opcode, func, wReg, bTarget = decoded
        # Execute
        executed = execute(instr, pcTemp, rdData1, rdData2, immed, opcode, func,
                        wReg, bTarget, cAluOp, cAluSrc, cBranch, cLoRd, cHiRd)
        instr, pcTemp, rdData2, aluRes1, aluRes2, wReg = executed
        # Memory
        memory(instr, pcTemp, rdData2, aluRes1, aluRes2, wReg,
            cMemWr, cMemRd, cMemReg, cLink)
        # Correctly compute the address
        address = (aluRes1 << 32) | aluRes2
        # Provide default values to avoid NoneType
        # 1000 = 3*256 + 232
        self.assertEqual(dMem[aluRes2], 0)
        self.assertEqual(dMem[aluRes2 + 1], 0)
        self.assertEqual(dMem[aluRes2 + 2], 3)
        self.assertEqual(dMem[aluRes2 + 3], 232)

    #Tests the jump (j), jump and link (jal), and jump register (jr) instructions.
    def test_jump_instruction(self):
        # Test jump (j) instruction
        self.setUp()
        instr = 0x08100010  # j to address 0x00400040 (shifted address)
        # Control signals
        cRegDst, cAluSrc, cMemReg, cRegWr, cMemRd, cMemWr, cBranch, \
            cAluOp, cHiLoWr, cLoRd, cHiRd, cJmp, cLink, cJr = controlUnit(instr)
        # Decode
        decoded = decode(instr, cRegDst, cLoRd, cHiRd, cJmp, cJr, cLink)
        instr, pcTemp, rdData1, rdData2, immed, opcode, func, wReg, bTarget = decoded
        # The PC should now be updated to the jump target
        self.assertEqual(getPC(), 0x00400040)

        # Test jump and link (jal) instruction
        instr = 0x0C100010  # jal to address 0x00400040
        # Control signals
        cRegDst, cAluSrc, cMemReg, cRegWr, cMemRd, cMemWr, cBranch, \
            cAluOp, cHiLoWr, cLoRd, cHiRd, cJmp, cLink, cJr = controlUnit(instr)
        # Decode
        decoded = decode(instr, cRegDst, cLoRd, cHiRd, cJmp, cJr, cLink)
        instr, pcTemp, rdData1, rdData2, immed, opcode, func, wReg, bTarget = decoded
        # The PC should now be updated to the jump target
        self.assertEqual(getPC(), 0x00400040)
        # The return address should be stored in $ra ($31)
        self.assertEqual(wReg, 31)
        # Writeback the return address
        wData = pcTemp
        aluRes1 = 0
        aluRes2 = 0
        cRegWr = 1
        cHiLoWr = 0
        writeback(wData, aluRes1, aluRes2, wReg, cRegWr, cHiLoWr)
        self.assertEqual(reg[31], pcTemp)

        # Test jump register (jr) instruction
        reg[8] = 0x00400040  # $t0 contains the target address
        instr = 0x01100008  # jr $t0
        # Control signals
        cRegDst, cAluSrc, cMemReg, cRegWr, cMemRd, cMemWr, cBranch, \
            cAluOp, cHiLoWr, cLoRd, cHiRd, cJmp, cLink, cJr = controlUnit(instr)
        # Decode
        decoded = decode(instr, cRegDst, cLoRd, cHiRd, cJmp, cJr, cLink)
        instr, pcTemp, rdData1, rdData2, immed, opcode, func, wReg, bTarget = decoded
        # The PC should now be updated to the address in $t0
        self.assertEqual(getPC(), reg[8])
    
    #Tests the load word (lw) instruction.
    def test_load_instruction(self):
        self.setUp()
        # Test load word (lw) instruction
        # lw $t1, 4($t0)
        reg[8] = 0x10000000  # Initialize $t0 with base address
        address = reg[8] + 4
        #Let the 32 bit number be 123, make it byte addressable
        dMem[address+3] = 123  # Set memory at address 0x10000004 to 123
        instr = 0x8D090004   # lw $t1, 4($t0)
        # Control signals
        cRegDst, cAluSrc, cMemReg, cRegWr, cMemRd, cMemWr, cBranch, \
            cAluOp, cHiLoWr, cLoRd, cHiRd, cJmp, cLink, cJr = controlUnit(instr)
        # Decode
        decoded = decode(instr, cRegDst, cLoRd, cHiRd, cJmp, cJr, cLink)
        instr, pcTemp, rdData1, rdData2, immed, opcode, func, wReg, bTarget = decoded
        # Execute
        executed = execute(instr, pcTemp, rdData1, rdData2, immed, opcode, func,
                        wReg, bTarget, cAluOp, cAluSrc, cBranch, cLoRd, cHiRd)
        instr, pcTemp, rdData2, aluRes1, aluRes2, wReg = executed
        # Memory Access
        mem_result = memory(instr, pcTemp, rdData2, aluRes1, aluRes2, wReg,
                            cMemWr, cMemRd, cMemReg, cLink)
        instr, wData, aluRes1, aluRes2, wReg = mem_result
        # Writeback
        writeback(wData, aluRes1, aluRes2, wReg, cRegWr, cHiLoWr)
        # Check that $t1 now contains the value loaded from memory
        self.assertEqual(reg[9], 123)

    #Tests the branch on equal (beq) instruction.
    def test_branch_instruction(self):
        # Test branch on equal (beq) instruction
        # beq $t2, $t3, 4
        self.setUp()
        reg[10] = 5
        reg[11] = 5
        instr = 0x114B0004  # beq $t2, $t3, 4
        cRegDst, cAluSrc, cMemReg, cRegWr, cMemRd, cMemWr, cBranch, cAluOp, cHiLoWr, cLoRd, cHiRd, cJmp, cLink, cJr = controlUnit(instr)
        decoded = decode(instr, cRegDst, cLoRd, cHiRd, cJmp, cJr, cLink)
        instr, pcTemp, rdData1, rdData2, immed, opcode, func, wReg, bTarget = decoded
        instr, pcTemp, rdData2, aluRes1, aluRes2, wReg = execute(instr, pcTemp, rdData1, rdData2, immed, opcode, func, wReg, bTarget, cAluOp, cAluSrc, cBranch, cLoRd, cHiRd)
        result = memory(instr, pcTemp, rdData2, aluRes1, aluRes2, wReg, cMemWr, cMemRd, cMemReg, cLink)
        self.assertEqual(getPC(), 0x400010)
       
#This test ensures that the clk class correctly increments the number of cycles and accurately tracks the time taken for each cycle.
class TestClk(unittest.TestCase):

    #Tests the cycle method of the clk class.
    def test_cycle(self):
        clock = clk(0.95)
        clock.cycle()
        self.assertEqual(clock.noOfCycles(), 1)
        self.assertAlmostEqual(clock.getTimeTaken(), 0.95)

if __name__ == '__main__':
    unittest.main()