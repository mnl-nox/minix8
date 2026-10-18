# Interface gráfica desktop

O MiniX8 inclui um frontend desktop funcional em Python/Tkinter com visual de terminal fósforo dos anos 1980. A CPU continua sendo o executável C `minix8`; a interface inicia e controla esse processo pelo monitor embutido. Não substitui nem altera a ISA e não requer biblioteca gráfica no núcleo. A janela permite carregar `.rom`/`.bin` e compilar `.hex`/`.asm` antes de executar.

## Requisitos

- Binário `minix8` compilado e acessível no diretório do projeto ou no `PATH`.
- Python 3 com Tkinter/Tcl-Tk. No Debian/Ubuntu, se necessário: `sudo apt install python3-tk`.
- Ambiente gráfico local. Sessões SSH sem display precisam de X forwarding ou desktop remoto.

## Iniciar

Na raiz do repositório:

```sh
make
python3 scripts/hex_to_rom.py examples/hello.hex /tmp/hello.rom
python3 tools/minix8_gui.py
python3 tools/minix8_gui.py --rom /tmp/hello.rom
python3 tools/minix8_gui.py --binary ./build/minix8 --rom /caminho/programa.rom
```

No Windows, compile com CMake e rode `py tools\minix8_gui.py --binary build\Release\minix8.exe`. No macOS, instale um Python com Tcl/Tk e rode o mesmo script pelo Terminal.

## Controles

- **LOAD ROM** abre o seletor e reinicia a máquina. Aceita `.rom`/`.bin` e
  converte `.hex` ou `.asm` para uma ROM temporária antes de carregar.
- **RESET** reinicia CPU e RAM e recarrega a ROM atualmente selecionada.
- **STEP** avança uma instrução. **RUN** executa até o limite configurado, HLT ou falha.
- **REFRESH RAM** mostra os primeiros 128 bytes de RAM; o monitor também permite `mem endereço [tamanho]` e `set endereço byte`.
- **CPU INPUT** envia um caractere UTF-8 à instrução `IN`; caracteres
  multibyte consomem uma instrução por byte.
- **DEVICES** abre um inventário somente leitura dos dispositivos publicados
  pelo sistema hospedeiro.
- **DEVICES** não conecta hardware à VM: não há passthrough, barramento virtual,
  adaptador de rede, disco guest ou driver MiniX8.
- A entrada `minix8>` envia comandos do monitor (`help`, `regs`, `step`, `run`, `mem`, `set`, `quit`).

## Limites

- Tkinter é uma interface de controle; não emula a CPU por conta própria. O processo e o binário C precisam estar instalados.
- Não é executada em containers headless sem encaminhamento de display.
- A visualização de RAM começa em `0000`; para outros endereços, use `mem` no monitor.
- O canal de CPU é de um byte; entrada UTF-8 multibyte requer uma instrução
  `IN` para cada byte codificado.
- O campo de comando do monitor não trata caminhos com espaços no comando `load`; use o botão **LOAD ROM**, que abre arquivo por caminho nativo.
- O `.hex` é texto de exemplo, não ROM executável. Converta-o para binário antes de carregar.

## Diagnóstico

Se a janela não abrir, instale Python/Tk e confirme a variável/display gráfico do sistema. Se aparecer “EXECUTÁVEL NÃO ENCONTRADO”, compile com `make` ou passe `--binary`. A saída completa do processo aparece na janela; mensagens de erro usam destaque âmbar.
