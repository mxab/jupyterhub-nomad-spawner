import logging

import httpx
import pytest

from jupyterhub_nomad_spawner.nomad.nomad_service import NomadService


@pytest.mark.respx(base_url="http://localhost:4646")
@pytest.mark.asyncio
async def test_register_volume(respx_mock):
    respx_mock.put(
        "/v1/volume/csi/volume123",
        json={
            "Volumes": [
                {
                    "AccessMode": "single-node-writer",
                    "AttachmentMode": "file-system",
                    "ID": "volume123",
                    "ExternalID": "volume123",
                    "Name": "volume123",
                    "PluginID": "csi_plugin_1",
                }
            ]
        },
    ).mock(return_value=httpx.Response(200))

    async with httpx.AsyncClient(base_url="http://localhost:4646") as client:
        service = NomadService(client=client, log=logging.getLogger("test"))
        await service.create_volume(id="volume123", plugin_id="csi_plugin_1")


@pytest.mark.respx(base_url="http://localhost:4646")
@pytest.mark.asyncio
async def test_register_volume(respx_mock):
    respx_mock.put(
        "/v1/volume/csi/volume123",
        json={
            "Volumes": [
                {
                    "AccessMode": "single-node-writer",
                    "AttachmentMode": "file-system",
                    "ID": "volume123",
                    "ExternalID": "volume123",
                    "Name": "volume123",
                    "PluginID": "csi_plugin_1",
                }
            ]
        },
    ).mock(return_value=httpx.Response(200))

    async with httpx.AsyncClient(base_url="http://localhost:4646") as client:
        service = NomadService(client=client, log=logging.getLogger("test"))
        await service.create_volume(id="volume123", plugin_id="csi_plugin_1")


@pytest.mark.respx(base_url="http://localhost:4646")
@pytest.mark.asyncio
async def test_lookup_service(respx_mock):
    respx_mock.get("/v1/service/my-notebook-service-123").mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "Address": "127.0.0.1",
                    "AllocID": "177160af-26f6-619f-9c9f-5e46d1104395",
                    "CreateIndex": 14,
                    "Datacenter": "dc1",
                    "ID": "_nomad-task-177160af-26f6-619f-9c9f-5e46d1104395-redis-example-cache-redis-db",
                    "JobID": "example",
                    "ModifyIndex": 24,
                    "Namespace": "default",
                    "NodeID": "7406e90b-de16-d118-80fe-60d0f2730cb3",
                    "Port": 29702,
                    "ServiceName": "my-notebook-service-123",
                    "Tags": ["db", "cache"],
                }
            ],
        )
    )
    async with httpx.AsyncClient(base_url="http://localhost:4646") as client:
        service = NomadService(client=client, log=logging.getLogger("test"))
        (address, port) = await service.get_service_address(service_name="my-notebook-service-123")
        assert address == "127.0.0.1"
        assert port == 29702

