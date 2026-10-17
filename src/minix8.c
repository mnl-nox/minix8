#include <ctype.h>
#include <errno.h>
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "minix8_core.h"

#define LINE_SIZE 512
#define DEFAULT_STEP_LIMIT UINT64_C(1000000)
#define RAM_SIZE MINIX8_RAM_SIZE
#define FLAG_Z MINIX8_FLAG_Z
#define FLAG_C MINIX8_FLAG_C
#define FLAG_N MINIX8_FLAG_N
typedef Minix8Machine Machine;

static void registers(const Machine *m) {
    printf("A=%02X B=%02X C=%02X D=%02X  PC=%04X SP=%04X  FLAGS=%c%c%c  CICLOS=%llu%s\n",
        m->a, m->b, m->c, m->d, m->pc, m->sp,
        m->flags & FLAG_N ? 'N' : '-', m->flags & FLAG_Z ? 'Z' : '-', m->flags & FLAG_C ? 'C' : '-',
        (unsigned long long)m->cycles, m->halted ? " HALT" : "");
}
static int load_file(Machine *m, const char *path, uint16_t origin) {
    FILE *f = fopen(path, "rb");
    if (!f) { fprintf(stderr, "Não foi possível abrir %s: %s\n", path, strerror(errno)); return 0; }
    size_t capacity = RAM_SIZE - (size_t)origin;
    uint8_t *buffer = (uint8_t *)malloc(capacity ? capacity : 1);
    if (!buffer) { fclose(f); fputs("Memória insuficiente ao carregar ROM.\n", stderr); return 0; }
    size_t n = fread(buffer, 1, capacity, f);
    int io_error = ferror(f);
    int extra = io_error ? EOF : fgetc(f);
    if (ferror(f)) io_error = 1;
    if (fclose(f) != 0) io_error = 1;
    if (io_error) { fprintf(stderr, "Falha de leitura da ROM %s.\n", path); free(buffer); return 0; }
    if (extra != EOF) { fprintf(stderr, "ROM excede a memória disponível a partir de %04X\n", origin); free(buffer); return 0; }
    memcpy(m->ram + origin, buffer, n);
    free(buffer);
    m->pc = origin;
    m->halted = 0;
    m->faulted = 0;
    printf("ROM carregada: %zu bytes em %04X\n", n, origin); return 1;
}
static int parse_u64(const char *text, uint64_t max, uint64_t *out) {
    char *end = NULL;
    unsigned long long value;
    if (!text || !*text || *text == '-' || *text == '+' || isspace((unsigned char)*text)) return 0;
    errno = 0;
    value = strtoull(text, &end, 0);
    if (errno == ERANGE || end == text || *end != '\0' || value > max) return 0;
    *out = (uint64_t)value;
    return 1;
}
static void help(void) {
    puts("Comandos: help | regs | step [n] | run [n] | reset | load arquivo [endereço] | mem endereço [tamanho] | set endereço byte | quit");
}
static void monitor(Machine *m) {
    char line[LINE_SIZE]; help();
    for (;;) {
        fputs("minix8> ", stdout); fflush(stdout);
        if (!fgets(line, sizeof(line), stdin)) break;
        size_t line_len = strlen(line);
        if (line_len && line[line_len - 1] != '\n' && !feof(stdin)) {
            int ch;
            while ((ch = getchar()) != '\n' && ch != EOF) { }
            puts("Linha longa demais; comando descartado.");
            continue;
        }
        char *cmd = strtok(line, " \t\r\n"); if (!cmd) continue;
        if (!strcmp(cmd, "quit") || !strcmp(cmd, "exit")) break;
        if (!strcmp(cmd, "help")) help();
        else if (!strcmp(cmd, "regs")) registers(m);
        else if (!strcmp(cmd, "reset")) { minix8_reset(m); puts("CPU e RAM reiniciadas."); }
        else if (!strcmp(cmd, "step") || !strcmp(cmd, "run")) {
            int running = !strcmp(cmd, "run"); char *arg = strtok(NULL, " \t\r\n");
            uint64_t count = running ? DEFAULT_STEP_LIMIT : 1, executed = 0;
            if (arg && !parse_u64(arg, UINT64_MAX, &count)) { puts("Quantidade inválida."); continue; }
            while (executed < count && !m->halted) { if (minix8_step(m) < 0) break; executed++; }
            if (running && !m->halted && executed == count) puts("Limite de instruções alcançado.");
            registers(m);
        } else if (!strcmp(cmd, "load")) {
            char *path = strtok(NULL, " \t\r\n"), *a = strtok(NULL, " \t\r\n");
            uint64_t origin = 0;
            if (!path || (a && !parse_u64(a, UINT16_MAX, &origin))) puts("Uso: load arquivo [endereço 0..65535]");
            else load_file(m, path, (uint16_t)origin);
        } else if (!strcmp(cmd, "mem")) {
            char *a = strtok(NULL, " \t\r\n"), *n = strtok(NULL, " \t\r\n");
            if (!a) { puts("Uso: mem endereço [tamanho]"); continue; }
            uint64_t start64, len64 = 16;
            if (!parse_u64(a, UINT16_MAX, &start64) || (n && !parse_u64(n, RAM_SIZE, &len64))) { puts("Endereço ou tamanho inválido."); continue; }
            unsigned start = (unsigned)start64, len = (unsigned)len64;
            if (start >= RAM_SIZE) { puts("Endereço inválido."); continue; }
            if (len > RAM_SIZE - start) len = RAM_SIZE - start;
            for (unsigned i = 0; i < len; i++) { if (i % 16 == 0) printf("\n%04X: ", start + i); printf("%02X ", m->ram[start + i]); }
            putchar('\n');
        } else if (!strcmp(cmd, "set")) {
            char *a = strtok(NULL, " \t\r\n"), *v = strtok(NULL, " \t\r\n");
            uint64_t address, value;
            if (!a || !v || !parse_u64(a, UINT16_MAX, &address) || !parse_u64(v, UINT8_MAX, &value)) puts("Uso: set endereço(0..65535) byte(0..255)");
            else m->ram[(uint16_t)address] = (uint8_t)value;
        } else printf("Comando desconhecido: %s\n", cmd);
    }
}
static void usage(const char *name) {
    printf("MiniX8 - computador virtual de 8 bits\nUso: %s [--rom arquivo] [--origin endereço] [--steps limite] [--monitor]\n", name);
}
int main(int argc, char **argv) {
    Machine *m = (Machine *)calloc(1, sizeof(*m)); if (!m) { fputs("Memória insuficiente.\n", stderr); return 1; }
    minix8_reset(m); const char *rom = NULL; uint64_t origin64 = 0, limit = DEFAULT_STEP_LIMIT; int interactive = 0, origin_set = 0, steps_set = 0;
    for (int i = 1; i < argc; i++) {
        if (!strcmp(argv[i], "--help") || !strcmp(argv[i], "-h")) { usage(argv[0]); free(m); return 0; }
        else if (!strcmp(argv[i], "--monitor") || !strcmp(argv[i], "-i")) interactive = 1;
        else if (!strcmp(argv[i], "--rom") && i + 1 < argc) rom = argv[++i];
        else if (!strcmp(argv[i], "--origin") && i + 1 < argc) {
            if (!parse_u64(argv[++i], UINT16_MAX, &origin64)) { fputs("Endereço de origem inválido (use 0..65535).\n", stderr); free(m); return 2; }
            origin_set = 1;
        }
        else if (!strcmp(argv[i], "--steps") && i + 1 < argc) {
            if (!parse_u64(argv[++i], UINT64_MAX, &limit) || limit == 0) { fputs("Limite de instruções inválido (deve ser maior que zero).\n", stderr); free(m); return 2; }
            steps_set = 1;
        }
        else { usage(argv[0]); free(m); return 2; }
    }
    if (!rom && origin_set) { fputs("--origin requer --rom.\n", stderr); free(m); return 2; }
    if (!rom && steps_set) { fputs("--steps requer --rom.\n", stderr); free(m); return 2; }
    if (rom && !load_file(m, rom, (uint16_t)origin64)) { free(m); return 1; }
    if (rom && !interactive) {
        uint64_t executed = 0;
        while (executed < limit && !m->halted) { if (minix8_step(m) < 0) break; executed++; }
        if (!m->halted && executed == limit) puts("Limite de instruções alcançado.");
        registers(m);
    } else monitor(m);
    int exit_code = m->faulted ? 1 : 0;
    free(m); return exit_code;
}
