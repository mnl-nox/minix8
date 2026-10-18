FROM debian:bookworm-slim AS build
RUN apt-get update && apt-get install -y --no-install-recommends gcc make libc6-dev python3 python3 ca-certificates git && rm -rf /var/lib/apt/lists/*
WORKDIR /src
COPY . .
RUN make
RUN make test

FROM debian:bookworm-slim
COPY --from=build /src/minix8 /usr/local/bin/minix8
USER 65532:65532
ENTRYPOINT ["/usr/local/bin/minix8"]
CMD ["--help"]
