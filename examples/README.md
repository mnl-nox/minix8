# ROMs de exemplo

- `hello.hex`: imprime `Oi!` e encerra.

Converta o texto hexadecimal para uma ROM binária e execute:

```sh
python3 scripts/hex_to_rom.py examples/hello.hex /tmp/hello.rom
./minix8 --rom /tmp/hello.rom
```

O formato `.hex` é uma conveniência para aprender e revisar bytes. A máquina executa arquivos binários brutos, sem cabeçalho nem relocação.
