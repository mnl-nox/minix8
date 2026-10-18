# Docker e Podman

Este guia descreve como construir e executar MiniX8 em um container, o que o build valida e como diagnosticar falhas do daemon ou de namespaces.

## O que a imagem faz

O Dockerfile tem dois estágios:

1. **Build e QA**, em `debian:bookworm-slim`: instala GCC, Make, `libc6-dev`, Python 3 e certificados; compila o núcleo e executa `make test`.
2. **Runtime**, também em Debian slim: copia somente o executável `minix8` e inicia como UID/GID `65532:65532`, sem privilégios de root.

`libc6-dev` fornece os headers C da libc, como `ctype.h` e `stdint.h`, que não vêm na imagem slim apenas com GCC. O runtime não inclui compilador, fontes, Python ou assembler. Monte ROMs como arquivos legíveis; o container não escreve no volume de ROM quando montado como somente leitura.

## Construir e executar

Com Docker:

```sh
docker build -t minix8:local .
docker run --rm minix8:local --help
docker run --rm -it -v "$PWD:/rom:ro" minix8:local --rom /rom/program.bin
```

Com Podman, os mesmos comandos funcionam:

```sh
podman build -t minix8:local .
podman run --rm minix8:local --help
podman run --rm -it -v "$PWD:/rom:ro" minix8:local --rom /rom/program.bin
```

O comando de build executa `make test`; não é necessário repetir a suíte dentro da imagem final. Para rodar a suíte diretamente no host, use `make test`.

No PowerShell, substitua `$PWD` pela sintaxe de caminho do Docker Desktop, por exemplo `${PWD}:/rom:ro`.

## Erros de compilação

### `ctype.h` ou `stdint.h` ausente em `RUN make`

Confirme que o estágio de build instala `libc6-dev`:

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc make libc6-dev python3 ca-certificates \
    && rm -rf /var/lib/apt/lists/*
```

Em Debian slim, instalar `gcc` sozinho não garante os headers de desenvolvimento da libc.

## Permissão negada ao daemon Docker

Erro como:

```text
permission denied while trying to connect to the Docker API at unix:///var/run/docker.sock
```

indica que o usuário atual não consegue acessar o daemon/socket Docker. O Dockerfile não controla essa permissão do host. Em Linux, confirme que o daemon está ativo (`sudo systemctl status docker`) e use uma conta autorizada. Em sistemas onde o daemon é gerenciado pelo usuário, confirme o contexto/socket correspondente com `docker context ls`.

Adicionar uma conta ao grupo `docker` costuma dar privilégios equivalentes a root; faça isso apenas em máquinas confiáveis e conforme a política do administrador. Em ambientes gerenciados, peça ao administrador acesso ao daemon ou um runner que aceite containers. Não altere permissões do socket para `666`.

## Podman e `newuidmap: Operation not permitted`

Podman rootless precisa de namespaces de usuário e faixas subordinadas de UID/GID. Em Debian/Ubuntu, verifique os pacotes `podman` e `uidmap`, e confira se seu usuário possui entradas em `/etc/subuid` e `/etc/subgid`. Um administrador pode configurar essas faixas segundo a política local; depois, encerre e reabra a sessão e verifique `podman info`.

Em CI restrito, container aninhado ou sandbox que proíbe user namespaces, a configuração do projeto não pode remover essa restrição. O administrador precisa habilitar namespaces apropriados ou fornecer um runner/daemon. A opção rootless é preferível para uso local quando suportada pelo host.

## Interpretação da validação

- Se `docker build` parar durante `apt-get`, verifique acesso à rede e aos repositórios Debian.
- Se parar em `RUN make`, examine a dependência/diagnóstico C; os headers estão cobertos por `libc6-dev`.
- Se parar em `RUN make test`, é uma falha da suíte durante o estágio de build.
- Se o build terminar e `docker run ... --help` não iniciar, verifique a arquitetura da imagem/runtime.
- Erros de socket Docker ou criação de namespace Podman ocorrem antes do build da imagem e são problemas de acesso/configuração do host.

O usuário não privilegiado do runtime melhora o isolamento, mas não substitui as permissões e políticas do host.
