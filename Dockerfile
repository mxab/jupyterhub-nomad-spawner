# syntax=docker/dockerfile:1.4
FROM jupyterhub/jupyterhub as builder

RUN apt update && apt install -y python3-venv
RUN pip install --upgrade pip pipx
RUN pipx install poetry
RUN poetry config virtualenvs.create false

RUN mkdir -p /opt/jupyterhub-nomad-spawner/jupyterhub_nomad_spawner

COPY poetry.lock pyproject.toml /opt/jupyterhub-nomad-spawner/
RUN touch /opt/jupyterhub-nomad-spawner/jupyterhub_nomad_spawner/__init__.py



WORKDIR /opt/jupyterhub-nomad-spawner
RUN --mount=type=cache,target=/root/.cache/pypoetry --mount=type=cache,target=/root/.cache/pip poetry install --no-dev -n -vv
COPY jupyterhub_nomad_spawner /opt/jupyterhub-nomad-spawner/jupyterhub_nomad_spawner
RUN poetry build -f wheel



FROM jupyterhub/jupyterhub AS jupyterhub
RUN --mount=type=cache,target=/root/.cache/pip python3 -m pip install --upgrade pip
RUN --mount=type=cache,target=/root/.cache/pip python3 -m pip -v install oauthenticator

RUN --mount=type=bind,target=/opt/jupyterhub-nomad-spawner/dist/,source=/opt/jupyterhub-nomad-spawner/dist/,from=builder --mount=type=cache,target=/root/.cache/pip python3 -m pip -v install /opt/jupyterhub-nomad-spawner/dist/*.whl
