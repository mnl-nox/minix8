# Mídia de distribuição MiniX8 1987

`MiniX8-1987.iso` é uma imagem de dados ISO9660/Joliet (Rock Ridge quando criada com `xorriso`). Ela reúne os executáveis da release para Linux x86-64, macOS ARM64 e Windows x86-64, fontes C, documentação, site estático, conversor de ROM e exemplos. A ROM binária `examples/hello.rom` está pronta para execução e os lançadores `START-UNIX.sh`/`START-WINDOWS.bat` abrem o monitor com ela carregada.

Para inicializar MiniX8 dentro de uma VM, use a imagem separada
[`MiniX8-VM-boot.iso`](BOOTABLE_VM.md). Essa mídia live inclui kernel Linux e
BusyBox para hospedar o emulador; não é a ISO de dados nem um OS 8-bit próprio.

## Limite essencial

Esta ISO **não é bootável** e não instala um sistema operacional. O MiniX8 é um processo C11 que roda sobre um sistema hospedeiro. Monte a imagem no sistema atual, copie os arquivos para uma pasta e execute o binário correspondente à plataforma. O rótulo “1987” descreve a direção visual retrô; o projeto não emula um computador histórico específico nem reproduz exatamente um sistema/ROM de 1987.

## Criar localmente

Requer compilador C11, Python 3 e `sha256sum`. O gerador Python embutido produz ISO9660/Joliet sem dependências externas. Se `xorriso` (ou `genisoimage`/`mkisofs`) estiver instalado, o script o usa para acrescentar Rock Ridge:

```sh
# Debian/Ubuntu: Python basta; xorriso é opcional
sudo apt-get install python3 xorriso

# Gere primeiro o binário local e depois a mídia:
make
make iso
```

O resultado padrão é `dist/MiniX8-1987.iso`. Uma build local inclui o binário Linux compilado nessa máquina. Para montar uma distribuição com todos os alvos, passe ao script os artefatos da matriz CI:

```sh
scripts/make_iso.sh dist/MiniX8-1987.iso dist/platforms
```

O diretório `dist/platforms` deve conter diretórios `minix8-linux-x86_64`, `minix8-macos-arm64` e `minix8-windows-x86_64`, cada um com o binário de mesmo nome (Windows com sufixo `.exe`). O CI valida a presença dos três binários antes de publicar a ISO.

## Conteúdo

- `bin/`: executáveis disponíveis, identificados por plataforma.
- `source/`: núcleo C11, conversores, assembler virtual, scanner, testes e frontend Tkinter.
- `examples/`: fontes `.hex` e assembly MiniX8, mais ROM `.rom` executável.
- `docs/`: guia do usuário, comandos, assembly, VM, arquitetura, ISA, segurança, erros, QA e CI/CD.
- `site/`: site estático com versão ligada ao projeto e links para os guias.
- `BUILD-INFO.txt`: versão/revisão; `SECURITY_AUDIT.md`: escopo e limites da revisão.
- `MANIFEST.sha256`: checksums dos arquivos da mídia, exceto o próprio manifesto.

O processo também cria `MiniX8-1987.iso.sha256` ao lado da imagem. No Linux,
entre em `dist/` e rode `sha256sum -c MiniX8-1987.iso.sha256`; no macOS compare
com `shasum -a 256 MiniX8-1987.iso`.

O pacote não inclui toolchain, BIOS, bootloader, kernel, software de terceiros ou garantia de ABI para todas as distribuições. Linux antigo com glibc incompatível pode compilar as fontes localmente.
