FROM python:3.8-slim
ENV PYTHONUNBUFFERED 1

ARG RUNNER_VERSION

RUN apt-get update && apt-get install -y \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    git
RUN apt-get autoremove -y && apt-get clean -y && rm -rf /var/lib/apt/lists/*

RUN pip install -U pip && pip install poetry && mkdir -p /root/.config/pypoetry \
    && echo "[virtualenvs]" > /root/.config/pypoetry/config.toml \
    && echo "create = false" >> /root/.config/pypoetry/config.toml

COPY executor /app/executor
COPY ./pyproject.toml /app/.

ADD . /app
WORKDIR /app

RUN poetry build

RUN pip install dist/*.whl

RUN rm -rf dist

WORKDIR /app

COPY ./entrypoint.sh /entrypoint.sh
RUN chmod 755 /entrypoint.sh

ENTRYPOINT [ "/entrypoint.sh" ]