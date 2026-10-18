# QA, cobertura e compatibilidade

## Executar QA local

```sh
make test      # unidade + CLI
make sanitize  # unidade + CLI sob AddressSanitizer/UBSan
make analyze   # GCC -fanalyzer com -Werror
make qa        # os três alvos
```

`make qa` precisa de GCC 10+ (para `-fanalyzer`), Python 3 e compilador com AddressSanitizer/UBSan. LeakSanitizer é desativado pelo Makefile por incompatibilidade com ambientes executados sob ptrace; AddressSanitizer e UBSan permanecem ativos. Não é uma certificação de segurança nem teste exaustivo de todas as ROMs.

CMake configura o binário e os testes unitários; quando encontra Python, ativa também os testes de CLI:

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug
cmake --build build --parallel
ctest --test-dir build --output-on-failure
```

## O que os testes cobrem

- Aritmética, flags, lógica, deslocamentos, cópias de registradores, saltos, memória, pilha, HLT e opcode inválido.
- CLI: saída por ROM, entrada/saída, origem/PC, limite superior de RAM, parâmetros incorretos, ROM oversized e comandos do monitor.
- Frontend Tkinter: verificação de sintaxe Python na QA; interação gráfica exige sessão desktop e é validada manualmente.
- Análise estática GCC no núcleo e CLI.
- Limites do conversor C de ROM, montagem de labels/UTF-8, rejeição de fonte
  excessiva, ROM vazia, limite de execução, round-trip UTF-8 no console e
  escape seguro de bytes de controle do terminal.
- `tools/minix8_devices.py --json` verificado manualmente no runner Linux; as
  APIs macOS/Windows são verificadas como Python, mas precisam de hosts nativos
  para validação de integração.
- Limites do conversor C de ROM, montagem de labels/UTF-8, rejeição de fonte
  excessiva, ROM vazia, limite de execução e round-trip UTF-8 no console.
- `tools/minix8_devices.py --json` verificado manualmente no runner Linux; as
  APIs macOS/Windows são compiladas como Python, mas requerem seus hosts nativos
  para validação de integração.
- Ações por commit/PR: CI executa `make qa`, CTest em Linux/macOS/Windows e build em Debian/Fedora.

Os casos de erro emitem mensagens esperadas no stderr. O contador de ciclos é testado como contador de instruções, não como temporização.

## Plataformas configuradas no CI

| Runner | Artefato | Observação |
|---|---|---|
| Ubuntu 22.04 x86-64 | Linux | ABI compilada em Ubuntu 22.04; pode exigir glibc mais nova que a do host |
| macOS 14 ARM64 | macOS Apple Silicon | Não é um binário universal Intel/ARM |
| Windows Server 2022 x86-64 | Windows | Build CMake/MSVC |
| Debian stable container | Build de fonte | Não gera binário Debian `.deb` |
| Fedora container | Build de fonte | Não gera RPM |

VMs Linux/Windows usam o mesmo binário da plataforma hospedeira. Imagens Docker/Podman usam kernel Linux do host; não são VMs completas. Sistemas ARM Linux, Windows ARM, macOS Intel e distribuições libc-musl não têm artefatos precompilados nesta matriz, mas podem compilar se houver toolchain C11 compatível.
