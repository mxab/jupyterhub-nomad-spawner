"""pytest config for dockerspawner tests"""
import logging
import subprocess
import time
from pathlib import Path

import httpx
import pytest
import pytest_asyncio
import requests
from jupyterhub.objects import Hub
from tenacity import retry, stop_after_attempt, wait_fixed
from traitlets.config import Config


@retry(stop=stop_after_attempt(5), wait=wait_fixed(2))
def wait_for_server(url: str):
    """Wait for a server to be up"""
    r = requests.get(url)
    r.raise_for_status()


@pytest.fixture(scope="session")
def nomad_process(tmp_path_factory):
    # https://til.simonwillison.net/pytest/subprocess-server
    nomad_proc = subprocess.Popen(
        ["nomad", "agent", "-dev", "-network-interface=en0"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    # Give the server time to start
    time.sleep(5)
    # Check it started successfully

    assert not nomad_proc.poll(), nomad_proc.stdout.read().decode("utf-8")
    wait_for_server("http://localhost:4646/v1/agent/self")
    yield nomad_proc

    # Shut it down at the end of the pytest session
    nomad_proc.terminate()


@pytest.fixture(scope="session")
def consul_process(tmp_path_factory):
    # https://til.simonwillison.net/pytest/subprocess-server
    consul_proc = subprocess.Popen(
        [
            "consul",
            "agent",
            "-dev",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    # Give the server time to start
    time.sleep(2)
    # Check it started successfully
    assert not consul_proc.poll(), consul_proc.stdout.read().decode("utf-8")
    wait_for_server("http://127.0.0.1:8500/v1/status/leader")
    yield consul_proc
    # Shut it down at the end of the pytest session
    consul_proc.terminate()


def nomad_client(nomad_process):
    pass


@pytest.fixture(autouse=True)
def traitlets_logging():
    """Ensure traitlets default logging is enabled

    so KubeSpawner logs are captured by pytest.
    By default, there is a "NullHandler" so no logs are produced.
    """
    logger = logging.getLogger("traitlets")
    logger.setLevel(logging.DEBUG)
    logger.handlers = []


@pytest.fixture
def config():
    """Return a traitlets Config object

    The base configuration for testing.
    Use when constructing Spawners for tests
    """
    cfg = Config()
    # cfg.NomadSpawner.cmd = ["jupyterhub-singleuser"]
    # cfg.NomadSpawner.start_timeout = 180
    # prevent spawners from exiting early due to missing env
    cfg.NomadSpawner.environment = {
        "JUPYTERHUB_API_TOKEN": "test-secret-token",
        "JUPYTERHUB_CLIENT_ID": "ignored",
    }
    return cfg


@pytest.fixture
def hub(hub_serivce) -> Hub:
    """Return the jupyterhub Hub object for passing to Spawner constructors

    Ensures the hub_pod is running
    """
    hub = Hub(
        ip=hub_serivce["Address"],
        port=hub_serivce["Port"],
        base_url="/hub/",
    )
    #  hub.base_url = '/hub'
    if not hub.is_up():
        raise Exception("Hub is not up")

    api_url = f'http://{hub_serivce["Address"]}:{hub_serivce["Port"]}/hub/api'

    token = "test-secret-token"
    r = requests.post(
        api_url + "/users/testuser",
        headers={
            "Authorization": f"token {token}",
        },
    )

    yield hub

    # clean up, delete test user
    r = requests.delete(
        api_url + "/users/testuser",
        headers={
            "Authorization": f"token {token}",
        },
    )
    r.raise_for_status()


@pytest_asyncio.fixture
@retry(stop=stop_after_attempt(4), wait=wait_fixed(5))
async def hub_serivce(hub_job, consul_process):
    async with httpx.AsyncClient(base_url="http://localhost:8500") as client:
        r = await client.get("/v1/health/service/jupyter-hub-api")
        body = r.json()
        if len(body) != 1:
            raise Exception("No jupyter-hub-api service found")
        return body[0]["Service"]


@pytest_asyncio.fixture
async def hub_job(nomad_process):
    job_hcl = open(f"{Path(__file__).parent}/hub.nomad", "r").read()
    async with httpx.AsyncClient(base_url="http://localhost:4646") as client:
        job_parse_request = {"JobHCL": job_hcl, "Canonicalize": True}
        parsed_job = await client.post(
            "/v1/jobs/parse",
            json=job_parse_request,
        )

        parsed_job_as_dict = parsed_job.json()

        register_job_as_dict = {
            "EnforceIndex": False,
            "PreserveCounts": True,
            "PolicyOverride": False,
            "JobModifyIndex": 0,
            "Job": parsed_job_as_dict,
        }
        job = await client.post(
            "/v1/jobs",
            json=register_job_as_dict,
        )
        job.raise_for_status()
