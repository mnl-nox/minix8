# Avisos de terceiros e redistribuição

O código original do MiniX8 é distribuído sob a GNU General Public License, versão 3 ou posterior (GPL-3.0-or-later). Consulte [LICENSE](LICENSE).

A ISO live para VM também reúne componentes de terceiros. A licença do MiniX8 não substitui as licenças desses componentes, e a licença de um componente não altera automaticamente a licença do código original do MiniX8.

## Componentes conhecidos da ISO live

| Componente | Origem | Licença do projeto | Observações |
|---|---|---|---|
| Kernel Linux | Kernel copiado do host de build, selecionado por `scripts/make_boot_iso.sh` | GPL-2.0-only, com arquivos individuais sujeitos a avisos/exceções próprios | A versão exata depende do runner ou do valor `KERNEL`. Registre a versão e disponibilize o código-fonte correspondente ao binário distribuído. |
| BusyBox | Executável fornecido pelo host ou por `BUSYBOX` | GPL-2.0-only, com avisos próprios quando aplicáveis | A versão exata depende do ambiente de build. Registre a versão e disponibilize o código-fonte correspondente. |
| GNU GRUB | Ferramentas e módulos instalados no host de build | GPL-3.0-or-later para o projeto GRUB, sujeito aos avisos específicos dos arquivos | A imagem EFI é gerada no host. Registre a versão e preserve os avisos aplicáveis. |
| MiniX8 e `hexrom` | Código deste repositório | GPL-3.0-or-later | Código-fonte disponível neste repositório. |

Fontes oficiais dos projetos: [Linux](https://kernel.org/), [BusyBox](https://busybox.net/), [GNU GRUB](https://www.gnu.org/software/grub/).

## Requisitos para releases com a ISO live

Como o kernel, BusyBox e GRUB vêm do ambiente de build, suas versões podem variar entre builds. Antes de tratar uma ISO como distribuição pronta para terceiros:

1. Registre as versões exatas dos componentes incorporados e os avisos de copyright/licença entregues por cada pacote.
2. Preserve ou inclua os textos de licença exigidos pelos pacotes e seus avisos.
3. Publique ou forneça, junto à release, o código-fonte correspondente e os materiais de build exigidos pelas licenças aplicáveis para os binários distribuídos.
4. Não afirme que a ISO está totalmente auditada enquanto esses dados e fontes não estiverem associados ao artefato.

A ISO de dados que contém apenas arquivos originais do MiniX8 deve continuar acompanhada desta licença e dos avisos pertinentes. Esta página é um inventário inicial; não substitui a verificação de cada pacote/binário concreto nem aconselhamento jurídico.
