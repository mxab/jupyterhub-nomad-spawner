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
# https://github.com/hashicorp/terraform-provider-nomad/issues/288
# resource "nomad_variable" "dummy_openai_key" {
#   path = "openai"
#   items = {
#     open_ai_key : "sk_dummy-key"
#   }
# }
resource "nomad_job" "jupyterhub" {
  jobspec = templatefile("jupyterhub.nomad", {

  })

  hcl2 {
    enabled = true
    allow_fs = true

  }

}
