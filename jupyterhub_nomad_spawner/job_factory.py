from enum import Enum
from typing import Dict, List, Optional, Tuple
from string import Template
import json

from pydantic import BaseModel


class VolumeType(str, Enum):
    host = "host"
    csi = "csi"


class JobVolumeData(BaseModel):
    type: VolumeType
    source: str = "jupyter"

    volume_name: str = "notebook-data"
    destination: str = "/home/jovyan/work"


class JobData(BaseModel):
    username: str
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

    env_json = "\n".join(
        [f"{key} = {json.dumps(value)}" for key, value in job_data.env.items()]
    )

    datacenters_json = json.dumps(job_data.datacenters)

    (volume_hcl, volume_mount_hcl) = create_volume_job_fragments(job_data.volume_data)

    job_spec_tmpl = Template(
        """


 job "jupyter-notebook-${username}" {

    datacenters = ${datacenters_json}



    group "nb" {

        ${volume_hcl}

        network {
            #mode = "host"
            port "notebook" {
                to = 8888
            }
        }
        task "nb" {
            driver = "docker"

            config {
                image = "${image}"
                ports = ["notebook"]
              #  volumes = ["local/work:/home/jovyan/work"]
                args = ${args}
            }
            env {
                ${env_json}
                JUPYTER_ENABLE_LAB="yes"
             #   GRANT_SUDO="yes"
            }

            resources {
                cpu    = ${cpu}
                memory = ${memory}
            }

            ${volume_mount_hcl}
        }

        service {
            name = "${service_name}"
            port = "notebook"
             check {
                name     = "alive"
                type     = "tcp"
                interval = "10s"
                timeout  = "2s"
            }
        }
    }
}
"""
    )
    job_hcl = job_spec_tmpl.safe_substitute(
        {
            **job_data.dict(),
            "env_json": env_json,
            "datacenters_json": datacenters_json,
            "volume_hcl": volume_hcl,
            "volume_mount_hcl": volume_mount_hcl,
        }
    )
    return job_hcl


def create_volume_job_fragments(
    volume_data: Optional[JobVolumeData],
) -> Tuple[str, str]:

    if volume_data is None:
        return "", ""

    volume_hcl = Template(
        """
    volume "${volume_name}" {
      type      = "${type}"
      read_only = false
      source    = "${source}"
    }
    """
    ).safe_substitute({**volume_data.dict(), "type": volume_data.type.value})

    volume_mount_hcl = Template(
        """
    volume_mount {
        volume      = "${volume_name}"
        destination = "${destination}"
        read_only   = false
    }
    """
    ).safe_substitute(volume_data.dict())

    return volume_hcl, volume_mount_hcl


class NomadVolumeData(BaseModel):
    foo: str
