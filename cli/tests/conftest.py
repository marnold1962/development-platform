import pytest


@pytest.fixture
def platform_root():
    from devcli.paths import PLATFORM_ROOT
    return PLATFORM_ROOT
