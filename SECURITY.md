# Segurança

## Limites de segurança

O MiniX8 executa ROMs como código de máquina convidado dentro do processo do emulador. A ROM pode ler de stdin e escrever em stdout através de `IN` e `OUT`, e pode consumir CPU até o limite configurado. O emulador não implementa syscalls, acesso convidado ao sistema de arquivos, rede, MMU ou sandbox de SO.

O carregador valida tamanho e erros de leitura antes de alterar RAM. Operandos e endereços são limitados a 8/16 bits, a RAM é exatamente 64 KiB, o monitor valida valores numéricos e a pilha detecta underflow/overflow. A execução por ROM tem limite padrão de 1.000.000 de instruções, configurável por `--steps`. `IN` pode bloquear esperando entrada, portanto esse limite não impõe timeout em chamadas de console.

Use containers ou mecanismos de isolamento do sistema hospedeiro para executar ROMs não confiáveis. A VM fornece contenção de memória convidada, não isolamento de processo.

## Relatar vulnerabilidades

Envie relatos sensíveis aos mantenedores por um canal privado, como GitHub Security Advisories se estiver habilitado no repositório. Inclua versão/commit, sistema e arquitetura hospedeiros, reprodução mínima e impacto observado. Evite publicar detalhes exploráveis antes de uma correção estar disponível.

## QA de segurança

`make qa` executa testes unitários/CLI, análise estática GCC e testes sob AddressSanitizer e UndefinedBehaviorSanitizer. LeakSanitizer é desativado neste alvo por incompatibilidade com ambientes que usam ptrace; isso não substitui revisão de alocação e liberação. A integração contínua executa o mesmo QA no Ubuntu e roda CTest nos alvos Linux, macOS e Windows.
