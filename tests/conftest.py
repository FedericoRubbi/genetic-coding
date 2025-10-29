"""
Pytest configuration and shared fixtures.
"""

import sys
import pytest
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# ============================================================================
# Fixtures for SuperCollider/SuperDirt
# ============================================================================

@pytest.fixture(scope="session")
def supercollider_client():
    """
    Create OSC client for SuperCollider server.
    
    Skips tests if SuperCollider is not available.
    """
    try:
        from pythonosc import udp_client
        client = udp_client.SimpleUDPClient("127.0.0.1", 57110)
        yield client
    except Exception as e:
        pytest.skip(f"SuperCollider not available: {e}")


@pytest.fixture(scope="session")
def superdirt_client():
    """
    Create OSC client for SuperDirt.
    
    Skips tests if SuperDirt is not available.
    """
    try:
        from pythonosc import udp_client
        client = udp_client.SimpleUDPClient("127.0.0.1", 57120)
        yield client
    except Exception as e:
        pytest.skip(f"SuperDirt not available: {e}")


@pytest.fixture(scope="session")
def backend():
    """
    Create backend instance for integration tests.
    """
    from genetic_music.backend import Backend
    backend = Backend(orbit=8)
    yield backend
    # Cleanup
    backend.stop_all()


# ============================================================================
# Pytest Hooks
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "supercollider: tests requiring SuperCollider server"
    )
    config.addinivalue_line(
        "markers", "superdirt: tests requiring SuperDirt"
    )
    config.addinivalue_line(
        "markers", "audio: tests that produce audio output"
    )


def pytest_collection_modifyitems(config, items):
    """
    Auto-mark integration tests based on file/test names.
    """
    for item in items:
        # Mark SuperCollider tests
        if "supercollider" in item.nodeid.lower():
            item.add_marker(pytest.mark.supercollider)
            item.add_marker(pytest.mark.integration)
        
        # Mark SuperDirt tests
        if "superdirt" in item.nodeid.lower():
            item.add_marker(pytest.mark.superdirt)
            item.add_marker(pytest.mark.integration)
            item.add_marker(pytest.mark.audio)
        
        # Mark TidalCycles tests
        if "tidal" in item.nodeid.lower():
            item.add_marker(pytest.mark.integration)


# ============================================================================
# Helper Functions
# ============================================================================

def is_supercollider_available():
    """Check if SuperCollider is available and responding."""
    try:
        from pythonosc import udp_client
        client = udp_client.SimpleUDPClient("127.0.0.1", 57110)
        # Try to send a status request
        client.send_message("/status", [])
        return True
    except Exception:
        return False


def is_superdirt_available():
    """Check if SuperDirt is available."""
    try:
        from pythonosc import udp_client
        client = udp_client.SimpleUDPClient("127.0.0.1", 57120)
        return True
    except Exception:
        return False

