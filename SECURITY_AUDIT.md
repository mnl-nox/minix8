# Revisão de segurança do MiniX8

**Escopo:** revisão de código estática local do núcleo C11, CLI/monitor,
conversores de ROM, assembler e ferramentas de inventário. Data: 2026-10-17.
Isto não é certificação, pentest independente, nem auditoria do kernel, GRUB,
BusyBox, compilador ou hipervisor distribuído pela plataforma.

## Controles aplicados

- CPU usa RAM fixa de 65.536 bytes, operandos de 16 bits e acessos por `uint16_t`;
  chamadas e pilha verificam profundidade antes de ler/escrever.
- Carregador valida a capacidade disponível, detecta byte extra, erros de I/O e
  ROM vazia antes de copiar para RAM.
- Limite de execução: 1.000.000 de instruções por padrão e máximo de 10.000.000
  por chamada. Interrupção pelo usuário ainda depende do terminal.
- `OUT` escapa bytes ASCII de controle por padrão; `--raw-output` desativa essa
  proteção e deve ser usado somente com ROM confiável.
- Conversor C limita a ROM a 64 KiB e o fonte a 1 MiB; conversor Python aplica
  os mesmos limites. Assembler limita fonte a 2 MiB e ROM a 64 KiB, sem `eval`,
  execução de shell ou interpretação de expressões arbitrárias.
- GUI usa argumentos de processo como lista, decodifica texto UTF-8 com
  substituição segura e limita buffers de saída/filas.
- `minix8_devices.py` e `DEVICES` só leem APIs/sysfs do sistema; não abrem
  dispositivos, requisitam elevação, alteram configuração ou enviam dados.
- Build C aplica stack protector; Linux usa `_FORTIFY_SOURCE=2`. QA cobre
  AddressSanitizer, UndefinedBehaviorSanitizer, GCC `-fanalyzer`, testes de
  limites, CLI, assembler e conversores.
- Builds MSVC ativam `/GS` e Control Flow Guard (`/guard:cf`); `/utf-8` mantém
  literais consistentes e caminhos Windows passam por APIs wide após conversão
  UTF-8.

## Limites e riscos conhecidos

- O núcleo não é sandbox de sistema operacional. Uma ROM fica confinada à
  memória virtual, mas `IN` pode aguardar stdin e `OUT` pode produzir saída até
  o limite de passos. O processo mantém as permissões do usuário que o iniciou.
- Não há MMU, isolamento entre ROMs, vídeo/áudio, interrupções, DMA, filesystem,
  barramento de hardware ou drivers do MiniX8. A VM live é Linux/BusyBox e vê
  apenas os dispositivos virtuais apresentados pelo hipervisor.
- Inventário de periféricos é best-effort por API/driver e não enumera
  universalmente todo dispositivo, firmware, dispositivo desconectado ou
  interface sem permissão. Não implica suporte de emulação.
- Assembly nesta distribuição é a linguagem de montagem da CPU MiniX8. O
  interpretador crítico continua C11 portátil; não foi introduzido assembly
  nativo por arquitetura sem benchmark que demonstre ganho e sem backend testado
  equivalente em Windows/macOS/Linux.
- A imagem ISO depende de Linux kernel, GRUB, BusyBox e xorriso; esses projetos
  têm ciclos e políticas de segurança próprios. Verifique o checksum da release
  e a origem dos pacotes usados na build.

## Reprodução da QA

```sh
make qa
python3 tools/minix8_devices.py --json
python3 tools/minix8_as.py examples/hello.asm /tmp/hello.rom
./minix8 --rom /tmp/hello.rom
```

Reporte vulnerabilidades seguindo [SECURITY.md](SECURITY.md), incluindo versão,
plataforma, ROM mínima de reprodução e saída sanitizada. Não anexe ROMs ou logs
que contenham dados pessoais sem removê-los.
