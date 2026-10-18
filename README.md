# MiniX8

MiniX8 é uma máquina virtual didática completa de 8 bits: CPU, 64 KiB de memória, pilha, flags, entrada e saída de terminal, carregador de ROM e monitor de depuração. O núcleo é C11 sem dependências de terceiros, então roda nativamente em Linux (Debian/Ubuntu, Fedora/RHEL e derivados), Windows e em containers. Também pode ser compilado e executado dentro de VMs Linux ou Windows.

## Compilar

### Linux (Debian/Ubuntu)

```sh
sudo apt-get install build-essential
make
./minix8 --help
sudo make install
```

### Linux (Fedora/RHEL e derivados)

```sh
sudo dnf group install "Development Tools"
make
./minix8 --help
```

### CMake (Linux, macOS, Windows)

```sh
cmake -S . -B build
cmake --build build --config Release
```

No Windows, abra o diretório no Visual Studio ou rode os comandos acima em um terminal com CMake e MSVC instalados. O executável fica em `build/Release/minix8.exe` para geradores multi-config e em `build/minix8.exe` para MinGW.

### Container

```sh
docker build -t minix8 .
docker run --rm minix8 --help
docker run --rm -it -v "$PWD:/rom:ro" minix8 --rom /rom/program.bin
```

O build compila o programa e executa `make test`. A imagem final roda como usuário sem privilégios e contém apenas o executável. Podman aceita os mesmos comandos. Consulte o [guia Docker/Podman](docs/DOCKER.md) para dependências, execução e erros de acesso ao daemon ou namespaces. No Windows, monte a pasta da ROM com a sintaxe de volume do Docker Desktop.

## Usar

Execute uma ROM binária que inicia em `0x0000`:

```sh
./minix8 --rom programa.bin
./minix8 --rom programa.bin --origin 0x8000 --steps 50000
```

Sem ROM, abra o monitor. Com `--monitor`, a ROM é carregada e o monitor permanece aberto para depuração:

```sh
./minix8
./minix8 --rom programa.bin --monitor
```

Comandos: `help`, `regs`, `step [n]`, `run [n]`, `reset`, `load arquivo [endereço]`, `mem endereço [tamanho]`, `set endereço byte`, `quit`. Números aceitam decimal e prefixos `0x`.

Para um programa mínimo que imprime `Oi!`, os bytes são `01 4F 19 01 69 19 01 21 19 1A` (LDA #O, OUT A, LDA #i, OUT A, LDA #!, OUT A, HLT). Salve-os em `oi.bin` e rode `./minix8 --rom oi.bin`.

Veja o conjunto completo de instruções em [docs/ISA.md](docs/ISA.md).

## Testes e QA

```sh
make test      # testes unitários do núcleo e integração da CLI
make sanitize  # mesmos testes com AddressSanitizer e UBSan
make analyze   # análise estática GCC (-fanalyzer)
make qa        # executa os testes, sanitizers e análise estática
```

Ou use CMake/CTest:

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug
cmake --build build --parallel
ctest --test-dir build --output-on-failure
```

Os testes CLI criam ROMs temporárias e verificam execução, entrada/saída, endereço de entrada, parâmetros inválidos, opcode desconhecido, tamanho máximo de ROM e comandos do monitor. `make qa` requer GCC com `-fanalyzer` e um compilador com AddressSanitizer/UBSan. Veja [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) para a cobertura e as limitações de QA.

## Documentação e contribuição

- [Arquitetura da máquina](docs/ARCHITECTURE.md): componentes, ciclo de CPU e limites implementados.
- [ISA](docs/ISA.md): opcodes, operandos, flags e convenções binárias.
- [Contribuição e mensagens de commit](CONTRIBUTING.md): fluxo de PR e regras Conventional Commits.
- [CI/CD, QA e releases](docs/RELEASING.md): testes, sanitizers, matriz de builds, gatilhos e publicação de versões.
- [Docker e Podman](docs/DOCKER.md): dependências da imagem, testes durante o build, usuário sem privilégios e diagnóstico do host.
- [Política e limites de segurança](SECURITY.md): modelo de ameaça e canal de relato.

O CI compila em Ubuntu 22.04 x86-64, macOS 14 ARM64 e Windows Server 2022 x86-64; também compila o núcleo em Debian stable e Fedora. Pushes e PRs executam a validação e os builds. Para publicar automaticamente, integre na `main` via squash um commit `feat: ...` (gera versão minor) ou uma mudança incompatível marcada com `!`/`BREAKING CHANGE:` (gera versão major). Os executáveis correspondentes são anexados à release no GitHub.
