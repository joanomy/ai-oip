"""Smoke test: proves the toolchain (pytest, coverage, imports) is wired correctly.

This test intentionally checks nothing business-relevant. Its only job is to
fail loudly if the environment, package install, or CI pipeline is broken.
"""

from ai_iop import __version__


def test_package_is_importable_and_versioned() -> None:
    assert __version__ == "0.0.1"
