# flake8: noqa
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

# c.NomadSpawner.job_template_path = "/local/job.hcl.j2"
