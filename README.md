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
jr?     001000 (08)
mfhi?	010000 (16)
mflo?	010010 (18)
mult?	011000 (24)
div?    011010 (26)
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
jal?    000011 (03)
```

## Running the program

To emulate the non-pipelined processor, ensure you are in the root directory of this project and run the command:

```python 1op.py```

Similarly, for the pipelined processor, run the following command:

```python 2op.py```

### Output

## External References (Outside the material of this course)

- Register numbers and equivalent names: [MIPS Quick Reference, cs.jhu.edu](https://www.cs.jhu.edu/~cs333/reference.html)
- MIPS opcodes: [MIPS Opcode Reference](http://mipsconverter.com/opcodes.html)