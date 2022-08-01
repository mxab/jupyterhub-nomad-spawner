import logging
from logging import Logger, LoggerAdapter
from pathlib import Path
from typing import Optional, Tuple, Union

from attrs import define
from httpx import AsyncClient
from jupyterhub_nomad_spawner.nomad.nomad_model import (
    CSIVolume,
    CSIVolumeCreateRequest,
    CSIVolumeRegisterRequest,
    JobRegisterResponse,
    JobsParseRequest,
)
from pydantic import AnyHttpUrl, BaseModel, parse_obj_as


class NomadTLSConfig(BaseModel):
    ca_cert: Optional[Path]
    ca_path: Optional[Path]
    client_cert: Path
    client_key: Path
    skip_verify: bool = False
    tls_server_name: Optional[str]


class NomadServiceConfig(BaseModel):
    nomad_addr: AnyHttpUrl = parse_obj_as(AnyHttpUrl, "http://localhost:4646")
    nomad_token: Optional[str]
    tls_config: Optional[NomadTLSConfig] = None


@define
class NomadService:

    client: AsyncClient
    log: Union[LoggerAdapter, Logger]

    async def create_volume(self, id: str, plugin_id: str):
        request = CSIVolumeRegisterRequest(
            Volumes=[
                CSIVolume(
                    ID=id,
                    Name=id,
                    ExternalId=id,
                    AttachmentMode="file-system",
                    AccessMode="single-node-writer",
                    PluginID=plugin_id,
                )
            ]
        )

        result = await self.client.put(
            f"/v1/volume/csi/{id}",
            json=request.dict(exclude_none=True, exclude_unset=True),
        )
        if result.is_error:
            raise Exception(
                f"Error registering volume, status code : {result.status_code}, content: {result.text}"
            )

    async def delete_volume(self, id: str):

        result = await self.client.post(
            f"/v1/volume/csi/{id}/delete",
        )
        if result.is_error:
            raise Exception(f"Error deleting volume: {result.text}")

    async def schedule_job(self, job_hcl: str) -> Tuple[str, str]:

        self.log.info("Parsing job: %s", job_hcl)
        job_parse_request = JobsParseRequest(JobHCL=job_hcl, Canonicalize=True)
        parsed_job = await self.client.post(
            f"/v1/jobs/parse",
            json=job_parse_request.dict(exclude_none=True, exclude_unset=True),
        )

        if parsed_job.is_error:
            raise Exception(f"Error parsing job: {parsed_job.text}")

        parsed_job_as_dict = parsed_job.json()
        self.log.info("Got parsed job %s", parsed_job_as_dict)
        job_id = parsed_job_as_dict["ID"]
        job_name = parsed_job_as_dict["Name"]
        # register_job_request = JobRegisterRequest(
        #     EnforceIndex=False,
        #     PreserveCounts=True,
        #     PolicyOverride=False,
        #     JobModifyIndex=0,
        #     Job=parsed_job_as_dict,
        # )

        # register_job_as_dict = register_job_request.dict(exclude_none=True, exclude_unset=True)
        # self.log.info("Registering job %s", register_job_as_dict)
        register_job_as_dict = {
            "EnforceIndex": False,
            "PreserveCounts": True,
            "PolicyOverride": False,
            "JobModifyIndex": 0,
            "Job": parsed_job_as_dict,
        }
        job = await self.client.post(
            f"/v1/jobs",
            json=register_job_as_dict,
        )
        if job.is_error:
            raise Exception(f"Error registering job: {job.text}")

        job_register_response = JobRegisterResponse.parse_obj(job.json())

        return (job_id, job_name)

    async def job_status(self, job_id) -> str:
        response = await self.client.get(f"/v1/job/{job_id}")
        if response.is_error:
            raise Exception(f"Error getting job status: {response.text}")

        job_detail = response.json()
        return job_detail.get("Status", "")

    async def delete_job(self, job_id: str):
        response = await self.client.delete(f"/v1/job/{job_id}")
        if response.is_error:
            raise Exception(f"Error deleting job: {response.text}")
