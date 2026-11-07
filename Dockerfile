FROM ghcr.io/astral-sh/uv:0.13.6 AS uv
FROM python:3.11-slim-bookworm
COPY --from=uv /uv /usr/local/bin/uv
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl git openssh-client ffmpeg procps libatomic1 \
    libglib2.0-0 libgl1 libasound2 libopus0 libssl3 libnss3 libnspr4 \
    libatk1.0-0 libatk-bridge2.0-0 libatspi2.0-0 libcups2 libdrm2 \
    libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 \
    libgbm1 libcairo2 libpango-1.0-0 fonts-liberation \
    && rm -rf /var/lib/apt/lists/*
RUN useradd --create-home --uid 1000 agent && mkdir /app && chown agent:agent /app
USER agent
ENV HOME=/home/agent HPA_HOME=/home/agent/.hpa HERMES_HOME=/home/agent/.hermes
ENV PATH=/home/agent/.local/bin:/app/.venv/bin:$PATH
RUN mkdir -p /home/agent/.hpa /home/agent/.hermes
ARG HERMES_REF=bf0203a794a07aac3ff764972ab9087baa4e4f4e
RUN curl -fsSL "https://raw.githubusercontent.com/NousResearch/hermes-agent/${HERMES_REF}/scripts/install.sh" -o /tmp/install-hermes.sh \
    && bash /tmp/install-hermes.sh --commit "${HERMES_REF}" --non-interactive --skip-computer-use
WORKDIR /app
COPY --chown=agent:agent pyproject.toml uv.lock README.md ./
COPY --chown=agent:agent src ./src
COPY --chown=agent:agent --chmod=755 scripts/coolify-entrypoint.sh ./scripts/coolify-entrypoint.sh
RUN uv sync --frozen --no-dev --extra calls --extra semantic
ENTRYPOINT ["/app/.venv/bin/hpa"]
CMD ["serve"]
