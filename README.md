# Nomad Jupyter Spawner


> **Warning**
> This project is currently in beta

Spawns a Jupyter Notebook via Jupyterhub.

Users can select and image, resource and connect it with volumes (csi / host)

```sh
pip install jupyterhub-nomad-spawner
```

## Show Case
https://user-images.githubusercontent.com/1607547/182332760-b0f96ba2-faa8-47b6-9bd7-db93b8d31356.mp4


TODOs:
- Document setup
- Namespace support


## Usage

### Config
```python

import json
import os
import socket

from jupyterhub.auth import DummyAuthenticator
import tarfile
c.JupyterHub.spawner_class = "nomad-spawner"
c.JupyterHub.bind_url = "http://0.0.0.0:8000"
c.JupyterHub.hub_bind_url = "http://0.0.0.0:8081"
c.JupyterHub.hub_connect_url = f"http://{os.environ.get('NOMAD_IP_api')}:{os.environ.get('NOMAD_HOST_PORT_api')}"

c.JupyterHub.allow_named_servers = True
c.JupyterHub.named_server_limit_per_user = 5

c.JupyterHub.authenticator_class = DummyAuthenticator

c.NomadSpawner.mem_limit = "2G"
c.NomadSpawner.datacenters = ["dc1", "dc2", "dc3"]

```


### Nomad Job


```hcl

job "jupyterhub" {
    type = "service"

    datacenters = ["dc1"]

    group "jupyterhub" {

        network {
            mode = "host"
            port "hub" {
                to = 8000
                static = 8000
            }
            port "api" {
                to = 8081
            }
        }
        task "jupyterhub" {
            driver = "docker"

            config {
                image = "mxab/jupyterhub:1"
                auth_soft_fail = false

                args = [
                        "jupyterhub",
                        "-f",
                        "/local/jupyterhub_config.py",
                    ]
                ports = ["hub", "api"]

            }
            template {
                destination = "/local/nomad.env"
                env = true
                data = <<EOF

NOMAD_ADDR=http://host.docker.internal:4646
CONSUL_HTTP_ADDR=http://host.docker.internal:8500
    EOF
            }
            template {
                destination = "/local/jupyterhub_config.py"

                data = <<EOF
import json
import os
import socket

from jupyterhub.auth import DummyAuthenticator
import tarfile
c.JupyterHub.spawner_class = "nomad-spawner"
c.JupyterHub.bind_url = "http://0.0.0.0:8000"
c.JupyterHub.hub_bind_url = "http://0.0.0.0:8081"

c.JupyterHub.hub_connect_url = f"http://{os.environ.get('NOMAD_IP_api')}:{os.environ.get('NOMAD_HOST_PORT_api')}"
c.JupyterHub.log_level = "DEBUG"
c.ConfigurableHTTPProxy.debug = True


c.JupyterHub.allow_named_servers = True
c.JupyterHub.named_server_limit_per_user = 3

c.JupyterHub.authenticator_class = DummyAuthenticator

c.NomadSpawner.datacenters = ["dc1"]

c.NomadSpawner.mem_limit = "2G"


c.NomadSpawner.common_images = ["jupyter/minimal-notebook:2022-08-20"]

def csi_volume_parameters(spawner):
    if spawner.user_options["volume_csi_plugin_id"] == "nfs":
        return {
            "gid" : "1000",
            "uid" : "1000"
        }
    else:
        return None
c.NomadSpawner.csi_volume_parameters = csi_volume_parameters


def vault_policies(spawner):
    return [f"my-policy-{spawner.user.name}"]
c.NomadSpawner.vault_policies = vault_policies

                EOF


            }

            resources {
                memory = "512"
            }

        }

        service {
            name = "jupyter-hub"
            port = "hub"

            check {
                type     = "tcp"
                interval = "10s"
                timeout  = "2s"
            }

        }
        service {
            name = "jupyter-hub-api"
            port = "api"
            check {
                type     = "tcp"
                interval = "10s"
                timeout  = "2s"
            }

        }
    }
}


```
