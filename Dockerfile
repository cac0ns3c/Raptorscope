# SPDX-License-Identifier: GPL-3.0-or-later
# Raptorscope API image. Default command serves the bundled sample case offline
# (no ES needed); the compose "app" profile overrides it to serve from ES.
FROM python:3.12-slim

WORKDIR /app

# Unified Log parser (raw-evidence ingestion) — the mandiant/macos-UnifiedLogs
# Rust binary parses tracev3 offline. Fetched per-arch and checksum-verified.
ARG UNIFIEDLOG_VERSION=v0.6.0
RUN set -eux; \
    apt-get update; apt-get install -y --no-install-recommends curl ca-certificates; \
    arch="$(dpkg --print-architecture)"; \
    case "$arch" in \
      amd64) ra=x86_64 ;; \
      arm64) ra=aarch64 ;; \
      *) echo "unsupported arch: $arch" >&2; exit 1 ;; \
    esac; \
    base="https://github.com/mandiant/macos-UnifiedLogs/releases/download/${UNIFIEDLOG_VERSION}"; \
    f="unifiedlog_iterator-${UNIFIEDLOG_VERSION}-${ra}-unknown-linux-gnu.tar.gz"; \
    curl -fsSL "$base/$f" -o /tmp/ul.tgz; \
    curl -fsSL "$base/$f.sha256" -o /tmp/ul.sha256; \
    echo "$(cut -d' ' -f1 /tmp/ul.sha256)  /tmp/ul.tgz" | sha256sum -c -; \
    tar -xzf /tmp/ul.tgz -C /tmp; \
    find /tmp -name unifiedlog_iterator -type f -exec mv {} /usr/local/bin/unifiedlog_iterator \; ; \
    chmod +x /usr/local/bin/unifiedlog_iterator; \
    /usr/local/bin/unifiedlog_iterator --version; \
    apt-get purge -y curl; apt-get autoremove -y; rm -rf /var/lib/apt/lists/* /tmp/ul.*

COPY requirements.txt pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir -r requirements.txt && pip install --no-cache-dir -e .

COPY detections ./detections
COPY samples ./samples
COPY profile ./profile
COPY docs ./docs
COPY README.md ./

EXPOSE 8000
CMD ["raptorscope", "serve", "--collection", "samples/mac-victim", \
     "--host", "0.0.0.0", "--port", "8000"]
