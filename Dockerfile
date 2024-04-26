FROM python:3.11-slim-bookworm as base

RUN apt-get update
RUN pip install poetry

WORKDIR /lez/

COPY README.md /lez/
COPY pyproject.toml /lez/
COPY poetry.lock /lez/

RUN poetry config virtualenvs.create false
RUN poetry install --no-interaction

COPY . /lez/

ENTRYPOINT [ "/lez/run.sh" ]