import logging
from pathlib import Path

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
