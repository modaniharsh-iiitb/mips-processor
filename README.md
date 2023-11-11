# mips-processor

A Python program that simulates the working of a MIPS ISA processor, that includes simulations both with and without pipelining.

## Description of MIPS

MIPS, or Microprocessor without Interlocked Pipeline Stages, is a family of RISC (Reduced Instruction Set Computer) ISAs. It has both 32- and 64-bit variants; however, this project emulates the working of a 32-bit MIPS ISA processor.

The MIPS ISA has a variety of 32-bit instructions, with multiple different formats. It uses 32 CPU registers, each of which store a 32-bit field (known as a **word**), and up to 2<sup>32</sup> memory slots, each of which stores an 8-bit field or a byte.

### Registers

As mentioned before, there are 32 registers in a processor that are used directly by instructions, along with `hi` and `lo` registers that are used to store values when multiplication and division instructions are performed.

Each of the registers has a number which is used to refer to it in the binary MIPS code, which is known as the **register number**. This register number can range from `$0` to `$31`.

Alternatively, **register names** are also given to registers, which are more descriptive of their expected function, and are used in assembly MIPS code.

A `$` precedes both the register number and name.

### Memory

The memory in MIPS is subdivided into various parts that serve multiple purposes, such as the stack, heap, and codespace - however, in this implementation, we need only discuss two main parts of the memory, namely the **instruction memory** and **data memory**.

The instruction memory starts from the address `0x04000000` and contains only instructions, which are 32 bits wide. It is only meaningful to access it via addresses that are multiples of 4. Also, the first hexadecimal digit of the address in the instruction memory must be `0`, or equivalently, the first 4 bits of the address must be `0000`.

The data memory starts from the address `0x10000000` and contains all the values that the running program needs to store. It is byte-addressible and any integer value between `0x10000000` and `0x80000000` is in the instruction memory and meaningful.

### Instructions

Instructions are 32-bit long, and can mainly be categorized into 3 different types, namely **R-format** (register), **I-format** (immediate) and **J-format** (jump) instructions.

#### R-format instructions

These instructions have a 6-bit wide opcode in the beginning, three 5-bit wide fields that describe three different registers, a 5-bit wide field that describes the shift amount and a 6-bit wide field that describes the function field of the instruction.

Since in all R-format instructions, the opcode is `000000`, the 6-bit wide function field is what determines the instruction.

For example, the MIPS instruction

`00000010000010001000100000100000`

translates to

`add $s1, $s0, $t1`

which takes the values in registers `$s0` and `$t1`, adds them, and stores the result in `$s1`.

#### I-format instructions

These instructions have a 6-bit wide opcode in the beginning, two 5-bit wide fields that describe two different registers, and a 16-bit wide field that describes the immediate value used in the instruction.

The 6-bit wide opcode field is what determines the instruction.

For example, the MIPS instruction

`10000001111000000000000000001100`

translates to

`add $t7, $0, 12`

which takes the values in the register `$0`, adds the immediate value `12` to it, and stores the result in `$t7`.

#### J-format instructions

These instructions have a 6-bit wide opcode in the beginning and a 26-bit wide field that describes the address of the instruction to jump to.

The 26-bit wide address is converted into a 32-bit wide address by left shifting the value by 2, and padding it with zeros on the right. Since the codespace of the memory ends before `0x10000000` and the instructions are only word-addressible, each memory location that has an instruction must begin with `0000` and end with `00` in binary, making it possible to condense all jump addresses into 26 bits.

For example, the MIPS instruction

`00001100000000001000111000100000`

translates to

`jal 145536`

by taking the return address field's value (`36384`) and multiplying it by 4 (effectively left-shifting the same by 2) to get the jump address.

### Pipelining

Pipelining is the procedure employed by MIPS and several other ISAs to try and ensure that the various stages of execution of an instruction (e.g. memory access, register file access) are used simultaneously, thereby saving time.

#### Pipeline registers

MIPS makes use of extra registers on the dye, referred to as **pipeline registers**, that store the data that serves as an intermediate to two stages in MIPS.

Since there are 5 broad stages in MIPS (Fetch-Decode-Execute-Memory access-Register Writeback) that are executed in a linear fashion, there are 4 pipeline registers that exist between any two consecutive registers. These are as follows:

- **Fetch/Decode register**
- **Decode/Execute register**
- **Execute/Memory register**
- **Memory/Writeback register**

#### Hazards - structural, control and data hazards

Of course, due to the introduction of pipelining in MIPS, several functions that would work perfectly in MIPS start to show malfunnctions in their operation. There are mainly 3 types of hazards, namely structural hazards, data hazards and control hazards.

