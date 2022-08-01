import asyncio
import json
import os
import time
from unittest.mock import Mock

import pytest
from jupyterhub.objects import Hub, Server
from jupyterhub.orm import Spawner
import requests
from tenacity import retry, stop_after_attempt, wait_fixed

from jupyterhub_nomad_spawner import __version__
from jupyterhub_nomad_spawner.spawner import NomadSpawner
import pytest
from jupyterhub.tests.mocking import public_url
from jupyterhub.tests.test_api import add_user, api_request
from jupyterhub.utils import url_path_join
from tornado.httpclient import AsyncHTTPClient
import pytest_asyncio


# @pytest.mark.parametrize("remove", (True, False))

# nomad_client:Nomad
# @pytest.mark.asyncio
# async def test_start_stop(nomadspawner_configured_app):
#     app = nomadspawner_configured_app
#     name = "has@"
#     add_user(app.db, app, name=name)
#     user = app.users[name]
#     server_name = 'also-has@'
#     spawner = user.spawners[server_name]
#     assert isinstance(spawner, NomadSpawner)
#   #  spawner.remove = remove
#     token = user.new_api_token()
#     # start the server
#     r = await api_request(app, "users", name, "servers", server_name, method="post")
#     pending = r.status_code == 202
#     while pending:
#         # request again
#         r = await api_request(app, "users", name)
#         user_info = r.json()
#         pending = user_info["servers"][server_name]["pending"]
#     assert r.status_code in {201, 200}, r.text

#     url = url_path_join(public_url(app, user), server_name, "api/status")
#     resp = await AsyncHTTPClient().fetch(
#         url, headers={"Authorization": "token %s" % token}
#     )
#     assert resp.effective_url == url
#     resp.rethrow()
#     assert "kernels" in resp.body.decode("utf-8")

#     # stop the server
#     r = await api_request(app, "users", name, "servers", server_name, method="delete")
#     pending = r.status_code == 202
#     while pending:
#         # request again
#         r = await api_request(app, "users", name)
#         user_info = r.json()
#         pending = user_info["servers"][server_name]["pending"]
#     assert r.status_code in {204, 200}, r.text
#     state = spawner.get_state()


#     assert state is not None
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
