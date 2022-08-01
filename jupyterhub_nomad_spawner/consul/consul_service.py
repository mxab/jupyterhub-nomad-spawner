from logging import Logger, LoggerAdapter
from pathlib import Path
from typing import Optional, Union
from attrs import define
from httpx import AsyncClient
from pydantic import AnyHttpUrl, BaseModel, parse_obj_as


class ConsulTLSConfig(BaseModel):
    ca_cert: Optional[Path]
    ca_path: Optional[Path]
    client_cert: Path
    client_key: Path
    skip_verify: bool = False
    tls_server_name: Optional[str]


class ConsulServiceConfig(BaseModel):
    consul_http_addr: AnyHttpUrl = parse_obj_as(AnyHttpUrl, "http://localhost:8500")
    consul_http_token: Optional[str]
    tls_config: Optional[ConsulTLSConfig] = None


@define
class ConsulService:
    client: AsyncClient

    log: Union[LoggerAdapter, Logger]

    async def health_service(self, service_name: str):
        result = await self.client.get(
            f"/v1/health/service/{service_name}",
        )
        if result.is_error:
            raise Exception(f"Error getting service: {result.text}")
        return result.json()
