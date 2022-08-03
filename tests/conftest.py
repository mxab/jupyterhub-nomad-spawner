import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--runintegration", action="store_true", help="run integration tests"
    )
    parser.addoption(
        "--update-job-fixtures",
        action="store_true",
        help="update job fixtures",
        default=False,
    )
    parser.addoption(
        "--update-job-options-fixtures",
        action="store_true",
        help="update job options form fixture",
        default=False,
    )


def pytest_runtest_setup(item):
    if "integration" in item.keywords and not item.config.getvalue("runintegration"):
        pytest.skip("need --runintegration option to run")


@pytest.fixture(scope="session")
def update_job_fixtures(pytestconfig):
    return pytestconfig.getoption("--update-job-fixtures")


@pytest.fixture(scope="session")
def update_job_options_fixtures(pytestconfig):
    return pytestconfig.getoption("--update-job-options-fixtures")
