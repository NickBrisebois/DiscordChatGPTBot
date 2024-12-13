FROM python:3.11-slim-bookworm as base

RUN apt-get update
RUN pip install poetry

WORKDIR /chatai/

COPY README.md $WORKDIR
COPY pyproject.toml $WORKDIR
COPY poetry.lock /$WORKDIR

RUN poetry config virtualenvs.create false
RUN poetry install --no-interaction

COPY . $WORKDIR

ENTRYPOINT [ "$WORKDIR/run.sh" ]