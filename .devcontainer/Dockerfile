# syntax=docker/dockerfile:1
FROM mcr.microsoft.com/devcontainers/base:1-ubuntu-24.04

# The single most important line in this file is the openssh purge below.
#
# openssh-client is deliberately REMOVED. Without an ssh binary on PATH, git has
# no SSH transport at all: it cannot fall back to ~/.ssh/id_ed25519 even if the
# key were somehow present, and even if GIT_SSH_COMMAND were unset. This repo
# gets containment from having exactly one credential, the repo-scoped PAT
# mounted in by devcontainer.json, and no other transport by which to use any
# credential.
#
# This has to be an explicit purge, not an omission: the devcontainers/base
# image ships openssh-client, so leaving it out of the apt list below leaves
# /usr/bin/ssh in place. Do not "fix" a git problem by reinstalling it.

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    git \
    ripgrep \
    ddgr \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get purge -y 'openssh-*' rsync && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/* \
    && rm -f /usr/bin/ssh /usr/bin/scp /usr/bin/sftp /usr/bin/ssh-agent /usr/bin/ssh-add /usr/bin/rsync

# Zola, pinned to the same release and sha256 as .github/workflows/site.yml
# (tests/check_site.py keeps the CI pin equal to the local zola, so a bump has
# to change both places). Zola 0.23 is a breaking release; don't float it.
ARG ZOLA_VERSION=0.23.6
ARG ZOLA_SHA256=8f5132b3522412d04e395e0b25f6d68613ad272a873e54a2b3ebf664873024a4
RUN tarball="zola-v${ZOLA_VERSION}-x86_64-unknown-linux-gnu.tar.gz" \
    && curl -fsSLO "https://github.com/getzola/zola/releases/download/v${ZOLA_VERSION}/${tarball}" \
    && echo "${ZOLA_SHA256}  ${tarball}" | sha256sum -c - \
    && tar -xzf "$tarball" -C /usr/local/bin zola \
    && rm "$tarball" \
    && zola --version

# uv, for scripts/check and the PEP 723 scripts (tests, hero.py, spend.py).
# No system Python on purpose: uv fetches 3.12, as in CI.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=automatic

# Node.js LTS: the KaTeX render check (tests/katex_check.js) and pi.
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/* \
    && npm install -g @earendil-works/pi-coding-agent

# pi's config dir: auth.json is mounted in; pi writes sessions beside it.
RUN mkdir -p /home/vscode/.pi/agent && chown -R vscode:vscode /home/vscode/.pi

RUN mkdir -p /workspace && chown vscode:vscode /workspace

USER vscode
WORKDIR /workspace

# No msmtp and no ~/.msmtprc. The one outbound message per unsupervised run
# goes through notify-jef (mounted from ~/tools/bin-container), which only
# drops a file in ~/outbox; agentd on the host holds the mail config and the
# recipient. Do not add msmtp back here.

CMD ["sleep", "infinity"]
