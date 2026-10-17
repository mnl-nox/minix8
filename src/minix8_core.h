#ifndef MINIX8_CORE_H
#define MINIX8_CORE_H

#include <stdint.h>

#define MINIX8_RAM_SIZE 65536u

enum {
    MINIX8_FLAG_Z = 1,
    MINIX8_FLAG_C = 2,
    MINIX8_FLAG_N = 4
};

typedef struct {
    uint8_t ram[MINIX8_RAM_SIZE];
    uint8_t a, b, c, d, flags;
    uint16_t pc, sp;
    int halted;
    int faulted;
    uint32_t stack_depth;
    uint64_t cycles;
} Minix8Machine;

void minix8_reset(Minix8Machine *machine);
/* Returns 1 when an instruction executes, 0 when halted, and -1 on CPU/I/O fault. */
int minix8_step(Minix8Machine *machine);

#endif
