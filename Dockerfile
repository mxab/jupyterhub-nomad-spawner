FROM jupyterhub/jupyterhub as builder

RUN pip install --upgrade pip
RUN mkdir -p /opt/jupyterhub-nomad-spawner/jupyterhub_nomad_spawner

COPY poetry.lock pyproject.toml /opt/jupyterhub-nomad-spawner/
RUN touch /opt/jupyterhub-nomad-spawner/jupyterhub_nomad_spawner/__init__.py

RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python3 -

RUN /root/.poetry/bin/poetry config virtualenvs.create false

WORKDIR /opt/jupyterhub-nomad-spawner
RUN /root/.poetry/bin/poetry install --no-dev -n -vv
COPY jupyterhub_nomad_spawner /opt/jupyterhub-nomad-spawner/jupyterhub_nomad_spawner
RUN /root/.poetry/bin/poetry build -f wheel

#RUN cd /opt/jupyterhub-nomad-spawner && /root/.poetry/bin/poetry install --no-dev -n -vvv

#COPY jupyterhub_config.py .

FROM jupyterhub/jupyterhub AS jupyterhub

COPY --from=builder /opt/jupyterhub-nomad-spawner/jupyterhub_nomad_spawner-0.1.0-py3-none-any.whl /opt/jupyterhub-nomad-spawner/

RUN pip install /opt/jupyterhub-nomad-spawner/jupyterhub_nomad_spawner-0.1.0-py3-none-any.whl