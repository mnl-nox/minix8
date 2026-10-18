# MiniX8

![Logo do MiniX8: um microcomputador de 8 bits com monitor verde-fósforo](site/logo.svg)

**MiniX8 é um computador virtual didático de 8 bits**, implementado principalmente em C11. O projeto reúne uma CPU com conjunto de instruções próprio, 64 KiB de memória, pilha, flags, entrada e saída por console, carregamento de ROM, monitor de depuração, assembler em Python e interface gráfica retro.

O objetivo é tornar conceitos de arquitetura de computadores e sistemas de baixo nível observáveis, testáveis e modificáveis — do ciclo de execução de uma instrução à construção de pequenos programas em Assembly.

<p>
  <a href="https://github.com/mnl-nox/minix8/releases"><img alt="Releases" src="https://img.shields.io/github/v/release/mnl-nox/minix8?display_name=tag&label=release"></a>
  <a href="https://github.com/mnl-nox/minix8/blob/main/LICENSE"><img alt="Licença GPL-3.0-or-later" src="https://img.shields.io/badge/license-GPL--3.0--or--later-blue.svg"></a>
  <a href="https://github.com/mnl-nox/minix8"><img alt="Linguagem principal C" src="https://img.shields.io/badge/linguagem-C11-informational"></a>
  <a href="https://github.com/mnl-nox/minix8/issues"><img alt="Issues" src="https://img.shields.io/github/issues/mnl-nox/minix8"></a>
</p>

