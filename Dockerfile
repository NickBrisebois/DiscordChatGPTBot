FROM python:3.12-slim-bookworm as base

RUN apt-get update
RUN pip install --progress-bar off uv

WORKDIR /chatai/

COPY README.md /chatai/
COPY pyproject.toml /chatai/
COPY uv.lock /chatai/

RUN uv sync

COPY . /chatai/

ENTRYPOINT [ "/chatai/run.sh" ]
