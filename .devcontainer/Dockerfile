FROM verilator/verilator:v5.052@sha256:a5b73e2fce0b2c483396f3800940f33b6faa802331a061c21694dd27b7352120 AS verilator

FROM mcr.microsoft.com/devcontainers/base:trixie@sha256:b8c3669fb4cc652621b3386517c40ab3e151e827de958d6fe75528798ffb5727

ARG UV_VERSION=0.10.0
ARG VERIBLE_VERSION=v0.0-4163-g6cce8f19

ENV UV_LINK_MODE=copy

USER root

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        curl \
        git \
        make \
        python3 \
        python3-dev \
        python3-venv \
    && rm -rf /var/lib/apt/lists/*

# cocotb 2.0.1 requires Verilator 5.036 or newer. Debian's packaged version
# can lag that requirement, so copy a known-compatible official release.
COPY --from=verilator /usr/local/bin/verilator* /usr/local/bin/
COPY --from=verilator /usr/local/share/verilator /usr/local/share/verilator

# Pinned, checksum-verified HDL frontends. Both Verilator and Verible provide
# native amd64 and arm64 builds, so Docker selects the host architecture.
ARG TARGETARCH
RUN set -eux; \
    case "${TARGETARCH}" in \
        amd64) VERIBLE_ARCH=x86_64; VERIBLE_SHA=ddb9c7ea1fe60146ce2fc9f2f2d7a6c0257d08bf51a98dc0ccb4b47b44161bd8 ;; \
        arm64) VERIBLE_ARCH=arm64; VERIBLE_SHA=6f894b4f375a1ca487c7a56fda961711aa0d7637f88e0ae6a6b22e1d0e76d227 ;; \
        *) echo "Unsupported container architecture: ${TARGETARCH}" >&2; exit 1 ;; \
    esac; \
    VERIBLE_FILE="verible-${VERIBLE_VERSION}-linux-static-${VERIBLE_ARCH}.tar.gz"; \
    curl --fail --location --silent --show-error --output "/tmp/${VERIBLE_FILE}" "https://github.com/chipsalliance/verible/releases/download/${VERIBLE_VERSION}/${VERIBLE_FILE}"; \
    echo "${VERIBLE_SHA}  /tmp/${VERIBLE_FILE}" | sha256sum --check; \
    tar --extract --gzip --file "/tmp/${VERIBLE_FILE}" --strip-components=2 --directory /usr/local/bin "verible-${VERIBLE_VERSION}/bin"; \
    rm -f "/tmp/${VERIBLE_FILE}"

RUN python3 -m venv /opt/demo-bootstrap \
    && /opt/demo-bootstrap/bin/python -m pip install --no-cache-dir "uv==${UV_VERSION}" \
    && ln -s /opt/demo-bootstrap/bin/uv /usr/local/bin/uv \
    && ln -s /opt/demo-bootstrap/bin/uvx /usr/local/bin/uvx

# Seed TerosHDL's global configuration for this repository's dev container.
COPY --chown=vscode:vscode .devcontainer/teroshdl-config.json /home/vscode/.teroshdl2_config.json
USER vscode
