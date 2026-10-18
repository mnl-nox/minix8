#include "minix8_core.h"

#include <stdio.h>
#include <string.h>

static uint8_t fetch8(Minix8Machine *m) { return m->ram[m->pc++]; }
static uint16_t fetch16(Minix8Machine *m) {
    uint16_t lo = fetch8(m);
    return (uint16_t)(lo | ((uint16_t)fetch8(m) << 8));
}
static void set_zn(Minix8Machine *m, uint8_t v) {
    m->flags = (uint8_t)((m->flags & MINIX8_FLAG_C) | (v == 0 ? MINIX8_FLAG_Z : 0) | (v & 0x80 ? MINIX8_FLAG_N : 0));
}
static int push(Minix8Machine *m, uint8_t v) {
    if (m->stack_depth >= MINIX8_RAM_SIZE) return 0;
    m->ram[m->sp--] = v;
    m->stack_depth++;
    return 1;
}
static int pop(Minix8Machine *m, uint8_t *v) {
    if (m->stack_depth == 0) return 0;
    *v = m->ram[++m->sp];
    m->stack_depth--;
    return 1;
}
static int push16(Minix8Machine *m, uint16_t v) {
    if (m->stack_depth > MINIX8_RAM_SIZE - 2) return 0;
    return push(m, (uint8_t)(v >> 8)) && push(m, (uint8_t)v);
}
static int pop16(Minix8Machine *m, uint16_t *v) {
    uint8_t lo, hi;
    if (m->stack_depth < 2) return 0;
    if (!pop(m, &lo) || !pop(m, &hi)) return 0;
    *v = (uint16_t)(lo | ((uint16_t)hi << 8));
    return 1;
}
static int cpu_fault(Minix8Machine *m, uint16_t at, const char *reason) {
    fprintf(stderr, "Erro da CPU em %04X: %s\n", at, reason);
    m->halted = 1;
    m->faulted = 1;
    return -1;
}

static int output_byte(const Minix8Machine *m, uint8_t byte) {
    if (m->raw_output || byte == '\n' || byte == '\r' || byte == '\t' || (byte >= 0x20 && byte != 0x7f))
        return putchar(byte);
    return printf("\\x%02X", byte) < 0 ? EOF : 0;
}

void minix8_reset(Minix8Machine *m) {
    if (m == NULL) return;
    memset(m, 0, sizeof(*m));
    m->sp = 0xffff;
}

int minix8_step(Minix8Machine *m) {
    if (m == NULL) return -1;
    if (m->halted) return 0;
    uint16_t at = m->pc;
    uint8_t op = fetch8(m), v;
    uint16_t addr;
    unsigned result;
    m->cycles++;
    switch (op) {
    case 0x00: break;
    case 0x01: m->a = fetch8(m); set_zn(m, m->a); break;
    case 0x02: m->b = fetch8(m); set_zn(m, m->b); break;
    case 0x03: m->c = fetch8(m); set_zn(m, m->c); break;
    case 0x04: m->d = fetch8(m); set_zn(m, m->d); break;
    case 0x05: addr = fetch16(m); m->a = m->ram[addr]; set_zn(m, m->a); break;
    case 0x06: addr = fetch16(m); m->ram[addr] = m->a; break;
    case 0x07: addr = fetch16(m); m->b = m->ram[addr]; set_zn(m, m->b); break;
    case 0x08: addr = fetch16(m); m->ram[addr] = m->b; break;
    case 0x09: result = (unsigned)m->a + m->b; m->a = (uint8_t)result; m->flags = result > 255 ? MINIX8_FLAG_C : 0; set_zn(m, m->a); break;
    case 0x0a: v = m->a; m->a = (uint8_t)(m->a - m->b); m->flags = v >= m->b ? MINIX8_FLAG_C : 0; set_zn(m, m->a); break;
    case 0x0b: m->a &= m->b; m->flags &= (uint8_t)~MINIX8_FLAG_C; set_zn(m, m->a); break;
    case 0x0c: m->a |= m->b; m->flags &= (uint8_t)~MINIX8_FLAG_C; set_zn(m, m->a); break;
    case 0x0d: m->a ^= m->b; m->flags &= (uint8_t)~MINIX8_FLAG_C; set_zn(m, m->a); break;
    case 0x0e: v = (uint8_t)(m->a - m->b); m->flags = m->a >= m->b ? MINIX8_FLAG_C : 0; set_zn(m, v); break;
    case 0x0f: m->pc = fetch16(m); break;
    case 0x10: addr = fetch16(m); if (m->flags & MINIX8_FLAG_Z) m->pc = addr; break;
    case 0x11: addr = fetch16(m); if (!(m->flags & MINIX8_FLAG_Z)) m->pc = addr; break;
    case 0x12: addr = fetch16(m); if (m->flags & MINIX8_FLAG_C) m->pc = addr; break;
    case 0x13: addr = fetch16(m); if (!(m->flags & MINIX8_FLAG_C)) m->pc = addr; break;
    case 0x14:
        addr = fetch16(m);
        if (!push16(m, m->pc)) return cpu_fault(m, at, "overflow da pilha em CALL");
        m->pc = addr; break;
    case 0x15:
        if (!pop16(m, &addr)) return cpu_fault(m, at, "underflow da pilha em RET");
        m->pc = addr; break;
    case 0x16:
        if (!push(m, m->a)) return cpu_fault(m, at, "overflow da pilha em PUSH");
        break;
    case 0x17:
        if (!pop(m, &m->a)) return cpu_fault(m, at, "underflow da pilha em POP");
        set_zn(m, m->a); break;
    case 0x18: {
        int ch = getchar();
        if (ch == EOF && ferror(stdin)) return cpu_fault(m, at, "falha de leitura em IN");
        m->a = ch == EOF ? 0 : (uint8_t)ch; set_zn(m, m->a); break;
    }
    case 0x19:
        if (output_byte(m, m->a) == EOF || fflush(stdout) == EOF) return cpu_fault(m, at, "falha de escrita em OUT");
        break;
    case 0x1a: m->halted = 1; break;
    case 0x1b: m->a++; set_zn(m, m->a); break;
    case 0x1c: m->a--; set_zn(m, m->a); break;
    case 0x1d: v = m->a; m->a <<= 1; m->flags = v & 0x80 ? MINIX8_FLAG_C : 0; set_zn(m, m->a); break;
    case 0x1e: v = m->a; m->a >>= 1; m->flags = v & 1 ? MINIX8_FLAG_C : 0; set_zn(m, m->a); break;
    case 0x1f: m->a = m->b; set_zn(m, m->a); break;
    case 0x20: m->b = m->a; set_zn(m, m->b); break;
    case 0x21: m->a = m->c; set_zn(m, m->a); break;
    case 0x22: m->c = m->a; set_zn(m, m->c); break;
    case 0x23: m->a = m->d; set_zn(m, m->a); break;
    case 0x24: m->d = m->a; set_zn(m, m->d); break;
    default: {
        char reason[64];
        snprintf(reason, sizeof(reason), "opcode %02X inválido", op);
        return cpu_fault(m, at, reason);
    }
    }
    return 1;
}
