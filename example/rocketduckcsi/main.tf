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

variable "nfs_server" {
  type = string

}
resource "nomad_job" "rocketduck_controller" {
  jobspec = templatefile("rocketduck-controller.nomad", {
    nfs_server = var.nfs_server
  })
}

resource "nomad_job" "rocketduck_node" {
  jobspec = templatefile("rocketduck-node.nomad", {
    nfs_server = var.nfs_server
  })
}
