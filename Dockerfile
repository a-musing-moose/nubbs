# Packaging Stage
# ===============

FROM python:3.10.0-slim-bullseye as packager
ENV PYTHONUNBUFFERED=1
RUN pip install -U pip && pip install poetry
COPY pyproject.toml poetry.lock /source/
COPY src /source/src/
WORKDIR /source/
RUN rm -rf dist && poetry build


# Building Stage
# ==============

FROM python:3.10.0-slim-bullseye as builder
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

FROM python:3.10.0-slim-bullseye as runtime
ENV PYTHONUNBUFFERED=1

ARG GIT_COMMIT_HASH
ARG GIT_COMMIT_DATE
ENV COMMIT_HASH=${GIT_COMMIT_HASH}
ENV COMMIT_DATE=${GIT_COMMIT_DATE}

# Runtime deps
RUN apt-get update && apt-get install -y \
    wget \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /venv /venv
COPY src/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
# _activate_ the virtual environment
ENV VIRTUAL_ENV=/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

EXPOSE 8000
# ENTRYPOINT [ "/entrypoint.sh" ]
