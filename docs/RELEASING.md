# CI/CD e releases

O workflow [ci-release.yml](../.github/workflows/ci-release.yml) automatiza validação, compilação e publicação. Ele não precisa de secrets pessoais: usa o `GITHUB_TOKEN` fornecido pelo GitHub Actions.

## Em cada pull request e push

1. `scripts/check_commits.py` verifica que os assuntos dos commits usam Conventional Commits e não passam de 100 caracteres.
2. O QA executa testes unitários, integração de CLI, análise estática GCC e sanitizers AddressSanitizer/UBSan com `make qa`.
3. CMake compila e roda CTest em três alvos: Ubuntu 22.04 x86-64, macOS 14 ARM64 e Windows Server 2022 x86-64.
4. O build nativo com Make é compilado em containers Debian stable e Fedora para conferir compatibilidade com distribuições Debian e RPM.
5. O workflow `docker-image.yml` constrói a imagem Docker em cada PR e push à `main`. O Dockerfile executa `make test`; em seguida, o workflow testa a CLI e confirma o UID sem privilégios do runtime.
6. O job de release só roda depois que todos os jobs anteriores terminam com sucesso; uma tag/release não deve ser criada manualmente antes de CI verde.
7. O job `distribution` coleta os três executáveis e cria a ISO 9660 multiplataforma; ela é anexada à release junto com os binários.

## Site e labels

`.github/workflows/pages.yml` publica `site/` e os manuais em GitHub Pages quando arquivos do site ou documentação mudam na `main`. Em **Settings → Pages**, selecione “GitHub Actions” como fonte. O endereço esperado é `https://<proprietário>.github.io/minix8/`.

`.github/labels.json` é a fonte de verdade das labels de issues. O workflow `sync-labels.yml` cria ou atualiza essas labels em push à `main` quando o catálogo muda, ou manualmente por `workflow_dispatch`. Requer `issues: write`. Ele não exclui labels existentes fora do catálogo.

Os artefatos de cada build ficam disponíveis no run do Actions durante 30 dias. A matriz e os artefatos publicados podem ser alterados em `ci-release.yml`.

## Regra de versionamento

O job de release verifica todos os commits que chegaram à `main` no push:

- `feat: ...` ou `feat(escopo): ...` incrementa MINOR;
- `fix: ...` ou `fix(escopo): ...` incrementa PATCH;
- qualquer assunto Conventional Commit terminado em `!:` ou um rodapé `BREAKING CHANGE:` incrementa MAJOR;
- os demais tipos apenas compilam e não criam release.

Ao incrementar MAJOR ou MINOR, os componentes inferiores voltam a zero. A tag mais alta `vMAJOR.MINOR.PATCH` serve de base. Na primeira publicação, o workflow usa diretamente a versão de `CMakeLists.txt` (atualmente `1.0.0`); nas seguintes, aplica o incremento SemVer. O job cria uma tag anotada `vX.Y.Z` no commit integrado e uma release GitHub com notas geradas automaticamente, três binários e a imagem ISO:

- `minix8-linux-x86_64` — Ubuntu 22.04;
- `minix8-macos-arm64` — macOS 14 em Apple Silicon;
- `minix8-windows-x86_64.exe` — Windows Server 2022.
- `MiniX8-1987.iso` — mídia ISO 9660 não inicializável, com os três binários, fontes, exemplos e documentação.

O executável Linux foi compilado em Ubuntu 22.04 para compatibilidade de glibc mais ampla. Sistemas com libc incompatível podem compilar localmente (`make`) ou usar o container. Os containers Debian/Fedora do CI são validação de build, não artefatos de release.

## Como integrar uma feature

1. Faça commits com assunto Conventional Commit.
2. Abra PR contra `main` e aguarde todos os checks verdes (validação de mensagens, QA com testes/análise/sanitizers, três builds/testes nativos e dois builds Linux em containers).
3. Use **Squash and merge** e mantenha o título do squash no formato Conventional Commit, como `feat(cpu): add rotate instruction`.
4. O push resultante à `main` executa a publicação para títulos `fix`, `feat` ou breaking change. A tag e a release aparecem na aba Releases do repositório.

Squash merge mantém o assunto que aciona a release claro e evita títulos automáticos de merge que não seguem o formato aceito. Se a publicação falhar por tag duplicada, revise as tags existentes e corrija manualmente a sequência SemVer antes de reexecutar o workflow.

## Permissões necessárias

O workflow de CI define `contents: read` globalmente. Apenas o job `release` recebe `contents: write`, para enviar tags e criar a release. Os workflows de Pages e labels declaram `pages: write`, `id-token: write` e `issues: write`, respectivamente. Nas configurações do repositório, permita ao `GITHUB_TOKEN` escrever conteúdo e publique Pages por GitHub Actions; políticas organizacionais podem restringir permissões.
