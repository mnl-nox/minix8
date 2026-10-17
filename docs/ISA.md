# MiniX8: arquitetura e conjunto de instruções

## Modelo e convenções

- CPU de 8 bits, registradores A, B, C e D e PC/SP de 16 bits.
- 64 KiB de RAM endereçável por byte. ROM/binário é carregado a partir de `0x0000` por padrão.
- Endereços e operandos de 16 bits são little-endian. SP inicia em `0xFFFF`; a pilha cresce para baixo.
- FLAGS: Z (bit 0, resultado zero), C (bit 1, carry ou indicação de não-borrow), N (bit 2, bit mais alto do resultado).
- `IN A` lê um byte de stdin (EOF retorna zero); `OUT A` escreve A como caractere em stdout.
- Uma instrução custa um ciclo no modelo atual. Não há periféricos temporizados.
- PC avança após cada byte lido e retorna a zero após `0xFFFF`. RAM não é protegida: código, dados e pilha compartilham o mesmo espaço.
- Os registradores gerais são de 8 bits. A pilha guarda bytes; CALL empilha o endereço de retorno de 16 bits e RET o recupera.

Loads, operações aritméticas/lógicas, comparações, deslocamentos, incrementos/decrementos e movimentos atualizam N e Z. Em geral preservam C, exceto operações que definem carry. Stores, saltos, NOP, CALL, RET, PUSH, OUT e HLT preservam todas as flags. POP atualiza N/Z e preserva C.

## Códigos

| Hex | Instrução | Bytes | Efeito |
|---|---|---:|---|
| 00 | NOP | 1 | Sem operação |
| 01–04 | LDA/LDB/LDC/LDD #byte | 2 | Carrega imediato |
| 05 | LDA endereço | 3 | A ← RAM[addr] |
| 06 | STA endereço | 3 | RAM[addr] ← A |
| 07 | LDB endereço | 3 | B ← RAM[addr] |
| 08 | STB endereço | 3 | RAM[addr] ← B |
| 09–0E | ADD/SUB/AND/OR/XOR/CMP B | 1 | Aritmética/lógica A com B; CMP atualiza flags sem gravar A. SUB/CMP definem C se A ≥ B; caso contrário indicam borrow |
| 0F–13 | JMP/JZ/JNZ/JC/JNC endereço | 3 | Salto absoluto, condicional por Z/C |
| 14–15 | CALL/RET | 3/1 | Chamada e retorno usando a pilha; CALL precisa de dois bytes livres e RET de dois bytes empilhados |
| 16–17 | PUSH/POP A | 1 | Empilha/desempilha A; pilha cheia/vazia gera falha da CPU |
| 18–19 | IN/OUT A | 1 | Entrada/saída de console |
| 1A | HLT | 1 | Para a CPU |
| 1B–1C | INC/DEC A | 1 | Incrementa/decrementa A |
| 1D–1E | SHL/SHR A | 1 | Desloca A; bit deslocado vai para C |
| 1F–24 | MOV A,B / MOV B,A / MOV A,C / MOV C,A / MOV A,D / MOV D,A | 1 | Cópia de registrador |

ADD define C quando a soma ultrapassa `0xFF`. SUB e CMP definem C quando não há borrow. SHL define C com o bit 7 anterior; SHR com o bit 0 anterior. N sempre espelha o bit 7 do resultado, mesmo em operações de comparação.

Instrução desconhecida interrompe a CPU com erro. Saltos e acesso à RAM usam endereços de 16 bits. Falhas de opcode, pilha ou I/O interrompem a execução e fazem o processo retornar status diferente de zero. A tentativa de instrução é contada no contador de ciclos.
