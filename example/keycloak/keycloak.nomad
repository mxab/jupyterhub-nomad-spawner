job "keycloak" {
    type = "service"

    datacenters = ["dc1"]

    group "keycloak" {

        network {
            port "http" {
                to = 8080
                static = 8080
            }
        }
        task "keycloak" {
            driver = "docker"
            config {
                image = "quay.io/keycloak/keycloak:21.1.1"
                command = "start-dev"
                ports = ["http"]
            }
            env {
                KEYCLOAK_ADMIN = "admin"
                KEYCLOAK_ADMIN_PASSWORD = "admin"
            }
            resources {
                memory = "512"
            }
        }
        service {
            name = "keycloak"
            port = "http"
            provider = "nomad"

            check {
                type = "http"
                path = "/"
                interval = "10s"
                timeout = "2s"
            }
        }
    }
}
