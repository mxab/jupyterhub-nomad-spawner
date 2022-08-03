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


# @pytest.mark.asyncio
# async def test_schedule_job(httpx_mock: HTTPXMock):
#     httpx_mock.add_response(
#         url="http://localhost:4646/v1/jobs/parse",
#         status_code=200,
#         json={
#             "ID": "job123",
#             "Name": "job123",
#         },
#         match_headers={"Content-Type": "application/json"},
#     )

#     httpx_mock.add_response(
#         url="http://localhost:4646/v1/jobs",
#         status_code=200,
#         json={},
#         match_headers={"Content-Type": "application/json"},
#     )
#     async with httpx.AsyncClient() as client:

#         service = NomadService(client=client, log=logging.getLogger("test"))

#         await service.schedule_job(
#             job_hcl="""

#             job "job123" {
#                 # should we put full content here?
#             }
#             """
#         )
