from enum import Enum
from optparse import Option
from typing import Dict, List, Optional, Tuple
from string import Template
import json
from jinja2 import Environment, PackageLoader, select_autoescape

from pydantic import BaseModel


class VolumeType(str, Enum):
    host = "host"
    csi = "csi"


class JobVolumeData(BaseModel):
    type: VolumeType
    source: str = "jupyter"

    volume_name: str = "notebook-data"
    destination: str = "/home/jovyan/work"

    class Config:
        use_enum_values = True


class JobData(BaseModel):

    job_name: str
    username: str
    notebook_name: Optional[str] = None

    env: Dict = {}
    args: List = []
    datacenters: List[str] = []
    region: str = "global"

    service_name: str = "${JOB}-notebook"
    image: str = "jupyter/base-notebook:latest"
    memory: int = 512
    cpu: int = 100

    volume_data: Optional[JobVolumeData]


def create_job(job_data: JobData) -> str:

    env = Environment(
        loader=PackageLoader("jupyterhub_nomad_spawner"), autoescape=select_autoescape()
    )

    template = env.get_template("job.hcl.j2")
    job_hcl = template.render(**job_data.dict())

    return job_hcl
