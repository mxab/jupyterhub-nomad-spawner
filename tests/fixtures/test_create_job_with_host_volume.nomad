job "jupyter-notebook-123" {

    type = "service"
    datacenters = ["dc1", "dc2"]

    meta {
        jupyterhub_user = "myname"
        
    }
    group "nb" {

        
        volume "notebook-data" {
            type      = "host"
            read_only = false
            source    = "jupyternotebookhostvolume"
        }
        

        network {
            port "notebook" {
                to = 8888
            }
        }

        task "nb" {
            driver = "docker"

            config {
                image = "jupyter/minimal-notebook"
                ports = [ "notebook" ]

                args = ["--arg1", "--arg2"]
            }
            env {
                
                foo = "bar"
                
                JUPYTER_ENABLE_LAB="yes"
                # GRANT_SUDO="yes"
            }

            resources {
                cpu    = 500
                memory = 512
            }

            
            volume_mount {
                volume      = "notebook-data"
                destination = "/home/jovyan/work"
                read_only   = false
            }
            
        }

        service {
            name = "jupyter-notebook-123"
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