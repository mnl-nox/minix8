/* Small standalone .hex to raw ROM converter for the bootable live image. */
#include <ctype.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <wchar.h>
#ifdef _WIN32
#include <windows.h>
#endif

#define MAX_ROM 65536u
#define MAX_SOURCE_SIZE (1024u * 1024u)

static int hex_value(int ch) {
    if (ch >= '0' && ch <= '9') return ch - '0';
    if (ch >= 'a' && ch <= 'f') return ch - 'a' + 10;
    if (ch >= 'A' && ch <= 'F') return ch - 'A' + 10;
    return -1;
}

static int flush_token(const char *token, size_t length, unsigned char *rom,
                       size_t *size, unsigned long line) {
    size_t offset = 0;
    if (!length) return 1;
    if (length == 4 && token[0] == '0' && (token[1] == 'x' || token[1] == 'X')) offset = 2;
    if (length - offset != 2) {
        fprintf(stderr, "hexrom: line %lu: invalid byte token '%.*s'\n", line, (int)length, token);
        return 0;
    }
    int high = hex_value((unsigned char)token[offset]);
    int low = hex_value((unsigned char)token[offset + 1]);
    if (high < 0 || low < 0) {
        fprintf(stderr, "hexrom: line %lu: invalid hexadecimal token '%.*s'\n", line, (int)length, token);
        return 0;
    }
    if (*size >= MAX_ROM) {
        fprintf(stderr, "hexrom: ROM exceeds %u bytes\n", MAX_ROM);
        return 0;
    }
    rom[(*size)++] = (unsigned char)((high << 4) | low);
    return 1;
}

static int hexrom_main(int argc, char **argv) {
    if (argc != 3) {
        fprintf(stderr, "Usage: hexrom input.hex output.rom\n");
        return 2;
    }
#ifdef _WIN32
    (void)SetConsoleOutputCP(CP_UTF8);
    int input_len = MultiByteToWideChar(CP_UTF8, MB_ERR_INVALID_CHARS, argv[1], -1, NULL, 0);
    int output_len = MultiByteToWideChar(CP_UTF8, MB_ERR_INVALID_CHARS, argv[2], -1, NULL, 0);
    wchar_t *input_path = input_len > 0 ? (wchar_t *)malloc((size_t)input_len * sizeof(wchar_t)) : NULL;
    wchar_t *output_path = output_len > 0 ? (wchar_t *)malloc((size_t)output_len * sizeof(wchar_t)) : NULL;
    if (!input_path || !output_path || !MultiByteToWideChar(CP_UTF8, MB_ERR_INVALID_CHARS, argv[1], -1, input_path, input_len) ||
        !MultiByteToWideChar(CP_UTF8, MB_ERR_INVALID_CHARS, argv[2], -1, output_path, output_len)) {
        free(input_path); free(output_path); fputs("hexrom: invalid UTF-8 path\n", stderr); return 1;
    }
    FILE *input = _wfopen(input_path, L"rb");
#else
    FILE *input = fopen(argv[1], "rb");
#endif
    if (!input) {
#ifdef _WIN32
        fprintf(stderr, "hexrom: cannot open input: %s\n", strerror(errno)); free(input_path); free(output_path);
#else
        fprintf(stderr, "hexrom: cannot open %s: %s\n", argv[1], strerror(errno));
#endif
        return 1;
    }
    unsigned char rom[MAX_ROM];
    char token[16];
    size_t size = 0, token_size = 0;
    unsigned long line = 1;
    int comment = 0, failed = 0, ch;
    size_t input_size = 0;
    while ((ch = fgetc(input)) != EOF) {
        if (++input_size > MAX_SOURCE_SIZE) {
            fprintf(stderr, "hexrom: input exceeds %u bytes\n", MAX_SOURCE_SIZE);
            failed = 1;
            break;
        }
        if (ch == '\n') {
            if (!comment && !flush_token(token, token_size, rom, &size, line)) failed = 1;
            token_size = 0; comment = 0; line++;
        } else if (comment) {
            continue;
        } else if (ch == '#') {
            if (!flush_token(token, token_size, rom, &size, line)) failed = 1;
            token_size = 0; comment = 1;
        } else if (isspace((unsigned char)ch) || ch == ',') {
            if (!flush_token(token, token_size, rom, &size, line)) failed = 1;
            token_size = 0;
        } else if (token_size + 1 < sizeof(token)) {
            token[token_size++] = (char)ch;
        } else {
            fprintf(stderr, "hexrom: line %lu: token too long\n", line);
            failed = 1;
        }
        if (failed) break;
    }
    if (!failed && ferror(input)) { perror("hexrom: read"); failed = 1; }
    if (fclose(input) != 0 && !failed) { perror("hexrom: close input"); failed = 1; }
    if (!failed && !flush_token(token, token_size, rom, &size, line)) failed = 1;
    if (!failed && size == 0) { fputs("hexrom: input contains no bytes\n", stderr); failed = 1; }
    if (failed) {
#ifdef _WIN32
        free(input_path); free(output_path);
#endif
        return 1;
    }

#ifdef _WIN32
    FILE *output = _wfopen(output_path, L"wb");
#else
    FILE *output = fopen(argv[2], "wb");
#endif
    if (!output) {
        fprintf(stderr, "hexrom: cannot create %s: %s\n", argv[2], strerror(errno));
#ifdef _WIN32
        free(input_path); free(output_path);
#endif
        return 1;
    }
    int write_failed = fwrite(rom, 1, size, output) != size;
    if (fclose(output) != 0) write_failed = 1;
    if (write_failed) {
#ifdef _WIN32
        free(input_path); free(output_path);
#endif
        fprintf(stderr, "hexrom: failed to write %s\n", argv[2]);
        return 1;
    }
    printf("ROM written: %zu bytes -> %s\n", size, argv[2]);
#ifdef _WIN32
    free(input_path); free(output_path);
#endif
    return 0;
}

#ifdef _WIN32
static char *wide_to_utf8(const wchar_t *wide) {
    int length = WideCharToMultiByte(CP_UTF8, WC_ERR_INVALID_CHARS, wide, -1, NULL, 0, NULL, NULL);
    if (length <= 0) return NULL;
    char *utf8 = (char *)malloc((size_t)length);
    if (!utf8 || !WideCharToMultiByte(CP_UTF8, WC_ERR_INVALID_CHARS, wide, -1, utf8, length, NULL, NULL)) {
        free(utf8); return NULL;
    }
    return utf8;
}

int wmain(int argc, wchar_t **wide_argv) {
    char **argv = (char **)calloc((size_t)argc + 1, sizeof(char *));
    if (!argv) return 1;
    int failed = 0;
    for (int i = 0; i < argc; ++i) {
        argv[i] = wide_to_utf8(wide_argv[i]);
        if (!argv[i]) { failed = 1; break; }
    }
    int result = failed ? 2 : hexrom_main(argc, argv);
    for (int i = 0; i < argc; ++i) free(argv[i]);
    free(argv);
    return result;
}
#else
int main(int argc, char **argv) { return hexrom_main(argc, argv); }
#endif