**[Site do projeto](https://mnl-nox.github.io/minix8/) · [Releases e binários](https://github.com/mnl-nox/minix8/releases) · [Documentação](docs/USER_GUIDE.md) · [Roadmap](docs/ROADMAP.md)**

## Índice

- [Visão geral](#visão-geral)
- [Funcionalidades](#funcionalidades)
- [Início rápido](#início-rápido)
- [Compilação](#compilação)
- [Assembly e exemplos](#assembly-e-exemplos)
- [Interface gráfica](#interface-gráfica)
- [Testes e qualidade](#testes-e-qualidade)
- [ISO e máquina virtual](#iso-e-máquina-virtual)
- [Arquitetura e documentação](#arquitetura-e-documentação)
- [Limites atuais](#limites-atuais)
- [Contribuição](#contribuição)
- [Licença](#licença)

## Visão geral

MiniX8 é um ambiente de experimentação para estudar como software interage com uma arquitetura de máquina simples. A implementação permite acompanhar registradores, memória, instruções e operações de entrada/saída sem exigir hardware físico específico.

O projeto é inspirado em temas clássicos de organização de computadores e sistemas operacionais. Ele **não é uma implementação compatível com MINIX 3**, não substitui um computador físico e não deve ser confundido com um sistema operacional completo. A mídia live opcional inicializa um ambiente Linux mínimo que hospeda o emulador de CPU de 8 bits.

## Funcionalidades

- **CPU virtual de 8 bits:** conjunto de instruções documentado, registradores e flags.
- **Memória:** espaço de endereçamento de 64 KiB.
- **Pilha e fluxo de execução:** operações de baixo nível adequadas a exercícios de arquitetura.
- **Console virtual:** instruções `IN`/`OUT` para entrada e saída byte a byte.
- **Monitor de depuração:** execução por passos ou limitada, inspeção de registradores e memória, carregamento e alteração de bytes.
- **Assembler em Python:** converte fontes Assembly da ISA MiniX8 em ROM.
- **Ferramentas auxiliares:** conversão de HEX para ROM e enumeração somente de leitura de dispositivos do sistema hospedeiro.
- **GUI em Tkinter:** carregamento de programas, execução controlada e visualização de estado da máquina.
- **Contador determinístico de instruções:** `GETCYC` e `GETCYH` leem os 16 bits inferiores do contador.
- **Validação automatizada:** testes, sanitizers, análise estática e builds em múltiplas plataformas.
- **Distribuição:** binários de release, ISO de dados e mídia live x86-64 para máquinas virtuais.

## Início rápido

### Requisitos

Para compilar o núcleo, use um compilador C compatível com C11 e GNU Make ou CMake. Para o assembler e ferramentas, use Python 3. Para a interface gráfica, também é necessário Tkinter e um ambiente gráfico. Os comandos abaixo presumem um shell Linux/macOS; no Windows, use um terminal com as ferramentas correspondentes instaladas.

### Compilar e executar

Em Debian ou Ubuntu:

```sh
sudo apt-get update
sudo apt-get install build-essential
make
make test
./minix8 --help
```

Execute um programa de exemplo:

```sh
python3 tools/minix8_as.py examples/hello.asm /tmp/hello.rom
./minix8 --rom /tmp/hello.rom
```

O exemplo `examples/hello.asm` demonstra o fluxo básico entre Assembly, ROM e execução. Para consultar as opções disponíveis, use `./minix8 --help`.

### Compilação com CMake

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel
```

No Windows, o caminho do executável depende do gerador: geradores multi-config, como Visual Studio, normalmente colocam o binário em `build/Release/minix8.exe`; com MinGW, ele costuma ficar em `build/minix8.exe`.

### Outras distribuições

No Fedora/RHEL e derivados, instale as ferramentas de desenvolvimento, por exemplo:

```sh
sudo dnf group install "Development Tools"
make
make test
```

Consulte [docs/TOOLS.md](docs/TOOLS.md) para a lista de ferramentas e as instruções específicas de cada plataforma.

## Assembly e exemplos

O assembler incluído aceita fontes da ISA MiniX8 e gera ROMs para o emulador:

```sh
python3 tools/minix8_as.py examples/hello.asm /tmp/hello.rom
./minix8 --rom /tmp/hello.rom
```

É possível carregar uma ROM em um endereço específico e limitar o número de passos executados:

```sh
./minix8 --rom programa.bin
./minix8 --rom programa.bin --origin 0x8000 --steps 50000
```

Para abrir o monitor interativo sem ROM ou manter o monitor disponível durante a execução de um programa:

```sh
./minix8
./minix8 --rom programa.bin --monitor
```

Comandos comuns do monitor incluem `help`, `regs`, `step [n]`, `run [n]`, `reset`, `load arquivo [endereço]`, `mem endereço [tamanho]`, `set endereço byte` e `quit`. Os números aceitam decimal e o prefixo `0x`.

Veja os programas em [examples/](examples/), a [referência da ISA](docs/ISA.md) e o [manual do assembler](docs/ASSEMBLY.md).

## Interface gráfica

A interface desktop usa Tkinter e permite carregar ROMs, montar fontes Assembly, converter arquivos HEX, executar por passos e inspecionar registradores e RAM.

```sh
make gui
```

Ou abra uma ROM diretamente:

```sh
python3 scripts/hex_to_rom.py examples/hello.hex /tmp/hello.rom
python3 tools/minix8_gui.py --rom /tmp/hello.rom
```

Requer Python 3, Tkinter, ambiente gráfico e o executável `minix8`. Consulte o [manual da GUI](docs/GUI.md). O site do projeto distingue explicitamente ilustrações de capturas reais da aplicação; consulte a página para ver o material visual disponível.

## Testes e qualidade

Os alvos Make mais usados são:

```sh
make test      # testes unitários e de integração da CLI
make sanitize  # testes com AddressSanitizer e UBSan
make analyze   # análise estática com GCC -fanalyzer
make qa        # conjunto de validações de QA
```

Com CMake/CTest:

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug
cmake --build build --parallel
ctest --test-dir build --output-on-failure
```

A disponibilidade de sanitizers e análise estática depende do compilador instalado. Consulte [docs/QA.md](docs/QA.md) e [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) para detalhes sobre cobertura, arquitetura e limitações conhecidas.

## ISO e máquina virtual

Há dois formatos distintos de mídia:

- **ISO de dados:** criada por `make iso`; reúne executável, ROM de exemplo, lançadores, fontes e manuais. Não é inicializável e roda sobre o sistema hospedeiro.
- **ISO live x86-64 para VM:** criada por `make boot-iso`; inclui kernel Linux, BusyBox e MiniX8 em um ambiente mínimo para iniciar em uma máquina virtual. O Linux é o hospedeiro do emulador — não um sistema operacional histórico de 8 bits.

Consulte o [guia da ISO](docs/ISO.md), o [guia da VM bootável](docs/BOOTABLE_VM.md), o [guia Docker/Podman](docs/DOCKER.md) e as [ferramentas necessárias](docs/TOOLS.md). A disponibilidade de dependências para gerar as imagens depende da plataforma.

## Arquitetura e documentação

| Documento | Conteúdo |
| --- | --- |
| [Guia do usuário](docs/USER_GUIDE.md) | Primeiros passos e fluxo de uso |
| [Arquitetura](docs/ARCHITECTURE.md) | Componentes, ciclo de CPU e decisões de implementação |
| [ISA](docs/ISA.md) | Instruções, operandos, flags e convenções binárias |
| [Assembler](docs/ASSEMBLY.md) | Sintaxe e geração de ROM |
| [Comandos](docs/COMMANDS.md) | Monitor, CLI e comandos disponíveis |
| [Interface gráfica](docs/GUI.md) | Uso e limitações da GUI |
| [Dispositivos](docs/DEVICES.md) | Capacidades existentes e possibilidades futuras |
| [Roadmap](docs/ROADMAP.md) | Evolução planejada |
| [QA e limitações](docs/QA.md) | Testes e limitações conhecidas |
| [Erros e diagnóstico](docs/ERRORS.md) | Mensagens de erro e resolução de problemas |
| [Docker/Podman](docs/DOCKER.md) | Construção e execução em contêineres |
| [ISO](docs/ISO.md) | Mídia de dados |
| [VM bootável](docs/BOOTABLE_VM.md) | Ambiente live x86-64 |
| [Referências](docs/REFERENCES.md) | Bibliografia e contexto relacionado ao MINIX 3 |
| [Ferramentas](docs/TOOLS.md) | Dependências de desenvolvimento e distribuição |
| [Releases](docs/RELEASING.md) | CI/CD e processo de publicação |
| [Contribuição](CONTRIBUTING.md) | Fluxo de trabalho e padrão de commits |
| [Segurança](SECURITY.md) | Modelo de ameaça e relato de vulnerabilidades |
| [Auditoria de segurança](SECURITY_AUDIT.md) | Observações e limitações de segurança |
| [Avisos de terceiros](THIRD_PARTY_NOTICES.md) | Licenças de componentes externos |

## Limites atuais

MiniX8 é um projeto educacional em evolução. As capacidades implementadas devem ser distinguidas das propostas no roadmap:

- A CPU virtual oferece console byte a byte; não há atualmente rede virtual, disco de convidado, passthrough USB, áudio ou framebuffer.
- O scanner de dispositivos enumera informações expostas pelo sistema hospedeiro em modo somente leitura; não faz a CPU virtual controlar esses dispositivos.
- A ISO de dados não é inicializável. A mídia live é um ambiente Linux hospedeiro para executar o emulador.
- A ISA MiniX8 é própria e não é binariamente compatível com processadores comerciais ou com o MINIX 3.

A evolução planejada e o estado das propostas estão documentados em [docs/ROADMAP.md](docs/ROADMAP.md) e no [issue agregador #15](https://github.com/mnl-nox/minix8/issues/15).

## Contribuição

Contribuições, relatos de bugs e sugestões são bem-vindos. Antes de abrir um pull request:

1. Leia [CONTRIBUTING.md](CONTRIBUTING.md) e confira as issues abertas.
2. Faça uma alteração focada e inclua testes quando aplicável.
3. Execute `make test`; quando disponíveis, execute também `make qa`.
4. Use mensagens de commit no padrão Conventional Commits.
5. Descreva no PR o problema, a solução, os testes executados e eventuais limitações.

Para relatar uma vulnerabilidade, siga a [política de segurança](SECURITY.md), em vez de publicar detalhes sensíveis em uma issue aberta.

## Projeto e referências de estudo

O MiniX8 é mantido por **[mnl-nox](https://github.com/mnl-nox)**. O repositório e o [site do projeto](https://mnl-nox.github.io/minix8/) documentam o escopo técnico, o histórico de desenvolvimento, curiosidades, perguntas frequentes e referências de estudo.

Para aprofundar os fundamentos, consulte a bibliografia indicada em [docs/REFERENCES.md](docs/REFERENCES.md), incluindo obras de Andrew S. Tanenbaum sobre organização de computadores e sistemas operacionais. O site também oferece um feed Atom das releases para acompanhar novas versões sem precisar cadastrar um e-mail.

## Licença

O código original do MiniX8 é distribuído sob a **GNU General Public License v3.0 ou posterior (GPL-3.0-or-later)**. Consulte [LICENSE](LICENSE). Componentes externos empacotados na mídia live podem ter licenças próprias; consulte [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) e os avisos associados à release.

---

[Reportar problema](https://github.com/mnl-nox/minix8/issues/new/choose) · [Ver releases](https://github.com/mnl-nox/minix8/releases) · [Acessar o site](https://mnl-nox.github.io/minix8/)
