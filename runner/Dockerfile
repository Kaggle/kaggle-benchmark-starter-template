FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    git \
    gnupg \
    iptables \
    python3 \
    python3-pip \
    python3-venv \
    docker.io \
    docker-compose-v2 \
  && rm -rf /var/lib/apt/lists/*

RUN curl -LsSf https://astral.sh/uv/install.sh | sh \
  && ln -s /root/.local/bin/uv /usr/local/bin/uv \
  && uv tool install harbor==0.15.0 --with litellm==1.89.4 --with cryptography==46.0.3 \
  && ln -s /root/.local/share/uv/tools/harbor/bin/harbor /usr/local/bin/harbor

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
