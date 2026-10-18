# Instalação e execução

## Releases

Baixe a release mais recente na página Releases do repositório. Os nomes indicam sistema e arquitetura:

- `minix8-linux-x86_64`: Linux x86-64 (Ubuntu 22.04 ABI; pode requerer glibc compatível).
- `minix8-macos-arm64`: macOS em Apple Silicon.
- `minix8-windows-x86_64.exe`: Windows x86-64.
- `MiniX8-1987.iso`: mídia ISO9660 de distribuição com binários, ROM executável, fontes e manuais.

No Linux, marque o executável como executável (`chmod +x minix8-linux-x86_64`) e rode `./minix8-linux-x86_64 --help`. No macOS, use `chmod +x minix8-macos-arm64` e execute-o pelo Terminal. O Windows pode executar o `.exe` pelo PowerShell ou Prompt de Comando.

Para abrir a interface desktop, compile ou baixe o executável e inicie `python3 tools/minix8_gui.py --binary /caminho/minix8` (no Windows: `py tools\minix8_gui.py --binary caminho\minix8.exe`). É necessário Python com Tkinter e um desktop gráfico. O frontend controla o processo local, não funciona em container headless. Consulte [GUI.md](GUI.md).

## Compilar do código-fonte

### Debian/Ubuntu

```sh
sudo apt-get install build-essential python3
make
make test
```

### Fedora/RHEL

```sh
sudo dnf group install "Development Tools"
sudo dnf install python3
make
make test
```

### CMake

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release
ctest --test-dir build --build-config Release --output-on-failure
```

O CMake detecta Python para ativar também o teste de CLI; o teste nativo do núcleo continua disponível sem Python.

## ROM e monitor

```sh
./minix8 --rom examples/hello.rom
./minix8 --rom examples/hello.rom --origin 0x8000 --steps 50000
./minix8 --rom examples/hello.rom --monitor
```

Crie `examples/hello.rom` a partir do exemplo textual com `python3 scripts/hex_to_rom.py examples/hello.hex examples/hello.rom`. A ROM pode ter no máximo 65.536 bytes, reduzidos pela origem escolhida. O PC começa no endereço de carga. O modo de execução automática para após HLT, falha ou alcançar o limite de instruções.

No monitor: `help`, `regs`, `step [n]`, `run [n]`, `reset`, `load arquivo [endereço]`, `mem endereço [tamanho]`, `set endereço byte` e `quit`. `reset` limpa CPU e RAM. `load` valida a ROM completamente antes de copiá-la.

## Container

```sh
docker build -t minix8 .
docker run --rm minix8 --help
docker run --rm -it -v "$PWD:/rom:ro" minix8 --rom /rom/hello.rom
```

Podman aceita os mesmos comandos. Um container facilita a instalação, mas não torna a máquina convidada inicializável por si só.
