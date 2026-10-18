# Assembly MiniX8

O assembler `tools/minix8_as.py` traduz mnemonics do ISA MiniX8 em uma ROM
binária plana. Ele usa apenas Python 3 e não executa código do arquivo fonte.
Identificadores são restritos a ASCII; strings `DB` e mensagens são UTF-8.

```sh
python3 tools/minix8_as.py examples/hello.asm /tmp/hello.rom
./minix8 --rom /tmp/hello.rom --monitor
```

Exemplo:

```asm
start:
    LDA #0x4F       ; A recebe 'O'
    OUT
    LDA #0x69
    OUT
    JMP start       ; salto absoluto para o rótulo
```

## Sintaxe suportada

- Mnemonics e semântica: [ISA.md](ISA.md). Imediatos usam `#`, por exemplo
  `LDA #42` ou `LDA #0x2A`.
- Loads/stores absolutos: `LDA 0x1234`, `STA 0x1234`; saltos e CALL aceitam
  rótulos ou endereços absolutos de 16 bits.
- `MOV A,B` aceita apenas os pares existentes na ISA.
- `DB 0x01, 2, "UTF-8"` insere bytes; strings são codificadas em UTF-8 e não
  recebem terminador NUL automático.
- `;` inicia comentários fora de strings. Endereço de origem opcional:
  `--origin 0x8000`; o assembler não preenche o intervalo até essa origem,
  então carregue a ROM também com `--origin 0x8000`.
- O fonte está limitado a 2 MiB e a imagem não pode exceder os 64 KiB de RAM.

O assembler gera a ISA virtual do MiniX8, não código x86/ARM nativo. O núcleo
do emulador permanece C11 portátil; essa separação mantém os builds de Windows,
macOS e Linux consistentes e deixa a ROM auditável em bytes.