- **Structural hazards** are those hazards that occur when the same structure (e.g. register file) is accessed by two different instructions in the same cycle, thereby leading to a risk of corrupted output for both instructions. This can be avoided by separating structures to make them exclusive to one phase of the instruction (e.g. splitting instruction and data memory), or implementing write-read cycles (i.e., writing to the structure in the first cycle, and reading from it in the second).
- **Data hazards** are those hazards that occur when an instruction retrieves incorrect data due to the structures not having been updated by previous instructions while the data is retrieved from the current instruction. To avoid data hazards, both **stalling/NOPing** and **forwarding** are used.
- **Control hazards** are those hazards that occur when incorrect instructions that do not follow irregular program flow (e.g. `j`, `beq`) enter the pipeline stages anyway. **Stalls** can be used preemptively to prevent unnecessary instructions from entering the pipeline, or alternatively **pipeline flushing** can be used to remove the data left behind by unnecessarily running instructions.

#### Resolving hazards - stalling/NOPing, forwarding, pipeline flushing

- **Stalling** is the process of temporarily preventing one of the stages of the MIPS processor from operating, in order for the instruction bearing the stall to be able to obtain values that it may not have obtained correctly had it not waited. Stalls can also be used to prevent instructions that should not be executed from entering the processor at all.
- **NOPing** is a similar procedure, but it involves introducing a NOP (no operation) instruction before the instruction that needs to be stalled so that the latter gets enough time to ensure that no dependencies are left unresolved.
- **Forwarding** is the procedure of sending data from intermediate pipeline registers backwards (i.e. to future instructions) that may need register data that is meant to be overwritten.
- **Pipeline flushing** is the process of "flushing" or invalidating any instruction that has been run since the instruction under scrutiny, and was not meant to run by program design.

## Implementation

### Registers

Registers are stored in the `reg` field in the code, which is a list indexed from `0` to `31` (both inclusive). The index refers to the register number of that register (i.e., `0` for `$0`, `21` for `$s6`, etc.), and the value at that index is the 32-bit field that the register stores (e.g., `reg[25]` would retrieve the value stored by `$t9`).

Also, the `hi` and `lo` registers used in `mult` and `div` operations are implemented with the same name.

### Memory

Instruction memory is represented by the `iMem` dictionary. The keys are addresses of each word and the values are the 32-bit instructions stored in them. For example, `iMem[0x0000000c]` returns the full instruction stored at the 12th (decimal) address in the instruction memory. Instruction memory is only word-addressible, not byte-addressible.

Similarly, data memory is represented by the `dMem` dictionary. The keys are addresses of each byte and the values are the 8-bit fields stored in them. For example, `iMem[0x9000001f]` returns the byte stored at the 2415919135th (decimal) address in the data memory. Data memory is byte-addressible; however, for the purpose of this implementation, none of the features that are a byproduct of its byte-addressibility come in use.

### Instructions

The following instructions, as explained briefly earlier, can be simulated by this processor:

#### R-format

```
Instr   Function
-------------------
jr      001000 (08)
mfhi	010000 (16)
mflo	010010 (18)
mult	011000 (24)
div     011010 (26)
add 	100000 (32)
sub 	100010 (34)
and 	100100 (36)
or  	100101 (37)
xor 	100110 (38)
nor     100111 (39)
slt     101010 (42)
```

#### I-format

```
Instr   Opcode
-------------------
beq 	000100 (04)
bne 	000101 (05)
addi	001000 (08)
lui 	001111 (15)
lw  	100011 (35)
sw  	101011 (43)
```

#### J-format

```
Instr   Opcode
-------------------
j       000010 (02)
jal     000011 (03)
```

### Pipelining

#### Pipeline registers

The following pipelined registers are used in `pipelined_op.py`:

- `IFIDReg`
- `IDEXReg`
- `EXMEMReg`
- `MEMWBReg`

#### Resolving hazards

- The program uses a `forwardingUnit` (defined in the `InstructionBuffer` class) to **forward** data to and from registers if dependencies are detected. The working of the forwarding unit is described in detail in the comments.
- For **stalling**, each pipeline register has a `stall` bit that determines whether its corresponding stage's operation will be stalled in the current cycle. Stalling is used only for load hazards, as ALU hazards can always be resolved using only forwarding.
- Similar to stalling, each pipeline register also has a `valid` bit that determines whether the stage is going to run in the current cycle. This is used for **pipeline flushing**.

### Variables and their meaning

#### Global variables

