import os
from enum import Enum
from typing import Dict, List, Optional, Any

from jinja2 import (
    BaseLoader,
    Environment,
    FileSystemLoader,
    PackageLoader,
    select_autoescape,
)
from pydantic import BaseModel


class VolumeType(str, Enum):
    host = "host"
    csi = "csi"
    ephemeral_disk = "ephemeral_disk"


class JobVolumeData(BaseModel):
    type: VolumeType
    source: str = "jupyter"

    volume_name: str = "notebook-data"
    destination: str = "/home/jovyan/work"

    ephemeral_disk_size: Optional[int] = None

    class Config:
        use_enum_values = True


class ServiceProvider(str, Enum):
    consul = "consul"
    nomad = "nomad"


class JobData(BaseModel):
    job_name: str
    username: str
    notebook_name: Optional[str] = None

    service_provider: ServiceProvider
    service_name: str
    env: Dict = {}
    args: List = []
    datacenters: List[str] = []
    region: str = "global"

    image: str = "jupyter/base-notebook:latest"
    memory: int = 512
    cpu: int = 100

    volume_data: Optional[JobVolumeData]
    policies: Optional[List[str]]

    class Config:
        use_enum_values = True


def create_job(job_data: JobData, job_template_path: Optional[str] = None) -> str:
    # if present, split up and use head as filesystem loader and tail as template name
    loader: BaseLoader

    if job_template_path:
        head_tail = os.path.split(job_template_path)
        loader = FileSystemLoader(head_tail[0])
        template_name = head_tail[1]

    else:
        loader = PackageLoader("jupyterhub_nomad_spawner")
        template_name = "job.hcl.j2"
    env = Environment(loader=loader, autoescape=select_autoescape())

    template = env.get_template(template_name)
    job_hcl = template.render(**job_data.dict())

    return job_hcl


def create_job_name(jinja_template: str, data: dict[str, Any]) -> str:
    env = Environment(autoescape=select_autoescape())
    template = env.from_string(jinja_template)

    return template.render(**data)
