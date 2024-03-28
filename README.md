# Nomad Jupyter Spawner

> [!WARNING]
> This project is currently in beta

A Jupyterhub plugin to spawn single-user notebook servers via [Nomad](https://www.nomadproject.io/). The project provides templates to allow users to influence how their servers are spawned (see the [showcase](#-show-case) and [recipes](#-recipes) for more details.).

After login users can select an image, resources and connect it with volumes (csi / host)

```sh
pip install jupyterhub-nomad-spawner
```

## Show Case

https://user-images.githubusercontent.com/1607547/182332760-b0f96ba2-faa8-47b6-9bd7-db93b8d31356.mp4

TODOs:

- Document setup
- Namespace support

## Usage

### Jupyterhub Configuration

```python

import os

from jupyterhub.auth import DummyAuthenticator

c.JupyterHub.spawner_class = "nomad-spawner"
c.JupyterHub.bind_url = "http://0.0.0.0:8000"
c.JupyterHub.hub_bind_url = "http://0.0.0.0:8081"

c.JupyterHub.hub_connect_url = (
    f"http://{os.environ.get('NOMAD_IP_api')}:{os.environ.get('NOMAD_HOST_PORT_api')}"
)
c.JupyterHub.log_level = "DEBUG"
c.ConfigurableHTTPProxy.debug = True


c.JupyterHub.allow_named_servers = True
c.JupyterHub.named_server_limit_per_user = 5

c.JupyterHub.authenticator_class = DummyAuthenticator

c.NomadSpawner.datacenters = ["dc1", "dc2", "dc3"]
c.NomadSpawner.csi_plugin_ids = ["nfs", "hostpath-plugin0"]
c.NomadSpawner.mem_limit = "2G"

c.NomadSpawner.common_images = ["jupyter/minimal-notebook:2023-06-26"]


def csi_volume_parameters(spawner):
    if spawner.user_options["volume_csi_plugin_id"] == "nfs":
        return {"gid": "1000", "uid": "1000"}
    else:
        return None


c.NomadSpawner.csi_volume_parameters = csi_volume_parameters

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
import os

from jupyterhub.auth import DummyAuthenticator

c.JupyterHub.spawner_class = "nomad-spawner"
c.JupyterHub.bind_url = "http://0.0.0.0:8000"
c.JupyterHub.hub_bind_url = "http://0.0.0.0:8081"

c.JupyterHub.hub_connect_url = (
    f"http://{os.environ.get('NOMAD_IP_api')}:{os.environ.get('NOMAD_HOST_PORT_api')}"
)
c.JupyterHub.log_level = "DEBUG"
c.ConfigurableHTTPProxy.debug = True


c.JupyterHub.allow_named_servers = True
c.JupyterHub.named_server_limit_per_user = 5

c.JupyterHub.authenticator_class = DummyAuthenticator

c.NomadSpawner.datacenters = ["dc1", "dc2", "dc3"]
c.NomadSpawner.csi_plugin_ids = ["nfs", "hostpath-plugin0"]
c.NomadSpawner.mem_limit = "2G"

c.NomadSpawner.common_images = ["jupyter/minimal-notebook:2023-06-26"]


def csi_volume_parameters(spawner):
    if spawner.user_options["volume_csi_plugin_id"] == "nfs":
        return {"gid": "1000", "uid": "1000"}
    else:
        return None


c.NomadSpawner.csi_volume_parameters = csi_volume_parameters

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

## Recipes

By default the `jupyterhub-nomad-spawner` allows users to customize the notebook servers image, the datacenters to spawn in, as well as the memory and volume type for the allocation. While these options are sufficient in most cases, `jupyterhub` operators may wish to customize the spawner's behavior and/or restrict the notebook users customization.

- using a custom job spec

  ```python
  # must be available to your hub server
  c.NomadSpawner.job_template_path = "/etc/jupyterhub/custom-job-template.hcl.j2"

  ```

- disabling user options

  ```python
  # skips the options dialogue, which is used to populate `NomadSpawner.user_options`
  # therefore you would also have to overwrite the default `job_factory``
  c.NomadSpawner.options_form = ""
  ```

- using a custom job factory

  ```python
  from jupyterhub_nomad_spawner.spawner import NomadSpawner
  from jupyterhub_nomad_spawner.job_factory import (
    JobData,
    create_job,
    )


  class CustomNomadSpawner(NomadSpawner):
    async def job_factory(self, _) -> str:
        return create_job(
            job_data=JobData(
                job_name=self.job_name,
                username=self.user.name,
                notebook_name=self.name,
                service_provider=self.service_provider,
                service_name=self.service_name,
                env=self.get_env(),
                args=self.get_args(),
                image="jupyter/minimal-notebook",
                datacenters=["dc1", "dc2"],
                cpu=500,
                memory=512,
            ),
            job_template_path=self.job_template_path,
        )

    c.JupyterHub.spawner_class = CustomNomadSpawner
  ```

- customizing server naming

  ```python
  c.NomadSpawner.base_job_name = "jupyter"   # used as prefix
  c.NomadSpawner.name_template = "{{prefix}}-{{username}}"
  ```

> [!NOTE]
> Please be aware that if you have enabled named servers, the template should contain the {{notebookid}}.

###

## Development

### Setup

Get poetry: https://python-poetry.org/docs/#installation

```sh
poetry install
```

### Release
