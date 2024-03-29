job "jupyter-notebook-123" {

    type = "service"
    datacenters = ["dc1", "dc2"]

    meta {
        jupyterhub_user = "myname"
        
    }
    group "nb" {

        
        ephemeral_disk {
            migrate = true
            size    = 1000
            sticky  = true
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

                
                volumes = [
                    "../alloc/data/notebook:/home/jovyan/work"
                ]
                

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

            
        }

        service {
            name = "jupyter-notebook-123"
            provider = "consul"
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