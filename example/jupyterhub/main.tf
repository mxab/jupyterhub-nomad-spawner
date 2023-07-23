terraform {
  required_providers {
    nomad = {
      source = "hashicorp/nomad"
      version = "2.0.0-beta.1"
    }
  }
}

provider "nomad" {
  address = "http://localhost:4646"
}
variable "openai_api_key" {
  type = string
  sensitive = true

}
resource "nomad_variable" "openai_api_key" {
  path = "openai"
  items = {
    openai_api_key : var.openai_api_key
  }
}
resource "nomad_job" "jupyterhub" {
  jobspec = templatefile("jupyterhub.nomad", {

  })
  hcl2 {
    allow_fs = true
  }
}
