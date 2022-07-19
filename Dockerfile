# syntax=docker/dockerfile:1.4
FROM jupyterhub/jupyterhub as builder

RUN pip install --upgrade pip
RUN mkdir -p /opt/jupyterhub-nomad-spawner/jupyterhub_nomad_spawner

COPY poetry.lock pyproject.toml /opt/jupyterhub-nomad-spawner/
RUN touch /opt/jupyterhub-nomad-spawner/jupyterhub_nomad_spawner/__init__.py

RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python3 -

RUN /root/.poetry/bin/poetry config virtualenvs.create false

WORKDIR /opt/jupyterhub-nomad-spawner
RUN --mount=type=cache,target=/root/.cache/pypoetry --mount=type=cache,target=/root/.cache/pip /root/.poetry/bin/poetry install --no-dev -n -vv
COPY jupyterhub_nomad_spawner /opt/jupyterhub-nomad-spawner/jupyterhub_nomad_spawner
RUN /root/.poetry/bin/poetry build -f wheel



FROM jupyterhub/jupyterhub AS jupyterhub
RUN --mount=type=cache,target=/root/.cache/pip python3 -m pip install --upgrade pip
RUN --mount=type=cache,target=/root/.cache/pip python3 -m pip -v install oauthenticator

RUN --mount=type=bind,target=/opt/jupyterhub-nomad-spawner/dist/,source=/opt/jupyterhub-nomad-spawner/dist/,from=builder --mount=type=cache,target=/root/.cache/pip python3 -m pip -v install /opt/jupyterhub-nomad-spawner/dist/*.whl
