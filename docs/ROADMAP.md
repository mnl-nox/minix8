# Roadmap de dispositivos virtuais

Este roadmap distingue o que está implementado do que está planejado. A detecção de hardware do sistema hospedeiro é informativa e somente leitura; ela não torna esses dispositivos acessíveis à CPU virtual.

## Entregável desta etapa

- **Implementado nesta branch:** `GETCYC` (`0x25`) e `GETCYH` (`0x26`) expõem os 16 bits inferiores do contador de instruções. A leitura inclui a instrução atual e atualiza as flags N/Z.
- **Uso:** `GETCYC` lê bits 0–7; `GETCYH` lê bits 8–15. São contagens determinísticas de instruções, não segundos, relógio de parede, timer independente ou interrupções.
- **Validação:** os testes de núcleo cobrem a leitura e o rollover; os testes do assembler garantem codificação e rejeição de operandos inválidos. O merge depende de CI verde.

## Próximas etapas

1. [#18 — Desacoplar console virtual de stdin/stdout](https://github.com/mnl-nox/minix8/issues/18): interface de I/O com callbacks e backend CLI compatível.
2. [#17 — Timer virtual determinístico e fila de eventos](https://github.com/mnl-nox/minix8/issues/17): estados, rollover, reset e ordenação de eventos reproduzíveis.
3. [#19 — Framebuffer virtual limitado](https://github.com/mnl-nox/minix8/issues/19): dimensões e formato de pixel limitados, renderização na GUI sem acesso arbitrário ao host.
4. [#20 — Armazenamento virtual baseado em imagem de disco](https://github.com/mnl-nox/minix8/issues/20): arquivo explicitamente selecionado, limites de faixa e sem passthrough de disco físico.
5. [#21 — Especificar interrupções e isolamento de memória](https://github.com/mnl-nox/minix8/issues/21): especificação e análise de compatibilidade antes de qualquer implementação incompatível.

O issue agregador [#15 — Implementar periféricos virtuais úteis](https://github.com/mnl-nox/minix8/issues/15) acompanha o progresso entre etapas.

## Regras de engenharia

- Cada dispositivo tem um contrato versionado: identificador, registradores/portas, estados, erros, limites e reset.
- Nenhum dispositivo abre hardware físico nem acessa recursos do host sem uma interface mediada e explícita.
- O comportamento virtual deve ser determinístico sempre que possível e coberto por testes de limites, falhas e reset.
- Documentação da ISA, arquitetura, guia de uso, README e site devem ser atualizados na mesma etapa funcional.
- Não criar tag/release antes de todos os checks obrigatórios estarem verdes. Releases são geradas pelo workflow de CI após integração na `main`.
