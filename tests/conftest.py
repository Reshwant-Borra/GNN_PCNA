def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "slow: expensive checks (CPU training runs). Deselect with -m 'not slow'.",
    )
