#include "../src/minix8_core.h"

#include <stdio.h>

#define RAM_SIZE MINIX8_RAM_SIZE
#define FLAG_Z MINIX8_FLAG_Z
#define FLAG_C MINIX8_FLAG_C
#define FLAG_N MINIX8_FLAG_N
typedef Minix8Machine Machine;
#define reset minix8_reset
#define step minix8_step

static int failures;

#define CHECK(condition, description) do { \
    if (!(condition)) { \
        fprintf(stderr, "FAIL %s:%d: %s\n", __FILE__, __LINE__, description); \
        failures++; \
    } \
} while (0)

static void test_reset_and_load_immediate(void) {
    Machine m;
    reset(&m);
    m.ram[0] = 0x01; m.ram[1] = 0x7f;
    CHECK(m.sp == 0xffff && m.pc == 0 && m.stack_depth == 0, "reset establishes initial CPU state");
    CHECK(step(&m) == 1, "LDA immediate executes");
    CHECK(m.a == 0x7f && m.pc == 2 && m.cycles == 1, "LDA stores value and advances PC/cycles");
    CHECK(m.flags == 0, "positive nonzero load clears N and Z");
}

static void test_arithmetic_flags(void) {
    Machine m;
    reset(&m); m.a = 0xff; m.b = 1; m.ram[0] = 0x09;
    CHECK(step(&m) == 1 && m.a == 0 && m.flags == (FLAG_Z | FLAG_C), "ADD wraps and sets zero/carry");
    reset(&m); m.a = 0; m.b = 1; m.ram[0] = 0x0a;
    CHECK(step(&m) == 1 && m.a == 0xff && m.flags == FLAG_N, "SUB wraps and records borrow");
    reset(&m); m.a = 7; m.b = 7; m.ram[0] = 0x0e;
    CHECK(step(&m) == 1 && m.a == 7 && m.flags == (FLAG_Z | FLAG_C), "CMP leaves A unchanged and sets equal flags");
}

static void test_memory_and_branch(void) {
    Machine m;
    reset(&m); m.a = 0x55; m.ram[0] = 0x06; m.ram[1] = 0x34; m.ram[2] = 0x12;
    CHECK(step(&m) == 1 && m.ram[0x1234] == 0x55, "STA writes the selected 16-bit address");
    reset(&m); m.ram[0x2345] = 0xa5; m.ram[0] = 0x05; m.ram[1] = 0x45; m.ram[2] = 0x23;
    CHECK(step(&m) == 1 && m.a == 0xa5, "LDA reads the selected 16-bit address");
    reset(&m); m.flags = FLAG_Z; m.ram[0] = 0x10; m.ram[1] = 0x34; m.ram[2] = 0x12;
    CHECK(step(&m) == 1 && m.pc == 0x1234, "JZ branches to the little-endian target");
    reset(&m); m.flags = FLAG_Z; m.ram[0] = 0x11; m.ram[1] = 0x34; m.ram[2] = 0x12;
    CHECK(step(&m) == 1 && m.pc == 3, "JNZ falls through when Z is set");
    reset(&m); m.b = 0x5a; m.ram[0] = 0x08; m.ram[1] = 0xff; m.ram[2] = 0xff;
    CHECK(step(&m) == 1 && m.ram[0xffff] == 0x5a, "STB writes to the last valid RAM byte");
    reset(&m); m.ram[0xffff] = 0xc3; m.ram[0] = 0x07; m.ram[1] = 0xff; m.ram[2] = 0xff;
    CHECK(step(&m) == 1 && m.b == 0xc3, "LDB reads from the last valid RAM byte");
}

