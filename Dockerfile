FROM python:3.11-slim-bookworm as base

RUN apt-get update
RUN pip install poetry

WORKDIR /chatai/

COPY README.md /chatai/
COPY pyproject.toml /chatai/
COPY poetry.lock /chatai/

RUN poetry config virtualenvs.create false
RUN poetry install --no-interaction

COPY . /chatai/

ENTRYPOINT [ "/chatai/run.sh" ]