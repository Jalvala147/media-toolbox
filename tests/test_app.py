from app import VERSION


def test_app_version():
    assert VERSION.startswith("2.3")