static void test_logic_shifts_and_moves(void) {
    Machine m;
    reset(&m); m.a = 0xf0; m.b = 0x0f; m.flags = FLAG_C; m.ram[0] = 0x0b;
    CHECK(step(&m) == 1 && m.a == 0 && m.flags == FLAG_Z, "AND clears carry and sets zero");
    reset(&m); m.a = 0xf0; m.b = 0x0f; m.ram[0] = 0x0c;
    CHECK(step(&m) == 1 && m.a == 0xff && m.flags == FLAG_N, "OR sets negative from result high bit");
    reset(&m); m.a = 0xf0; m.b = 0x0f; m.ram[0] = 0x0d;
    CHECK(step(&m) == 1 && m.a == 0xff && m.flags == FLAG_N, "XOR produces expected byte");
    reset(&m); m.a = 0xff; m.flags = FLAG_C; m.ram[0] = 0x1b;
    CHECK(step(&m) == 1 && m.a == 0 && m.flags == (FLAG_C | FLAG_Z), "INC wraps and preserves carry");
    reset(&m); m.a = 0; m.ram[0] = 0x1c;
    CHECK(step(&m) == 1 && m.a == 0xff && m.flags == FLAG_N, "DEC wraps to negative byte");
    reset(&m); m.a = 0x80; m.ram[0] = 0x1d;
    CHECK(step(&m) == 1 && m.a == 0 && m.flags == (FLAG_C | FLAG_Z), "SHL moves the top bit into carry");
    reset(&m); m.a = 1; m.ram[0] = 0x1e;
    CHECK(step(&m) == 1 && m.a == 0 && m.flags == (FLAG_C | FLAG_Z), "SHR moves the low bit into carry");
    reset(&m); m.a = 0x12; m.b = 0x23; m.c = 0x34; m.d = 0x45;
    m.ram[0] = 0x1f; step(&m); CHECK(m.a == 0x23, "MOV A,B copies register");
    reset(&m); m.a = 0x12; m.ram[0] = 0x20; step(&m); CHECK(m.b == 0x12, "MOV B,A copies register");
    reset(&m); m.c = 0x34; m.ram[0] = 0x21; step(&m); CHECK(m.a == 0x34, "MOV A,C copies register");
    reset(&m); m.a = 0x12; m.ram[0] = 0x22; step(&m); CHECK(m.c == 0x12, "MOV C,A copies register");
    reset(&m); m.d = 0x45; m.ram[0] = 0x23; step(&m); CHECK(m.a == 0x45, "MOV A,D copies register");
    reset(&m); m.a = 0x12; m.ram[0] = 0x24; step(&m); CHECK(m.d == 0x12, "MOV D,A copies register");
}

static void test_call_return_and_stack_faults(void) {
    Machine m;
    reset(&m); m.ram[0] = 0x14; m.ram[1] = 0x10; m.ram[2] = 0x00; m.ram[0x10] = 0x15;
    CHECK(step(&m) == 1 && m.pc == 0x10 && m.stack_depth == 2, "CALL transfers control and pushes return address");
    CHECK(step(&m) == 1 && m.pc == 3 && m.stack_depth == 0, "RET restores return address and stack depth");
    reset(&m); m.a = 0x69; m.ram[0] = 0x16; m.ram[1] = 0x17;
    CHECK(step(&m) == 1 && m.stack_depth == 1, "PUSH stores one byte");
    m.a = 0;
    CHECK(step(&m) == 1 && m.a == 0x69 && m.stack_depth == 0, "POP restores one byte");
    reset(&m); m.ram[0] = 0x17;
    CHECK(step(&m) == -1 && m.faulted && m.halted, "POP on empty stack faults safely");
    reset(&m); m.ram[0] = 0x15;
    CHECK(step(&m) == -1 && m.faulted && m.halted, "RET on empty stack faults safely");
    reset(&m); m.ram[0] = 0x16; m.stack_depth = RAM_SIZE;
    CHECK(step(&m) == -1 && m.faulted, "PUSH beyond full stack faults safely");
}

static void test_invalid_opcode_and_halt(void) {
    Machine m;
    reset(&m); m.ram[0] = 0xff;
    CHECK(step(&m) == -1 && m.faulted, "undefined opcode is reported as a CPU fault");
    reset(&m); m.ram[0] = 0x1a;
    CHECK(step(&m) == 1 && m.halted, "HLT stops the CPU");
    uint64_t cycles = m.cycles;
    CHECK(step(&m) == 0 && m.cycles == cycles, "halted CPU does not advance");
}

int main(void) {
    test_reset_and_load_immediate();
    test_arithmetic_flags();
    test_memory_and_branch();
    test_logic_shifts_and_moves();
    test_call_return_and_stack_faults();
    test_invalid_opcode_and_halt();
    if (failures) {
        fprintf(stderr, "%d core test(s) failed.\n", failures);
        return 1;
    }
    puts("Core tests passed.");
    return 0;
}
