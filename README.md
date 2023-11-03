# mips-processor

A Python program that simulates the working of a MIPS ISA processor, that includes simulations both with and without pipelining.

## Description of MIPS

MIPS, or Microprocessor without Interlocked Pipeline Stages, is a family of RISC (Reduced Instruction Set Computer) ISAs. It has both 32- and 64-bit variants; however, this project emulates the working of a 32-bit MIPS ISA processor.

The MIPS ISA has a variety of 32-bit instructions, with multiple different formats. It uses 32 CPU registers, each of which store a 32-bit field (known as a **word**), and up to 2<sup>32</sup> memory slots, each of which stores an 8-bit field or a byte.

### Instructions

Instructions are 32-bit long, and can mainly be categorized into 3 different types, namely **R-format** (register), **I-format** (immediate) and **J-format** (jump) instructions.

#### R-format instructions

These instructions have a 6-bit wide opcode in the beginning, three 5-bit wide fields that describe three different registers, a 5-bit wide field that describes the shift amount and a 6-bit wide field that describes the function field of the instruction.

Since in all R-format instructions, the opcode is `000000`, the 6-bit wide function field is what determines the instruction.

For example, the instruction

`00000010000010001000100000100000`

translates to

`add $s1, $s0, $t1`

which takes the values in registers `$s0` and `$t1`, adds them, and stores the result in `$s1`.

## Implementation

### Registers

### Memory

### Instructions

### Output

## Running the program

To emulate the non-pipelined processor, ensure you are in the root directory of this project and run the command:

```python 1op.py```

Similarly, for the pipelined processor, run the following command:

```python 2op.py```

