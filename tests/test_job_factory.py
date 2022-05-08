from jupyterhub_nomad_spawner.job_factory import JobData, create_job


def test_create_job():

    job = create_job(JobData(username="myname", env={"foo": "bar"}))

    assert job == """
 job "jupyter-notebook-myname" {

    datacenters = ["dc1"]

    group "nb" {
        network {
            mode = "host"
            port "notebook" {
                to = 8888
            }
        }
        task "nb" {
            driver = "docker"

            config {
                image = "jupyter/base-notebook:python-3.8.6"
                ports = ["notebook"]
                network_mode = "host"
            }
            env {
                foo = "bar"
                JUPYTER_ENABLE_LAB="yes"
                GRANT_SUDO="yes"
            }

            resources {
                cpu    = 500
                memory = 256
            }
        }

        service {
            name = "${JOB}-notebook"
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
"""