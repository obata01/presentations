FROM python:3.11-slim

ENV APP_HOME /workspace
ENV PYTHONPATH ${APP_HOME}
WORKDIR ${APP_HOME}

COPY pyproject.toml ${APP_HOME}

RUN pip install --upgrade pip && \
    pip install uv

RUN uv pip install . --system
