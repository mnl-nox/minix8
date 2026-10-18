# Referências e leituras

Estas fontes apoiam o estudo de sistemas operacionais, dispositivos e desenho de drivers. São materiais externos; sua inclusão não indica compatibilidade de código ou patrocínio.

## Andrew S. Tanenbaum

- Andrew S. Tanenbaum e Albert S. Woodhull, *Operating Systems: Design and Implementation*, 3ª edição, Pearson/Prentice Hall, 2006. ISBN 978-0-13-142938-3. Apresenta princípios de sistemas operacionais junto da implementação MINIX 3. [Registro editorial InformIT/Pearson](https://www.informit.com/store/operating-systems-design-and-implementation-9780131429383).
- Andrew S. Tanenbaum e Herbert Bos, *Modern Operating Systems*, 5ª edição, Pearson, 2022/2023. ISBN 978-0-13-761893-4. Inclui processos, memória, sistemas de arquivos, I/O, virtualização e segurança. [Página editorial Pearson](https://www.pearson.com/en-us/subject-catalog/p/modern-operating-systems/P200000003295/9780137618934).

Consulte bibliotecas ou editoras para obter os livros; este projeto não distribui cópias.

## Documentação MINIX 3

- [MINIX 3 Developers Guide: visão geral dos drivers](https://wiki.minix3.org/doku.php?id=developersguide:overviewofminixdrivers) — drivers de caractere/bloco, processos em user mode e bibliotecas `chardriver`, `blockdriver`, `inputdriver` e `netdriver`.
- [Tutorial de programação de drivers](https://wiki.minix3.org/doku.php?id=releases:3.2.0:developersguide:driverprogramming) — exemplos de driver e protocolos; página de release antiga, verificar contra o código/documentação atual do MINIX antes de usá-la.
- [Protocolo Data Link](https://wiki.minix3.org/doku.php?id=developersguide:datalinkprotocol) — protocolo de rede entre servidor `inet` e drivers Ethernet.
- [Configuração de rede](https://wiki.minix3.org/doku.php?id=usersguide:networkconfiguration) — adaptadores e configuração de MINIX 3, incluindo cenários virtualizados.
- [MINIX 3 em QEMU/KVM](https://wiki.minix3.org/doku.php?id=usersguide:runningonqemu) — uso de dispositivos de rede/armazenamento virtio com MINIX 3.
- [Manual do serviço `inet`](https://man.minix3.org/cgi-bin/man.cgi?apropos=0&manpath=Minix&query=inet&sektion=8) — serviço de rede TCP/IP do MINIX.

As referências explicam decisões de MINIX 3. MiniX8 é outro projeto: seu núcleo atual não implementa microkernel, processos de driver, protocolo de rede ou dispositivos virtuais correspondentes. O estado detalhado está em [DEVICES.md](DEVICES.md).
