import logging
from unittest.mock import Mock

import pytest
import requests
from jupyterhub.objects import Server
from tenacity import retry, stop_after_attempt, wait_fixed

from jupyterhub_nomad_spawner.spawner import NomadSpawner

log = logging.getLogger("test")


class MockUser(Mock):
    name = "testuser"
    server = Server()

    def __init__(self, **kwargs):
        super().__init__()
        for key, value in kwargs.items():
            setattr(self, key, value)

    @property
    def escaped_name(self):
        return self.name

    @property
    def url(self):
        return self.server.url


@pytest.mark.integration
@pytest.mark.asyncio
async def test_spawn_start(config, hub, hub_serivce):
    spawner = NomadSpawner(
        hub=hub,
        user=MockUser(),
        config=config,
        api_token="abc123",
        oauth_client_id="unused",
    )
    options = {}
    options["image"] = "jupyter/minimal-notebook:2022-07-27"
    options["datacenters"] = ["dc1"]
    options["memory"] = 512
    options["volume_type"] = None

    spawner.user_options = options
    # empty spawner isn't running

    status = await spawner.poll()
    assert isinstance(status, int)

    # start the spawner
    url = await spawner.start()
    log.info("started spawner at %s", url)
    # verify the pod exists

    # verify poll while running
    status = await spawner.poll()
    assert status is None

    # check for activity

    api_url = f'http://{hub_serivce["Address"]}:{hub_serivce["Port"]}/hub/api'

    assert_activity(api_url)
    # make sure spawn url is correct

    # stop the pod
    await spawner.stop()

    # verify exit status
    status = await spawner.poll()
    assert isinstance(status, int)


@retry(stop=stop_after_attempt(6), wait=wait_fixed(10))
def assert_activity(api_url):
    token = "test-secret-token"
    r = requests.get(
        api_url + "/users/testuser",
        headers={
            "Authorization": f"token {token}",
        },
    )
    data = r.json()
    assert data["last_activity"] is not None
