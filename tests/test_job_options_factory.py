import logging

from jupyterhub_nomad_spawner.job_options_factory import create_form

log = logging.getLogger(__name__)


def test_create_form(update_job_options_fixtures):
    datacenters = ["dc1", "dc2"]
    common_images = ["common_image1", "common_image2"]
    csi_plugin_ids = ["csi_plugin_id1", "csi_plugin_id2"]
    memory_limit = 1024
    html = create_form(datacenters, common_images, csi_plugin_ids, memory_limit)

    if update_job_options_fixtures:
        log.warning("Updating job options fixtures")
        with open("tests/fixtures/test_create_form.html", "w") as f:
            f.write(html)
            f.close()

    # compare html against fixture
    with open("tests/fixtures/test_create_form.html", "r") as f:
        fixture = f.read()
        f.close()
    assert html == fixture
