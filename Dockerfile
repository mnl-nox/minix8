FROM debian:bookworm-slim AS build
RUN apt-get update && apt-get install -y --no-install-recommends gcc make ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /src
COPY . .
RUN make

FROM debian:bookworm-slim
COPY --from=build /src/minix8 /usr/local/bin/minix8
ENTRYPOINT ["/usr/local/bin/minix8"]
CMD ["--help"]
