import imp
from typing import AsyncGenerator


import pytest
from jupyterhub_nomad_spawner.nomad.nomad_model import CSIVolume, CSIVolumeCreateRequest
from jupyterhub_nomad_spawner.nomad.nomad_service import (
    
    NomadService,
    NomadServiceConfig,
)
from pytest_httpx import HTTPXMock
import httpx
import json

async def http_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    
    client = httpx.AsyncClient()
    yield client
    await client.aclose()


@pytest.mark.asyncio
async def test_register_volume(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="http://localhost:4646/v1/volumes/csi/volume123/create",
        status_code=200,
        json=1,
        match_headers={"Content-Type": "application/json"},
        match_content=json.dumps(
            {
                "Volumes": [
                    {
                        "AccessMode": "single-node-writer",
                        "AttachmentMode": "file-system",
                        "ID": "volume123",
                    }
                ]
            }
        ).encode("ascii"),
    )

    async with httpx.AsyncClient() as client:

        service = NomadService(client=client, config=NomadServiceConfig())
        await service.create_volume(id="volume123")


@pytest.mark.asyncio
async def test_schedule_job(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="http://localhost:4646/v1/jobs/parse",
        status_code=200,
        json={
            "ID" : "job123",
            "Name":"job123",
        },

        match_headers={"Content-Type": "application/json"},
    )

    httpx_mock.add_response(
        url="http://localhost:4646/v1/jobs",
        status_code=200,
        json={
            
        },

        match_headers={"Content-Type": "application/json"},
    )
    async with httpx.AsyncClient() as client:

        service = NomadService(client=client, config=NomadServiceConfig())
        
        await service.schedule_job(job_hcl="""
        
            job "job123" {
                # should we put full content here?
            }
            """
        )

