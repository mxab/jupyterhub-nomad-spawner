from logging import Logger, LoggerAdapter
from pathlib import Path
from typing import Dict, Optional, Tuple, Union, Any

from attrs import define
from httpx import AsyncClient
from pydantic import AnyHttpUrl, BaseModel, parse_obj_as

from jupyterhub_nomad_spawner.nomad.nomad_model import (
    CSIVolume,
    CSIVolumeCapability,
    CSIVolumeCreateRequest,
    JobsParseRequest,
)


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


class NomadException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


@define
class NomadService:
    client: AsyncClient
    log: Union[LoggerAdapter, Logger]

    async def create_volume(
        self,
        id: str,
        plugin_id: str,
        parameters: Optional[Dict[str, str]] = None,
        min_size: Optional[int] = None,
    ):
        request = CSIVolumeCreateRequest(
            Volumes=[
                CSIVolume(
                    ID=id,
                    Name=id,
                    ExternalID=id,
                    AttachmentMode="file-system",
                    AccessMode="single-node-writer",
                    PluginID=plugin_id,
                    RequestedCapabilities=[
                        CSIVolumeCapability(
                            AttachmentMode="file-system",
                            AccessMode="single-node-writer",
                        )
                    ],
                    Parameters=parameters,
                    RequestedCapacityMin=min_size,
                )
            ]
        )

        create_volume_json = request.dict(exclude_none=True, exclude_unset=True)
        result = await self.client.put(
            f"/v1/volume/csi/{id}/create",
            json=create_volume_json,
        )
        if result.is_error:
            if 'ErrorCode: "AccessPointAlreadyExists"' not in result.text:
                raise NomadException(
                    "Error registering volume."
                    + f" status code: {result.status_code}, content: {result.text}"
                )
        self.log.info("Created volume (status code: %d)", result.status_code)

    async def delete_volume(self, id: str):
        result = await self.client.post(
            f"/v1/volume/csi/{id}/delete",
        )
        if result.is_error:
            raise NomadException(f"Error deleting volume: {result.text}")

    async def schedule_job(self, job_hcl: str) -> Tuple[str, str]:
        self.log.info("Parsing job: %s", job_hcl)
        job_parse_request = JobsParseRequest(JobHCL=job_hcl, Canonicalize=True)
        parsed_job = await self.client.post(
            "/v1/jobs/parse",
            json=job_parse_request.dict(exclude_none=True, exclude_unset=True),
        )

        if parsed_job.is_error:
            raise NomadException(f"Error parsing job: {parsed_job.text}")

        parsed_job_as_dict = parsed_job.json()
        self.log.info("Got parsed job %s", parsed_job_as_dict)
        job_id = parsed_job_as_dict["ID"]

        register_job_as_dict = {
            "EnforceIndex": False,
            "PreserveCounts": True,
            "PolicyOverride": False,
            "JobModifyIndex": 0,
            "Job": parsed_job_as_dict,
        }
        job = await self.client.post(
            "/v1/jobs",
            json=register_job_as_dict,
        )
        if job.is_error:
            raise NomadException(f"Error registering job: {job.text}")

        return job_id

    async def job_status(self, job_id) -> str:
        response = await self.client.get(f"/v1/job/{job_id}")
        if response.is_error:
            raise NomadException(f"Error getting job status: {response.text}")

        job_detail = response.json()
        return job_detail.get("Status", "")

    async def job_allocations(self, job_id) -> list[dict[str, Any]]:
        response = await self.client.get(f"/v1/job/{job_id}/allocations")
        if response.is_error:
            raise NomadException(f"Error getting job allocations: {response.text}")

        allocations = response.json()
        return allocations

    async def delete_job(self, job_id: str, purge: Optional[bool] = None):
        params = {"purge": purge} if purge else None
        response = await self.client.delete(f"/v1/job/{job_id}", params=params)
        if response.is_error:
            raise NomadException(f"Error deleting job: {response.text}")

    async def get_service_address(self, service_name: str) -> Tuple[str, int]:
        response = await self.client.get(f"/v1/service/{service_name}")
        if response.is_error:
            raise NomadException(f"Error reading service: {response.text}")

        services = response.json()
        if len(services) == 0:
            raise NomadException(f"Service {service_name} not found")
        if len(services) > 1:
            raise NomadException(f"Multiple services found for {service_name}")
        return str(services[0]["Address"]), int(services[0]["Port"])

    async def get_service_of_allocation(self, allocation_id: str) -> Tuple[str, int]:
        response = await self.client.get(f"/v1/allocation/{allocation_id}")
        if response.is_error:
            raise NomadException(f"Error reading allocation: {response.text}")

        allocation = response.json()

        networks = allocation["Resources"]["Networks"]
        host_port = networks[0]["DynamicPorts"][0]["Value"]

        return str(networks[0]["IP"]), int(host_port)
