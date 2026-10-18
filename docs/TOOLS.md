# Ferramentas e dependências

## Usar o MiniX8 no sistema hospedeiro

- Linux: binário x86-64 ou compilador C11 e GNU Make/CMake.
- macOS: binário ARM64 publicado ou toolchain C11 e Make/CMake.
- Windows: binário x86-64 `.exe` ou Visual Studio CMake/C compiler.
- Python 3 é necessário para scripts de ROM, testes e interface gráfica.
- `tools/minix8_as.py` monta mnemonics MiniX8; `tools/minix8_devices.py` faz
  inventário somente leitura dos dispositivos que o host publica.
- Tkinter só é necessário para `tools/minix8_gui.py`; o monitor de terminal não
  precisa de Python/Tk.
- A ISO de dados é criada pelo Python padrão. `xorriso` é opcional para
  extensões Rock Ridge.

## Criar a mídia bootável

Linux x86-64 é necessário para criar a imagem VM. O build precisa de kernel
Linux, BusyBox estático, compilador C com biblioteca estática, Python 3, gzip,
`grub-mkimage` e módulos GRUB `x86_64-efi`. `grub-mkrescue`, `grub-pc-bin` e
`xorriso` são usados para acrescentar boot BIOS; sem esse conjunto a mídia local
pode ser apenas UEFI. O CI prepara esses pacotes e também inclui kernel e
BusyBox no initramfs.

Para rodar, use um hipervisor x86-64 (QEMU, VirtualBox, VMware ou outro) com
firmware UEFI; a ISO de release também oferece BIOS legado. A VM não exige disco
virtual nem rede. Memória sugerida: 256 MiB.

## Ferramentas dentro do guest

O shell `ash` e utilitários vêm de BusyBox; estão disponíveis aliases retro
`HELP`, `DIR`, `CLS`, `VER`, `RUN` e `DEVICES`, além de `ls`, `cat`, `cp`, `mv`, `rm`,
`mkdir`, `pwd`, `vi`, `grep`, `find`, `hexdump`, `uname`, `reboot` e `poweroff`.
MiniX8 fornece seu próprio monitor e comandos; `hexrom` converte arquivos texto
hexadecimal para ROM. Veja [BOOTABLE_VM.md](BOOTABLE_VM.md) e a [matriz de
dispositivos virtuais e do host](DEVICES.md).

O inventário de dispositivos do host é best-effort por plataforma: sysfs no
Linux, `system_profiler` no macOS e PnP via PowerShell no Windows. Execute
`python3 tools/minix8_devices.py --json` para integração. Não existe descoberta
universal de todo dispositivo, acesso a firmware ou controle de hardware; o
scanner não abre interfaces de dispositivo e pode omitir dados sem permissão,
driver ou API do sistema.
