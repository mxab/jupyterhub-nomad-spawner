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

# resource "keycloak_openid_client" "jupyterhub" {
#   realm_id            = "master"
#   client_id           = "jupyterhub"

#   name                = "jupyterhub"
#   enabled             = true

#   access_type         = "CONFIDENTIAL"

# standard_flow_enabled =  true
#   root_url = "http://<keycloak-external-ip>:8000"
#   base_url = "/"
#   valid_redirect_uris = [
#     "/hub/oauth_callback"
#   ]
#   web_origins = [ "+" ]
#   admin_url ="/"

#   login_theme = "keycloak"
#   client_secret = "jupyterhub"
# }
