CC ?= cc
CFLAGS ?= -O2 -std=c11 -Wall -Wextra -Wpedantic -fstack-protector-strong
SANITIZER_FLAGS ?= -O1 -g -std=c11 -Wall -Wextra -Wpedantic -fsanitize=address,undefined -fno-omit-frame-pointer
ANALYZE_CC ?= gcc
ANALYZE_FLAGS ?= -O2 -std=c11 -Wall -Wextra -Wpedantic -Werror -fanalyzer
PREFIX ?= /usr/local
BUILD_DIR ?= build
ISO_OUT ?= dist/MiniX8-1987.iso
BOOT_ISO_OUT ?= dist/MiniX8-VM-boot.iso
ISO_BIN_DIR ?= .

.PHONY: all clean install test sanitize analyze qa iso gui boot-iso
all: minix8 hexrom
minix8: src/minix8.c src/minix8_core.c src/minix8_core.h
	$(CC) $(CFLAGS) -o $@ src/minix8.c src/minix8_core.c
hexrom: tools/hexrom.c
	$(CC) $(CFLAGS) -o $@ tools/hexrom.c
install: minix8 hexrom
	install -d $(DESTDIR)$(PREFIX)/bin
	install -m 755 minix8 $(DESTDIR)$(PREFIX)/bin/minix8
	install -m 755 hexrom $(DESTDIR)$(PREFIX)/bin/hexrom
$(BUILD_DIR)/test-core: tests/test_core.c src/minix8_core.c src/minix8_core.h
	install -d $(BUILD_DIR)
	$(CC) $(CFLAGS) -o $@ tests/test_core.c src/minix8_core.c
test: minix8 hexrom $(BUILD_DIR)/test-core
	./$(BUILD_DIR)/test-core
	python3 scripts/test_cli.py ./minix8
	python3 -m unittest tests/test_tools.py tests/test_check_commits.py
	python3 scripts/test_hexrom.py ./hexrom
	python3 -m py_compile tools/minix8_gui.py tools/minix8_as.py tools/minix8_devices.py scripts/hex_to_rom.py scripts/write_sha256.py
$(BUILD_DIR)/minix8-sanitize: src/minix8.c src/minix8_core.c src/minix8_core.h
	install -d $(BUILD_DIR)
	$(CC) $(SANITIZER_FLAGS) -o $@ src/minix8.c src/minix8_core.c
$(BUILD_DIR)/test-core-sanitize: tests/test_core.c src/minix8_core.c src/minix8_core.h
	install -d $(BUILD_DIR)
	$(CC) $(SANITIZER_FLAGS) -o $@ tests/test_core.c src/minix8_core.c
sanitize: $(BUILD_DIR)/minix8-sanitize $(BUILD_DIR)/test-core-sanitize
	ASAN_OPTIONS=detect_leaks=0 ./$(BUILD_DIR)/test-core-sanitize
	ASAN_OPTIONS=detect_leaks=0 python3 scripts/test_cli.py ./$(BUILD_DIR)/minix8-sanitize
analyze:
	$(ANALYZE_CC) $(ANALYZE_FLAGS) -fsyntax-only src/minix8.c src/minix8_core.c tools/hexrom.c
qa: test sanitize analyze
iso: minix8
	ISO_BIN_DIR="$(ISO_BIN_DIR)" sh scripts/make_iso.sh "$(ISO_OUT)" "$(ISO_BIN_DIR)"
boot-iso: minix8 hexrom
	sh scripts/make_boot_iso.sh "$(BOOT_ISO_OUT)"
gui: minix8
	python3 tools/minix8_gui.py
clean:
	rm -f minix8 minix8.exe hexrom
	rm -rf $(BUILD_DIR)
