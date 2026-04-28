ARG BUILD_FROM=ghcr.io/home-assistant/base:latest
FROM ${BUILD_FROM}

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/opt/matter-network-doctor/bin:${PATH}"

RUN apk add --no-cache ca-certificates iproute2 procps python3 py3-pip

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
COPY run.sh /run.sh
RUN python3 -m venv /opt/matter-network-doctor \
  && pip install --no-cache-dir --upgrade pip \
  && pip install --no-cache-dir . \
  && chmod +x /run.sh

CMD ["/run.sh"]