- `reg`: the register file (list of 32 integers, `reg[i]` represents the value stored in the `$i` register)
- `iMem`: the instruction memory (dictionary, with the key being the address and the corresponsing value being the 32-bit instruction held at that address). It follows MIPS conventions but is not byte-addressible.
- `dMem`: the data memory (similar to above, but the corresponding value to each address is a byte instead of a word). It is byte-addressible.
- `pc`: the program counter (integer). Starts at the base instruction memory location, i.e. `0x04000000`.
- `hi`, `lo`: registers corresponding to `hi` and `lo` as in MIPS, used in multiplication and division operations (integers).
- `clock`: representation of the clock that works with any processor. It has the option to customize its cycle duration, emulate a cycle, return the total number of cycles emulated and the corresponding time taken.

#### Control signals

- `cRegDst`: Signal to select the destination register (i.e., the register to be written into). In case of R-type instructions, the destination register is `rd` and `cRegDst = 1`. Otherwise, the destination register is either irrelevant or `rt` and `cRegDst = 0`.
- `cAluSrc`: Signal to select the source of the second input value to the ALU. In case of R-type instructions, the source is the value of `rt` and `cAluSrc = 0`. In all other instructions, the source is the immediate value `immed` and `cAluSrc = 1`.
- `cMemReg`: Signal to select the source of the data to be written back into the register file. In case of an `lw` instruction, the source is memory and `cMemReg = 1`, otherwise the source is the ALU output and `cMemReg = 0`.
- `cRegWr`: Signal to determine whether any register needs to be written back into. In case of instructions that have an explicit destination register (e.g. `addi`), `cRegWr = 1`, and in case of instructions that do not have a destination register (e.g. `beq`), `cRegWr = 0`.
- `cMemRd`: Signal to determine whether data is being read from the memory. In case of `lw`, `cMemRd = 1`, otherwise `cMemRd = 0`.
- `cMemWr`: Signal to determine whether data is being written to the memory. In case of `sw`, `cMemWr = 1`, otherwise `cMemWr = 0`.
- `cBranch`: Signal to determine whether the program counter should source from the branch adder or itself. In case of `beq` and `bne`, `cBranch = 1`, otherwise `cBranch = 0`.
- `cAluOp`: Signal to determine the source using which the ALU Control Unit should determine the `cAluCont` bits. If the instruction is I-format or J-format, `cAluOp = 0`, otherwise `cAluOp = 0`.
- `cHiLoWr`: Signal to determine whether `hi` and `lo` are being written into. In case of `mult` and `div` instructions, `cHiLoWr = 1`, otherwise `cHiLoWr = 0`.
- `cLoRd`: Signal to determine whether `lo` is being read from. In case of `mflo`, `cLoRd = 1`, otherwise `cLoRd = 0`.
- `cHiRd`: Signal to determine whether `hi` is being read from. In case of `mfhi`, `cHiRd = 1`, otherwise `cHiRd = 0`.
- `cJmp`: Signal to determine whether the instruction will jump. In case of `j`, `jal` and `jr`, `cJmp = 1`, otherwise `cJmp = 0`.

## Running the program

To emulate the non-pipelined processor, ensure you are in the root directory of this project and run the command:

```python non_pipelined_op.py```

Similarly, for the pipelined processor, run the following command:

```python pipelined_op.py```

### Output

Both programs provide the following output:

```
Done executing
No. of cycles: 116
Time taken: 110.2 ms

Value of registers:
$0:     0
$1:     0
$2:     0
$3:     0
$4:     0
$5:     0
$6:     0
$7:     0
$8:     0
$9:     3
$10:    268435456
$11:    268435468
$12:    2
$13:    0
$14:    0
$15:    4
$16:    0
$17:    1
$18:    3
$19:    -1
$20:    1
$21:    1
$22:    0
$23:    0
$24:    3
$25:    268435468
$26:    0
$27:    0
$28:    268435456
$29:    2147479548
$30:    0
$31:    0

Value of data memory:
0x10000000      4
0x10000004      5
0x10000008      3
0x1000000c      3
0x10000010      4
0x10000014      5
0x10000018      0
0x1000001c      0
0x10000020      0
0x10000024      0
0x10000028      0
0x1000002c      0
```

The values of data memory, in addition, are also stored into the `bindata` file.

Note that the value of the number of cycles and time taken changes.

## External References (Outside the material of this course)

- Register numbers and equivalent names: [MIPS Quick Reference, cs.jhu.edu](https://www.cs.jhu.edu/~cs333/reference.html)
- MIPS opcodes: [MIPS Opcode Reference](http://mipsconverter.com/opcodes.html)

## Authors

- IMT2022055 Harsh Modani
- IMT2022102 Md. Owais