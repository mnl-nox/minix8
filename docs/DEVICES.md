# Dispositivos, integração e compatibilidade

Este documento separa os recursos da máquina virtual dos dispositivos reais que o sistema hospedeiro informa. MiniX8 é uma VM didática de processo único, não uma distribuição MINIX 3 nem um emulador de PC x86. A GUI e o scanner de dispositivos estão prontos para uso; eles não adicionam hardware virtual à CPU.

## O que funciona hoje

| Recurso | Estado | Como funciona |
| --- | --- | --- |
| CPU, RAM e pilha virtuais | Implementado | CPU de 8 bits, 64 KiB de RAM e ISA descrita em [ISA.md](ISA.md). |
| Console de saída | Implementado | `OUT` escreve o byte de A em stdout; a GUI exibe a saída do processo. |
| Entrada de console | Implementado | `IN` lê um byte de stdin. A GUI envia bytes UTF-8, uma instrução `IN` por byte. |
| GUI desktop | Implementado | Tkinter controla o executável C: carrega `.rom`/`.bin`, monta `.asm`, converte `.hex`, executa passo a passo e mostra CPU/RAM. |
| Inventário do host | Implementado, best-effort, somente leitura | `DEVICES` na GUI ou `python3 tools/minix8_devices.py --json` consulta APIs do Linux, macOS ou Windows. |
| Carregamento de ROM | Implementado | Abrir arquivo via GUI ou `--rom` CLI; isso não monta o sistema de arquivos do host dentro da VM. |

O inventário pode listar categorias como armazenamento, rede, entrada, áudio, vídeo, portas seriais, Bluetooth e barramentos USB/PCI quando o sistema as publica. A cobertura depende de sistema operacional, APIs, permissões, drivers e hardware. A listagem identifica recursos do **host**; não concede acesso, não testa funcionamento e não significa que a CPU virtual consiga usá-los.

## Periféricos virtuais: suporte atual e possibilidades

| Classe | Suporte atual na CPU virtual | Caminho possível |
| --- | --- | --- |
| Terminal/TTY | Entrada e saída byte a byte por `IN`/`OUT`; sem registradores de dispositivo | Formalizar UART virtual, baud/timing opcionais e buffers limitados. |
| Teclado | Não há dispositivo independente; texto enviado pela GUI alimenta `IN` | Eventos de tecla normalizados ligados a uma UART/console virtual. |
| Vídeo/framebuffer | Não há framebuffer; GUI é apenas painel de controle | Dispositivo framebuffer com formato, dimensões, limites de memória e atualização documentados. |
| Contador de instruções | Parcial: `GETCYC` (`0x25`) lê os bits 0–7 e `GETCYH` (`0x26`) os bits 8–15 do contador de instruções, incluindo a instrução de leitura | Já disponível para loops e contagens determinísticas; não equivale a tempo de parede nem a um timer de hardware. | 
| Timer/interrupções | Não implementado | Adicionar timer virtual e fila determinística de eventos, com comportamento de reset e limites testados, antes de considerar interrupções. |
| Armazenamento em bloco | Não há disco virtual, filesystem guest ou passthrough | Imagem de disco explicitamente selecionada, operações limitadas por faixa e somente sobre o arquivo da VM. |
| Rede | Não há NIC, pilha TCP/IP, sockets ou tráfego de pacotes do guest | Adaptador virtual mediado pelo host (por exemplo, backend UDP ou rede isolada), com permissões explícitas e limites de tráfego. |
| Áudio, USB, Bluetooth, sensores | Não há emulação nem passthrough | Interfaces virtuais por classe, cada uma com especificação, autorização, limites e testes próprios. |

“Pode vir” indica uma direção de projeto, não compromisso de versão ou compatibilidade já disponível. A lista de hardware do host não prevê quais recursos serão adicionados à ISA.

## Fluxo de programação hoje

1. Escreva assembly da ISA virtual MiniX8 em UTF-8, por exemplo `examples/hello.asm`.
2. Monte com `python3 tools/minix8_as.py examples/hello.asm /tmp/hello.rom`, ou abra `.asm` pelo botão **LOAD ROM** na GUI.
3. Execute na GUI com **STEP/RUN**, examine registradores e RAM, e envie bytes ao `IN` pelo campo **CPU INPUT**.
4. Para CLI, rode `./minix8 --rom /tmp/hello.rom`; `IN`/`OUT` usam stdin/stdout.

O assembler converte texto Unicode em bytes de código-fonte e comentários, mas a ROM e os registradores continuam byte-oriented. Texto Unicode impresso requer que o programa emita os bytes UTF-8 correspondentes, um por vez. Veja [ASSEMBLY.md](ASSEMBLY.md), [GUI.md](GUI.md) e [COMMANDS.md](COMMANDS.md).

## Princípios de arquitetura para novos dispositivos

A documentação MINIX 3 é referência de projeto, não código ou drivers diretamente compatíveis com MiniX8. MINIX 3 separa drivers e serviços, define protocolos entre componentes e documenta uma interface específica entre o servidor `inet` e drivers Ethernet. Isso inspira uma possível arquitetura MiniX8 com:

1. API de dispositivo virtual pequena e versionada entre núcleo e frontend;
2. registro explícito de dispositivos e mapa de endereços/portas sem conflitos;
3. operações com comprimentos, estado e erros validados antes de acessar buffers;
4. IO mediado pelo host, permissões mínimas e nenhuma abertura implícita de hardware real;
5. comportamento determinístico, limites de instruções/dados e testes por dispositivo.

Drivers de MINIX 3 rodam como componentes de seu próprio sistema, usam APIs e permissões do microkernel MINIX e não são binários que possam ser carregados nesta VM. Não reutilize uma página de dispositivos do host como se fosse uma interface emulada.

## Referências técnicas

- [Visão geral dos drivers MINIX 3](https://wiki.minix3.org/doku.php?id=developersguide:overviewofminixdrivers): categorias character/block, componentes em user mode e bibliotecas de abstração.
- [Programação de drivers MINIX 3](https://wiki.minix3.org/doku.php?id=releases:3.2.0:developersguide:driverprogramming): tutorial de drivers e APIs específicas do MINIX; a própria página identifica detalhes potencialmente antigos.
- [Protocolo Data Link](https://wiki.minix3.org/doku.php?id=developersguide:datalinkprotocol): interface entre `inet` e drivers Ethernet.
- [Configuração de rede MINIX 3](https://wiki.minix3.org/doku.php?id=usersguide:networkconfiguration): configuração e exemplos de adaptadores reconhecidos pelo MINIX, que não representam suporte MiniX8.
- [MINIX 3 em QEMU/KVM](https://wiki.minix3.org/doku.php?id=usersguide:runningonqemu): exemplo de dispositivos virtio em MINIX 3.
- [Livros e outras referências](REFERENCES.md).

Veja também o [roadmap e issues de implementação](ROADMAP.md), [TOOLS.md](TOOLS.md), [ARCHITECTURE.md](ARCHITECTURE.md) e [SECURITY_AUDIT.md](../SECURITY_AUDIT.md).
