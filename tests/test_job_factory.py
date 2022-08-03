import logging
from pathlib import Path

from jupyterhub_nomad_spawner.job_factory import (
    JobData,
    JobVolumeData,
    VolumeType,
    create_job,
)

log = logging.getLogger(__name__)


def fixture_path(test: str):
    return f"{Path(__file__).parent}/fixtures/{test}.nomad"


def fixture_content(test: str):
    return open(fixture_path(test), "r").read()


def update_fixture(test: str, job: str):
    log.warning("Updating job fixtures")
    f = open(fixture_path(test), "w")
    f.write(job)
    f.close()


def test_create_job(update_job_fixtures: bool):

    job = create_job(
        JobData(
            job_name="jupyter-notebook-123",
            service_name="jupyter-notebook-123",
            username="myname",
            notebook_name="mynotebook",
            env={"foo": "bar", "some_list": '["a", "b", "c"]'},
            datacenters=["dc1", "dc2"],
            args=["--arg1", "--arg2"],
            image="jupyter/minimal-notebook",
            cpu=500,
            memory=512,
        )
    )
    if update_job_fixtures:
        update_fixture("test_create_job", job)
    assert job == fixture_content("test_create_job")


def test_create_job_with_host_volume(update_job_fixtures: bool):

    job = create_job(
        JobData(
            job_name="jupyter-notebook-123",
            service_name="jupyter-notebook-123",
            username="myname",
            env={"foo": "bar"},
            datacenters=["dc1", "dc2"],
            args=["--arg1", "--arg2"],
            image="jupyter/minimal-notebook",
            cpu=500,
            memory=512,
            volume_data=JobVolumeData(
                type=VolumeType.host,
                source="jupyternotebookhostvolume",
                destination="/home/jovyan/work",
            ),
        )
    )
    if update_job_fixtures:
        update_fixture("test_create_job_with_host_volume", job)
    assert job == fixture_content("test_create_job_with_host_volume")


def test_create_job_with_csi_volume(update_job_fixtures: bool):

    job = create_job(
        JobData(
            job_name="jupyter-notebook-123",
            service_name="jupyter-notebook-123",
            username="myname",
            env={"foo": "bar"},
            datacenters=["dc1", "dc2"],
            args=["--arg1", "--arg2"],
            image="jupyter/minimal-notebook",
            cpu=500,
            memory=512,
            volume_data=JobVolumeData(
                type=VolumeType.csi,
                source="somecsivolumeid",
                destination="/home/jovyan/work",
            ),
        )
    )
    if update_job_fixtures:
        update_fixture("test_create_job_with_csi_volume", job)
    assert job == fixture_content("test_create_job_with_csi_volume")
