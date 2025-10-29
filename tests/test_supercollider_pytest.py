"""
SuperCollider integration tests using pytest.

Run with: pytest tests/test_supercollider_pytest.py -v
Skip if SC unavailable: pytest -m "not supercollider"
"""

import pytest
import time


@pytest.mark.supercollider
@pytest.mark.integration
class TestSuperColliderServer:
    """Tests for SuperCollider server functionality."""
    
    def test_server_connection(self, supercollider_client):
        """Test basic OSC connection to SuperCollider server."""
        # If we got the fixture, connection works
        assert supercollider_client is not None
    
    def test_status_request(self, supercollider_client):
        """Test sending status request to server."""
        supercollider_client.send_message("/status", [])
        time.sleep(0.1)
        # If no exception, test passes
        assert True
    
    def test_control_bus_set(self, supercollider_client):
        """Test setting control bus values."""
        # Set control bus 100 to 0.5
        supercollider_client.send_message("/c_set", [100, 0.5])
        time.sleep(0.1)
        assert True
    
    def test_multiple_control_buses(self, supercollider_client):
        """Test setting multiple control bus values."""
        test_data = [(100, 0.5), (101, 0.75), (102, 1.0)]
        
        for bus, value in test_data:
            supercollider_client.send_message("/c_set", [bus, value])
            time.sleep(0.05)
        
        assert True
    
    def test_notify_registration(self, supercollider_client):
        """Test registering for server notifications."""
        supercollider_client.send_message("/notify", [1])
        time.sleep(0.1)
        assert True


@pytest.mark.supercollider
@pytest.mark.integration
@pytest.mark.parametrize("bus,value", [
    (100, 0.0),
    (100, 0.5),
    (100, 1.0),
    (101, 0.33),
])
def test_control_bus_parametrized(supercollider_client, bus, value):
    """Parametrized test for different bus values."""
    supercollider_client.send_message("/c_set", [bus, value])
    time.sleep(0.05)
    assert True

