# Contribuir

## Fluxo

1. Crie uma branch a partir de `main`.
2. Faça mudanças pequenas e compile em C11 com avisos habilitados (`make` ou CMake).
3. Abra um pull request para `main`. O CI valida os títulos das mensagens, compila Linux, macOS e Windows e verifica build em imagens Debian e Fedora.
4. Use mensagens [Conventional Commits](https://www.conventionalcommits.org/), por exemplo `feat(cpu): add carry rotate` ou `fix(monitor): reject invalid address`.

## Tipos aceitos

`feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore` e `revert`. Formato: `tipo(escopo opcional): resumo` em minúsculas. Use `!` ou um rodapé `BREAKING CHANGE:` para mudanças incompatíveis.

## Releases automáticas

Após um commit `feat` ser enviado diretamente ou integrado em `main`, o workflow calcula a próxima versão menor e cria uma tag `vMAJOR.MINOR.PATCH`. Uma mudança marcada como breaking (`!` no cabeçalho ou rodapé `BREAKING CHANGE:`) cria a próxima versão maior. As imagens binárias Linux, macOS e Windows produzidas pelo mesmo commit são anexadas à release do GitHub.

As versões iniciais usam `1.0.0` como base definida em `CMakeLists.txt`; portanto, o primeiro `feat` sem tags anteriores gera `v1.1.0`. Commits que não sejam `feat` ou breaking change passam pelo CI, mas não publicam release automaticamente.

## Portabilidade

O núcleo depende apenas da biblioteca padrão C. Mantenha o código em C11, evite APIs exclusivas de plataforma e atualize a arquitetura e a ISA quando alterar comportamento visível da máquina. Instruções de build local estão no [README](README.md).

## Issues e labels

Use os formulários em GitHub Issues e associe o tipo (`type: bug`, `type: enhancement`, `type: docs`, `type: question`), área (`area: cpu`, `area: memory`, `area: rom-loader`, `area: monitor`, `area: gui`, `area: packaging`, `area: website`, `area: ci`), prioridade (`priority: critical/high/normal/low`) e estado (`status: needs-triage`, `status: confirmed`, `status: in-progress`, `status: blocked`, `status: wont-fix`) quando aplicável. `good first issue` e `help wanted` destacam contribuições abertas. O workflow `Sync issue labels` cria ou atualiza as labels listadas em `.github/labels.json` sem apagar labels personalizadas.
