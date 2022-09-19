# Packaging Stage
# ===============

FROM python:3.10.7-slim-bullseye as packager
ENV PYTHONUNBUFFERED=1
RUN pip install -U pip && pip install poetry
COPY pyproject.toml poetry.lock /source/
COPY src /source/src/
WORKDIR /source/
RUN rm -rf dist && poetry build


# Building Stage
# ==============

FROM python:3.10.7-slim-bullseye as builder
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY --from=packager /source/dist/*.whl /
RUN python -m venv /venv/

# _activate_ the virtual environment
ENV VIRTUAL_ENV=/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN pip install -U pip && pip install *.whl

# Final Runtime
# =============

FROM python:3.10.7-slim-bullseye as runtime
ENV PYTHONUNBUFFERED=1

ARG COMMIT_HASH
ARG COMMIT_TIME
ENV COMMIT_HASH=${COMMIT_HASH}
ENV COMMIT_TIME=${COMMIT_TIME}




# Runtime deps
RUN apt-get update && apt-get install -y \
    wget \
    libpq5 \
    openssh-server \
    && rm -rf /var/lib/apt/lists/*



COPY --from=builder /venv /venv
COPY src/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
# _activate_ the virtual environment
ENV VIRTUAL_ENV=/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Create a user who can connect over SSH
# This is a horrible hack for local testing, a better approach is needed longer term
RUN useradd --create-home --shell /venv/bin/nubbs --password "$(openssl passwd -1 nubbs)" nubbs
EXPOSE 22

ENTRYPOINT [ "/entrypoint.sh" ]
