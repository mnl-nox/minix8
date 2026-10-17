CC ?= cc
CFLAGS ?= -O2 -std=c11 -Wall -Wextra -Wpedantic
SANITIZER_FLAGS ?= -O1 -g -std=c11 -Wall -Wextra -Wpedantic -fsanitize=address,undefined -fno-omit-frame-pointer
ANALYZE_CC ?= gcc
ANALYZE_FLAGS ?= -O2 -std=c11 -Wall -Wextra -Wpedantic -Werror -fanalyzer
PREFIX ?= /usr/local
BUILD_DIR ?= build

.PHONY: all clean install test sanitize analyze qa
all: minix8
minix8: src/minix8.c src/minix8_core.c src/minix8_core.h
	$(CC) $(CFLAGS) -o $@ src/minix8.c src/minix8_core.c
install: minix8
	install -d $(DESTDIR)$(PREFIX)/bin
	install -m 755 minix8 $(DESTDIR)$(PREFIX)/bin/minix8
$(BUILD_DIR)/test-core: tests/test_core.c src/minix8_core.c src/minix8_core.h
	install -d $(BUILD_DIR)
	$(CC) $(CFLAGS) -o $@ tests/test_core.c src/minix8_core.c
test: minix8 $(BUILD_DIR)/test-core
	./$(BUILD_DIR)/test-core
	python3 scripts/test_cli.py ./minix8
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
	$(ANALYZE_CC) $(ANALYZE_FLAGS) -fsyntax-only src/minix8.c src/minix8_core.c
qa: test sanitize analyze
clean:
	rm -f minix8 minix8.exe
	rm -rf $(BUILD_DIR)
