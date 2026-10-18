# Guia de uso rápido

## Primeiros cinco minutos

1. Monte a ISO ou extraia seu conteúdo em uma pasta gravável do computador.
2. Linux/macOS: execute `sh START-UNIX.sh`. Windows: abra `START-WINDOWS.bat`. A ROM `Oi!` será carregada e o monitor abrirá.
3. No prompt `minix8>`, digite `g` para executar o programa; depois use `regs` e `mem 0 16` para explorar a máquina. `q` fecha o monitor.
4. Para uma janela gráfica, execute `sh START-UNIX.sh --gui` ou `START-WINDOWS.bat --gui`.
5. Para experimentar uma ROM própria, use o CLI: `bin/minix8-linux-x86_64 --rom /caminho/programa.rom --monitor`.

O binário tem de corresponder ao sistema hospedeiro. Dentro de uma VM, escolha o binário da VM. Containers Linux usam o kernel do host; a ISO do MiniX8 é uma mídia de dados ISO9660, não um CD inicializável de sistema operacional.

## Compilar e executar exemplo no fonte

```sh
make
python3 scripts/hex_to_rom.py examples/hello.hex /tmp/hello.rom
./minix8 --rom /tmp/hello.rom --monitor
```

Na sessão do monitor:

```text
minix8> regs
minix8> mem 0 16
minix8> reset
minix8> load /tmp/hello.rom 0
minix8> run 100
minix8> quit
```

O `reset` apaga CPU e RAM; em seguida carregue novamente a ROM. `run` para em `HLT`. Se alcançar o orçamento informado antes de HLT, mostra aviso e deixa a máquina pronta para continuar.

## Montar e criar ROMs

Para escrever assembly com rótulos/mnemonics, use o assembler da ISA:

```sh
python3 tools/minix8_as.py examples/hello.asm /tmp/hello.rom
```

Veja [ASSEMBLY.md](ASSEMBLY.md) para a sintaxe. Também pode converter bytes
hexadecimais em `.hex`:

```text
01 4F 19 01 69 19 01 21 19 1A
```

O conversor produz um binário simples sem metadados. As instruções formam três pares `LDA #byte; OUT A`, seguidos por `HLT`. Veja [ISA.md](ISA.md) para os opcodes e [COMMANDS.md](COMMANDS.md) para o manual completo do terminal e da GUI.

## Se algo não funcionar

- **`No runnable binary found`**: a imagem não inclui binário para essa plataforma; compile o fonte com Make/CMake.
- **`EXECUTÁVEL NÃO ENCONTRADO` na GUI**: compile MiniX8 ou passe `--binary` com caminho válido.
- **GUI não abre**: instale Python 3/Tkinter e execute em sessão gráfica; container headless precisa de display encaminhado.
- **`opcode XX inválido`**: o PC encontrou byte ausente/errado; verifique ROM, origem e `mem`.
- **`ROM excede a memória`**: reduza a ROM ou escolha origem com espaço livre suficiente.
- **Sem saída para `IN`**: envie um byte ASCII pela GUI ou forneça stdin no terminal.

Mais mensagens e recuperação: [ERRORS.md](ERRORS.md). Plataformas, dependências e recursos não implementados: [QA.md](QA.md).
