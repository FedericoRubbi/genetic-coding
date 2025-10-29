"""
SuperDirt integration tests using pytest.

Run with: pytest tests/test_superdirt_pytest.py -v
Skip audio tests: pytest -m "not audio"
"""

import pytest
import time


@pytest.mark.superdirt
@pytest.mark.integration
@pytest.mark.audio
class TestSuperDirtBasics:
    """Basic SuperDirt functionality tests."""
    
    def test_connection(self, superdirt_client):
        """Test SuperDirt connection."""
        assert superdirt_client is not None
    
    def test_kick_drum(self, superdirt_client):
        """Test playing a kick drum."""
        superdirt_client.send_message("/dirt/play", [
            "cps", 0.5,
            "cycle", 0.0,
            "delta", 1.0,
            "orbit", 8,
            "s", "bd",
            "n", 0,
            "gain", 1.0
        ])
        time.sleep(0.5)
        assert True
    
    def test_snare(self, superdirt_client):
        """Test playing a snare."""
        superdirt_client.send_message("/dirt/play", [
            "cps", 0.5,
            "cycle", 0.0,
            "delta", 1.0,
            "orbit", 8,
            "s", "sn",
            "n", 0,
            "gain", 1.0
        ])
        time.sleep(0.5)
        assert True


@pytest.mark.superdirt
@pytest.mark.integration
@pytest.mark.audio
@pytest.mark.parametrize("sample", ["bd", "sn", "hh", "cp"])
def test_drum_samples(superdirt_client, sample):
    """Test different drum samples."""
    superdirt_client.send_message("/dirt/play", [
        "cps", 0.5,
        "cycle", 0.0,
        "delta", 1.0,
        "orbit", 8,
        "s", sample,
        "n", 0,
        "gain", 0.8
    ])
    time.sleep(0.3)
    assert True


@pytest.mark.superdirt
@pytest.mark.integration
@pytest.mark.audio
class TestSuperDirtParameters:
    """Test SuperDirt parameters (gain, speed, pan)."""
    
    @pytest.mark.parametrize("gain", [0.3, 0.6, 1.0])
    def test_gain_parameter(self, superdirt_client, gain):
        """Test different gain values."""
        superdirt_client.send_message("/dirt/play", [
            "cps", 0.5,
            "cycle", 0.0,
            "delta", 1.0,
            "orbit", 8,
            "s", "bd",
            "n", 0,
            "gain", gain
        ])
        time.sleep(0.4)
        assert True
    
    @pytest.mark.parametrize("speed", [0.5, 1.0, 2.0])
    def test_speed_parameter(self, superdirt_client, speed):
        """Test different playback speeds."""
        superdirt_client.send_message("/dirt/play", [
            "cps", 0.5,
            "cycle", 0.0,
            "delta", 1.0,
            "orbit", 8,
            "s", "sn",
            "n", 0,
            "speed", speed,
            "gain", 0.8
        ])
        time.sleep(0.4)
        assert True
    
    @pytest.mark.parametrize("pan", [0.0, 0.5, 1.0])
    def test_pan_parameter(self, superdirt_client, pan):
        """Test stereo panning."""
        superdirt_client.send_message("/dirt/play", [
            "cps", 0.5,
            "cycle", 0.0,
            "delta", 1.0,
            "orbit", 8,
            "s", "hh",
            "n", 0,
            "pan", pan,
            "gain", 0.8
        ])
        time.sleep(0.4)
        assert True


@pytest.mark.superdirt
@pytest.mark.integration
@pytest.mark.parametrize("orbit", [0, 8, 11])
def test_multiple_orbits(superdirt_client, orbit):
    """Test sending to different orbits."""
    superdirt_client.send_message("/dirt/play", [
        "cps", 0.5,
        "cycle", 0.0,
        "delta", 1.0,
        "orbit", orbit,
        "s", "bd",
        "n", 0,
        "gain", 0.8
    ])
    time.sleep(0.3)
    assert True

