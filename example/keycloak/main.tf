terraform {
  required_providers {
    nomad = {
      source = "hashicorp/nomad"
      version = "1.4.20"
    }
  }
}

provider "nomad" {
  address = "http://localhost:4646"
}

resource "nomad_job" "keycloak" {
  jobspec = templatefile("keycloak.nomad", {

  })
}
