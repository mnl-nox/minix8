# Erros e diagnóstico

## Status de saída

| Status | Significado | Ação |
|---:|---|---|
| 0 | Ajuda, saída normal, HLT ou limite de instruções alcançado | Nenhuma; um limite alcançado aparece como aviso em stdout |
| 1 | Falha de abertura/leitura de ROM, ROM grande demais, falta de memória ou falha da CPU/I/O | Confira caminho/tamanho/ROM; veja stderr e endereço reportado |
| 2 | Opção CLI ou valor inválido | Corrija argumentos conforme `--help` |

## Mensagens comuns

| Mensagem | Causa | Recuperação |
|---|---|---|
| `Não foi possível abrir ...` | Caminho inexistente ou sem permissão de leitura | Confira o caminho e permissões no sistema hospedeiro |
| `ROM excede a memória disponível ...` | Bytes ultrapassam `65536 - origem` | Reduza ROM ou escolha uma origem com espaço suficiente |
| `Endereço de origem inválido` | Origem não é inteiro entre 0 e 65535 | Use decimal ou hexadecimal `0x...` nessa faixa |
| `Limite de instruções inválido` | Valor zero, negativo, incompleto ou fora da faixa uint64 | Use inteiro positivo, como `--steps 50000` |
| `--origin requer --rom` / `--steps requer --rom` | Opção de execução automática usada sem uma ROM | Informe `--rom`; no monitor use `run [n]` |
| `opcode XX inválido` | PC apontou para um byte não definido na ISA | Inspecione `PC` e `mem`; confira montagem e fluxo de execução |
| `underflow da pilha em POP/RET` | Programa retirou mais bytes do que empilhou | Balanceie PUSH/POP e CALL/RET |
| `overflow da pilha em PUSH/CALL` | Pilha já ocupou todos os 65.536 bytes | Reduza recursão ou quantidade de dados empilhados |
| `falha de leitura em IN` / `falha de escrita em OUT` | Erro de stdin/stdout do sistema hospedeiro | Verifique redirecionamento, terminal e destino de saída |
| `Linha longa demais; comando descartado.` | Comando do monitor excedeu o buffer de 511 caracteres | Envie um comando menor |
| `Endereço ou tamanho inválido.` / `Uso: set ...` | Parâmetros do monitor fora da faixa ou malformados | Use endereço 0–65535 e byte 0–255 |

## Diagnóstico no monitor

1. Rode `regs` para obter PC, SP, flags e ciclos.
2. Rode `mem <PC> 16` para inspecionar os bytes no ponto atual.
3. Use `step 1` para avançar com granularidade. Para avançar após HLT ou falha, use `reset` e recarregue a ROM.
4. A carga de ROM é atômica: uma ROM grande/inacessível não modifica a RAM já existente.

Falhas da CPU escrevem endereço e causa em stderr, marcam CPU como HLT/falha e retornam status de processo 1 quando o monitor termina. HLT normal retorna 0. Consulte [ISA.md](ISA.md) para opcodes e flags.
