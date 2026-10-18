# Manual de comandos MiniX8

Este manual descreve os comandos realmente implementados. O vocabulário tem aliases inspirados em monitores de microcomputadores antigos; não é uma cópia de CP/M, MS-DOS, BASIC ou de uma máquina histórica. O sistema operacional e comandos de arquivos (`DIR`, `COPY`, `DEL`) continuam sendo os do computador hospedeiro.

## Iniciar pelo terminal

```sh
./minix8 --help
./minix8 --rom programa.rom
./minix8 --rom programa.rom --origin 0x8000 --steps 50000
./minix8 --rom programa.rom --raw-output
./minix8 --rom programa.rom --monitor
```

No Windows, use `minix8.exe` e a sintaxe de caminhos do PowerShell. `--origin` e `--steps` exigem `--rom`. A origem padrão é `0x0000`; a execução automática termina em `HLT`, falha da CPU ou limite de instruções.

## Monitor interativo

Sem ROM, o programa abre o monitor. `--monitor` mantém o monitor aberto depois de carregar uma ROM. Cada execução aceita no máximo 10 milhões de instruções para limitar uso acidental de CPU. Os comandos não diferenciam maiúsculas de minúsculas.

Por padrão, `OUT` escapa bytes ASCII de controle para reduzir sequências de
terminal maliciosas em ROMs não confiáveis. Use `--raw-output` somente quando
precisar da saída byte-a-byte e confiar na ROM; sequências de controle podem
alterar o terminal hospedeiro.

| Comando principal | Aliases retrô | Argumentos | Ação |
|---|---|---|---|
| `help` | `?` | — | Mostra todos os comandos |
| `regs` | `r`, `status` | — | Mostra A–D, PC, SP, flags, ciclos e HALT |
| `step` | `trace`, `t` | `[n]` | Executa uma instrução ou até `n` instruções |
| `run` | `go`, `g` | `[n]` | Executa até HLT/falha; padrão: 1.000.000 instruções |
| `reset` | `new` | — | Zera CPU e toda a RAM |
| `load` | `l` | `arquivo [endereço]` | Carrega ROM binária; origem padrão `0` |
| `mem` | `dump`, `d` | `endereço [tamanho]` | Exibe bytes em hexadecimal; padrão: 16 |
| `set` | `poke`, `p` | `endereço byte` | Escreve um byte na RAM |
| `quit` | `exit`, `x`, `q` | — | Fecha o monitor |

Endereços aceitam decimal ou prefixo `0x`; RAM vai de `0x0000` a `0xFFFF`, bytes de `0x00` a `0xFF`. ROMs são imagens binárias planas, sem cabeçalho. O monitor não contém assembler integrado; monte ROMs com [minix8_as.py](ASSEMBLY.md). Não implementa editor BASIC, desassemblador, diretórios virtuais, `SAVE`, `COPY` ou `DIR`.

Exemplo de sessão:

```text
minix8> load examples/hello.rom 0x0000
minix8> regs
minix8> t
minix8> d 0 16
minix8> g 100
minix8> x
```

## GUI desktop

`make gui` ou `python3 tools/minix8_gui.py` abre a bancada gráfica. **LOAD ROM** seleciona um arquivo, **RESET** reinicia e recarrega, **STEP** executa uma instrução, **RUN** usa o limite exibido, **REFRESH RAM** mostra `0x0000–0x007F`; o campo de comando encaminha comandos do monitor. **CPU INPUT** envia o primeiro caractere em UTF-8; um caractere multibyte consome uma instrução `IN` por byte.

## Conversão e criação de ROM

O conversor aceita dois dígitos hexadecimais por byte, separados por espaço/vírgula, comentários começando por `#` e arquivos de até 64 KiB:

```sh
python3 scripts/hex_to_rom.py exemplos.hex programa.rom
./minix8 --rom programa.rom --monitor
```

Programa `Oi!` de exemplo: `01 4F 19 01 69 19 01 21 19 1A`. `01` carrega byte imediato em A, `19` escreve A no console, `1A` para.

## Instruções da CPU

As instruções não são comandos digitados no monitor: são bytes executados por uma ROM. A tabela de todos os 37 opcodes, tamanhos, operandos, flags, pilha e entrada/saída fica em [ISA.md](ISA.md). O mapa por grupos é:

- `00`: NOP; `01–08`: loads/stores; `09–0E`: aritmética e lógica.
- `0F–13`: saltos; `14–17`: CALL/RET/PUSH/POP.
- `18–1A`: IN/OUT/HLT; `1B–1E`: incremento, decremento e shifts.
- `1F–24`: cópia de registradores.

## Erros e limites

Saída `0` indica término normal; `1`, erro de ROM/CPU/I/O; `2`, opção inválida. `run` limitado avisa ao atingir o orçamento. OpCodes inválidos, overflow/underflow de pilha e I/O falho encerram a execução com erro. A CPU tem 64 KiB de RAM, sem vídeo, áudio, interrupções, filesystem, temporizadores ou sistema operacional convidado. Veja [ERRORS.md](ERRORS.md) e [ARCHITECTURE.md](ARCHITECTURE.md).
