terraform {
  required_providers {
    nomad = {
      source = "hashicorp/nomad"
      version = "1.4.16"
    }
    keycloak = {
      source = "mrparkers/keycloak"
      version = "3.8.0"
    }
  }
}

provider "nomad" {
  address = "http://localhost:4646"
}
# provider "keycloak" {
#   base_path = ""
#   url = "http://<keycloak-external-ip>:8080"

#   realm = "master"
#   username = "admin"
#   password = "admin"
#   client_id = "admin-cli"
# }

resource "nomad_job" "jupyterhub" {
  jobspec = templatefile("jupyterhub.nomad", {

  })
}
