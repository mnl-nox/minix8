# Mídia bootável para VM

`MiniX8-VM-boot.iso` é uma mídia live para inicialização em VM x86-64. Ela
carrega um kernel Linux, um initramfs em RAM com BusyBox, MiniX8, `hexrom`, ROM
de exemplo e uma seleção deste manual. Depois do boot aparece um shell
interativo; `HELP` lista comandos, `RUN` abre o monitor com `Oi!` e `DEVICES`
lista os barramentos publicados para o guest pelo kernel.

## O que esta imagem é

É um pequeno ambiente Linux de demonstração que hospeda a máquina virtual
didática MiniX8. A CPU de 8 bits, memória de 64 KiB e ISA são emuladas pelo
programa `minix8`. O Linux fornece o kernel e o shell para iniciar o emulador.
Não é um kernel 8-bit, clone de CP/M/MS-DOS, sistema instalado ou representação
de uma máquina comercial específica de 1987. A estética e os aliases de shell
fazem homenagem ao período.

## Executar

Use uma VM x86-64 (QEMU, VirtualBox ou VMware), pelo menos 256 MiB de RAM e
CD-ROM ligado à ISO. Ative firmware UEFI na configuração da VM. A ISO CI inclui
boot UEFI e BIOS legado quando `grub-mkrescue` oferece os dois alvos. A
construção local sem `grub-pc-bin` pode ser somente UEFI. Selecione a unidade
óptica como primeiro dispositivo de boot; não é preciso disco virtual.

QEMU com UEFI instalado no host:

```sh
qemu-system-x86_64 -m 256 -cdrom dist/MiniX8-VM-boot.iso -boot d \
  -bios /usr/share/OVMF/OVMF_CODE.fd
```

Para firmware BIOS tradicional, a ISO publicada pelo CI pode iniciar sem
`-bios`. Não grave a imagem em disco rígido como instalador: a raiz é montada
em RAM, alterações não são persistentes e desligar descarta os arquivos.

## Construir

Build local Linux requer compilador C com suporte a link estático, BusyBox
(preferencialmente `busybox-static`), kernel x86-64 em `/boot`, GRUB EFI
(`grub-mkimage`, módulos x86_64-efi), Python 3 e gzip. `grub-mkrescue`,
`grub-pc-bin` e `xorriso` habilitam também BIOS e a criação da ISO híbrida.

```sh
make boot-iso
```

O resultado fica em `dist/MiniX8-VM-boot.iso`. O CI instala ferramentas
necessárias e publica a imagem junto à ISO de dados nas releases. Consulte
[TOOLS.md](TOOLS.md) para dependências por sistema e [INSTALLATION.md](INSTALLATION.md)
para o emulador hospedeiro.

## Conteúdo e limites

- Kernel Linux x86-64 escolhido no host de build; não incluído no código-fonte.
- Initramfs BusyBox, ash, utilitários básicos, MiniX8 e conversor `hexrom`.
- ROM de exemplo, `HELP` local e manuais enxutos em `/usr/share/minix8/docs`.
- A rede, armazenamento persistente, GUI Tkinter e drivers adicionais não são
  configurados. A imagem requer CPU x86-64 e firmware compatível.
- `DEVICES` mostra as classes e barramentos publicados em `/sys` ao guest; o
  hipervisor decide quais periféricos são apresentados. Isso não controla o
  hardware do host.
- O sistema live é somente leitura exceto RAM; não há instalador ou atualização
  dentro do guest. Obtenha uma nova ISO para atualizar.

Consulte [ERRORS.md](ERRORS.md), [USER_GUIDE.md](USER_GUIDE.md) e
[COMMANDS.md](COMMANDS.md) para diagnóstico e detalhes dos comandos MiniX8.
