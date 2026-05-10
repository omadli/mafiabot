"""Pytest configuration — fixtures shared across tests."""

import pytest


@pytest.fixture
def sample_users() -> list[int]:
    return [100, 101, 102, 103, 104, 105, 106, 107]
