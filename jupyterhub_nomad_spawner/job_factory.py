from typing import Dict, List
from string import Template
import json


def create_job(username: str, env: Dict = {}, args: List = []) -> str:

    env = "\n".join([f'{key} = {json.dumps(value)}' for key, value in env.items()])

    service_name = "${JOB}-notebook"
    job_spec_tmpl = Template(
        """
 job "jupyter-notebook-${username}" {

    datacenters = ["dc1"]

    group "nb" {
        network {
            #mode = "host"
            port "notebook" {
                to = 8888
            }
        }
        task "nb" {
            driver = "docker"

            config {
                image = "jupyter/base-notebook:latest"
                ports = ["notebook"]
                
                args = ${args}
            }
            env {
                ${env}
                JUPYTER_ENABLE_LAB="yes"
             #   GRANT_SUDO="yes"
            }

            resources {
                cpu    = 500
                memory = 256
            }
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
        {"username": username, "env": env, "service_name": service_name, "args": args}
    )
    return job_hcl
