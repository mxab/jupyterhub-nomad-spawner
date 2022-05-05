job "jupyterhub" {
    type = "service"

    datacenters = ["dc1"]

    group "jupyterhub" {

        network {
            mode = "host"
            port "hub" {
                to = 8000
            }
            port "api" {
                to = 8081
            }
        }
        task "jupyterhub" {
            driver = "docker"

            config {
                image = "mxab/jupyterhub"
                #auth_soft_fail = false

                args = [
                        "jupyterhub",
                        "-f",
                        "/local/jupyterhub_config.py",
                    ]
                ports = ["hub", "api"]
                #network_mode = "host"
            }
            
            template {
                destination = "/local/jupyterhub_config.py"

                data = <<EOF
import json
import os
import socket
import tarfile
c.JupyterHub.spawner_class = "jupyterhub_nomad_spawner.spawner:NomadSpawner"
c.JupyterHub.bind_url = "http://0.0.0.0:8000"
c.JupyterHub.hub_bind_url = "http://0.0.0.0:8081"

c.JupyterHub.hub_connect_url = f"http://{os.environ.get('NOMAD_IP_api')}:{os.environ.get('NOMAD_HOST_PORT_api')}"
c.JupyterHub.log_level = "DEBUG"
c.ConfigurableHTTPProxy.debug = True
c.JupyterHub.authenticator_class = 'dummy'

                EOF


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