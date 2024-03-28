job "jupyter-notebook-123" {

    type = "service"
    datacenters = ["dc1", "dc2"]

    meta {
        jupyterhub_user = "myname"
        
    }
    group "nb" {

        

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

                args = []

                

            }
            env {
                
                JPY_API_TOKEN = ""
                
                JUPYTERHUB_ACTIVITY_URL = "api.test/users/myname/activity"
                
                JUPYTERHUB_API_TOKEN = ""
                
                JUPYTERHUB_API_URL = "api.test"
                
                JUPYTERHUB_BASE_URL = ""
                
                JUPYTERHUB_CLIENT_ID = ""
                
                JUPYTERHUB_HOST = "127.0.0.1"
                
                JUPYTERHUB_OAUTH_ACCESS_SCOPES = "[\"access:servers!server=myname/\", \"access:servers!user=myname\"]"
                
                JUPYTERHUB_OAUTH_CALLBACK_URL = "/server/name/lab/oauth_callback"
                
                JUPYTERHUB_OAUTH_CLIENT_ALLOWED_SCOPES = "[]"
                
                JUPYTERHUB_OAUTH_SCOPES = "[\"access:servers!server=myname/\", \"access:servers!user=myname\"]"
                
                JUPYTERHUB_SERVER_NAME = ""
                
                JUPYTERHUB_SERVICE_URL = "http://0.0.0.0:8888/"
                
                JUPYTERHUB_USER = "myname"
                
                LANG = "de_DE.UTF-8"
                
                JUPYTER_ENABLE_LAB="yes"
                # GRANT_SUDO="yes"
            }

            resources {
                cpu    = 100
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