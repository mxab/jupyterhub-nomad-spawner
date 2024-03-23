"""pytest config for dockerspawner tests"""
from textwrap import indent
from unittest.mock import Mock, patch
from .utils import fixture_content

import pytest

from jupyterhub.tests.mocking import MockHub

from traitlets.config import Config


from jupyterhub_nomad_spawner.spawner import NomadSpawner


class MockUser(Mock):
    name = "myname"
    server = MockHub()

    def __init__(self, **kwargs):
        super().__init__()
        for key, value in kwargs.items():
            setattr(self, key, value)

    @property
    def escaped_name(self):
        return self.name

    @property
    def url(self):
        return "/server/name/lab"


@pytest.fixture
def user():
    return MockUser()


def test_spawner_auto_remove_default(user):
    cfg = Config()
    cfg.NomadSpawner.auto_remove_jobs = False

    spawner = NomadSpawner(user=user, config=cfg)

    assert spawner.auto_remove_jobs == False


@pytest.mark.parametrize("config", [True, False])
def test_spawner_auto_remove_set(user, config):
    cfg = Config()
    cfg.NomadSpawner.auto_remove_jobs = config

    spawner = NomadSpawner(user=user, config=cfg)

    assert spawner.auto_remove_jobs == config


# @patch("jupyterhub_nomad_spawner.spawner.NomadSpawner.get_env",**{'method.return_value': {}})
@pytest.mark.asyncio
async def test_job_factory_default(user):
    cfg = Config()
    cfg.NomadSpawner.base_job_name = "jupyter-notebook"
    cfg.NomadSpawner.service_provider = "consul"

    # slim down env vars to avoid test pollution by the host config
    cfg.NomadSpawner.env_keep = [
        "LANG",
        "LC_ALL",
        "JUPYTERHUB_SINGLEUSER_APP",
    ]

    hub = user.server
    hub.public_host = "127.0.0.1"
    hub.base_url = "/"
    hub.api_url = "api.test"

    spawner = NomadSpawner(user=user, hub=hub, config=cfg)

    user_options = {
        "datacenters": ["dc1", "dc2"],
        "args": ["--arg1", "--arg2"],
        "image": "jupyter/minimal-notebook",
        "memory": 512,
    }
    spawner.user_options = user_options
    spawner.notebook_id = "123"

    nomad_service = Mock()
    job = await spawner._default_job_factory(nomad_service=nomad_service)

    assert job == fixture_content("test_create_job.v2")
