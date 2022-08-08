job "csi-plugin" {
  datacenters = ["dc1"]

  group "csi" {
    task "plugin" {
      driver = "docker"

      config {
        image = "k8s.gcr.io/sig-storage/hostpathplugin:v1.8.0"


        args = [
         "--drivername=csi-hostpath",
          "--v=5",
          "--endpoint=$${CSI_ENDPOINT}",
          "--nodeid=node-$${NOMAD_ALLOC_INDEX}",
        ]


        privileged = true
      }

      csi_plugin {
        id        = "hostpath-plugin0"
        type      = "monolith"
        mount_dir = "/csi"
      }

      resources {
        cpu    = 500
        memory = 256

        network {
          mbits = 10
          port  "plugin" {}
        }
      }
    }
  }
}