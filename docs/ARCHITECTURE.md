# Arquitetura do MiniX8

MiniX8 é uma máquina virtual de processo único. O programa hospedeiro contém a CPU e a RAM; a ROM é uma imagem binária plana carregada na memória. Não existe firmware obrigatório, sistema operacional convidado ou formato de executável proprietário.

## Componentes

- **CPU:** biblioteca de núcleo em `src/minix8_core.c`/`.h`, com quatro registradores gerais de 8 bits (A–D), PC/SP de 16 bits e flags N/Z/C. `src/minix8.c` contém o carregador e a CLI/monitor.
- **Memória:** 65.536 bytes zerados no reset. Código e dados podem ocupar qualquer endereço.
- **Pilha:** começa em `0xFFFF`, cresce para endereços menores. PUSH/CALL gravam na posição apontada por SP e depois decrementam SP.
- **Console:** IN bloqueia esperando um byte em stdin; EOF vira zero. OUT escreve um byte de A para stdout e o descarrega imediatamente.
- **Monitor:** permite executar instruções, inspecionar registradores e RAM, carregar imagens e escrever bytes manualmente.
- **Carregador:** aceita um arquivo binário bruto de até `65536 - origem` bytes. A execução começa no endereço de carga: `0x0000` por padrão ou o valor de `--origin`.

## Ciclo da CPU

1. Se a CPU está em HLT, o ciclo não faz nada.
2. O byte em PC é lido como opcode e PC avança.
3. A instrução lê os operandos sequenciais, também avançando PC.
4. A CPU atualiza registradores, flags, memória, pilha, console ou PC.
5. Um opcode inválido, erro de pilha ou falha de I/O reporta o endereço e interrompe a execução.

O contador de ciclos é um contador de instruções tentadas, não uma simulação de frequência ou tempo real. Ramos condicionais contam como uma instrução, assim como todos os demais opcodes; uma instrução que falha também é contada.

## Decisões e limites atuais

- Sem MMU, modos privilegiados, interrupções, DMA, temporizadores ou periféricos de vídeo/áudio.
- Sem montagem/assembler embutido: desenvolvedores podem gerar os bytes com qualquer assembler ou ferramenta externa, segundo [ISA.md](ISA.md).
- Sem temporização de console e sem modo raw de terminal; IN usa a semântica de stdin do sistema hospedeiro.
- Reset limpa RAM e estado da CPU. Carregar uma ROM no monitor define PC para a origem e remove o estado de HLT/falha, preservando os demais registradores.
- O carregador valida o tamanho e a leitura completa antes de copiar bytes para RAM; ROM grande ou com erro de I/O não altera a memória existente.
- Underflow e overflow da pilha são falhas da CPU e retornam status de processo diferente de zero. A pilha tem profundidade máxima de 65.536 bytes.
- Endereços e limites de execução são analisados sem truncamento; argumentos fora da faixa são rejeitados antes da execução.

Essas escolhas mantêm o núcleo pequeno, previsível e compilável em toolchains C11 comuns. Novas instruções devem receber opcodes não usados, atualizar a tabela de [ISA.md](ISA.md), e preservar a regra de uma instrução por ciclo.

## QA

`make test` executa testes unitários do núcleo e testes CLI em subprocessos temporários. `make sanitize` compila ambos com AddressSanitizer e UndefinedBehaviorSanitizer; `make analyze` roda `-fanalyzer` do GCC com warnings tratados como erros; `make qa` executa tudo. Os testes unitários linkam a biblioteca pública de núcleo, sem incluir o arquivo de implementação. O LeakSanitizer fica desativado no alvo local por compatibilidade com ambientes que executam processos sob ptrace. No CMake, use `ctest --test-dir build --output-on-failure`.
