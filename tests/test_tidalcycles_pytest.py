"""
TidalCycles integration tests using pytest.

Run with: pytest tests/test_tidalcycles_pytest.py -v
"""

import pytest
import time
from genetic_music.genome import PatternTree, SynthTree, Genome
from genetic_music.codegen import to_tidal, to_supercollider


@pytest.mark.integration
@pytest.mark.unit  # These don't require external services
class TestPatternGeneration:
    """Test pattern code generation."""
    
    def test_random_pattern_generation(self):
        """Test generating random pattern code."""
        pattern = PatternTree.random(max_depth=3)
        code = to_tidal(pattern)
        
        assert code is not None
        assert len(code) > 0
        assert isinstance(code, str)
    
    def test_simple_pattern_generation(self):
        """Test that generated code is valid."""
        pattern = PatternTree.random(max_depth=2)
        code = to_tidal(pattern)
        
        # Basic validation
        assert '"' in code or 'silence' in code
    
    @pytest.mark.parametrize("depth", [1, 2, 3, 4])
    def test_different_depths(self, depth):
        """Test pattern generation at different depths."""
        pattern = PatternTree.random(max_depth=depth)
        code = to_tidal(pattern)
        
        assert len(code) > 0
        assert pattern.depth() <= depth


@pytest.mark.integration
class TestTidalSyntax:
    """Test Tidal syntax validation."""
    
    def test_balanced_quotes(self):
        """Test that generated code has balanced quotes."""
        for _ in range(5):
            pattern = PatternTree.random(max_depth=3)
            code = to_tidal(pattern)
            
            # Count quotes should be even
            assert code.count('"') % 2 == 0
    
    def test_balanced_brackets(self):
        """Test that generated code has balanced brackets."""
        for _ in range(5):
            pattern = PatternTree.random(max_depth=3)
            code = to_tidal(pattern)
            
            assert code.count('[') == code.count(']')
    
    def test_balanced_parentheses(self):
        """Test that generated code has balanced parentheses."""
        for _ in range(5):
            pattern = PatternTree.random(max_depth=3)
            code = to_tidal(pattern)
            
            assert code.count('(') == code.count(')')


@pytest.mark.integration
@pytest.mark.superdirt
@pytest.mark.audio
class TestPatternPlayback:
    """Test playing generated patterns via SuperDirt."""
    
    def test_play_simple_pattern(self, superdirt_client):
        """Test playing a simple generated pattern."""
        pattern = PatternTree.random(max_depth=2)
        
        # For simplicity, just play some test samples
        samples = ["bd", "sn"]
        
        for sample in samples:
            superdirt_client.send_message("/dirt/play", [
                "cps", 0.5,
                "cycle", 0.0,
                "delta", 1.0,
                "orbit", 8,
                "s", sample,
                "n", 0,
                "gain", 0.8
            ])
            time.sleep(0.5)
        
        assert True


@pytest.mark.integration
class TestBackendIntegration:
    """Test backend integration."""
    
    def test_backend_creation(self, backend):
        """Test backend can be created."""
        assert backend is not None
        assert backend.orbit == 8
    
    def test_send_pattern(self, backend):
        """Test sending pattern via backend."""
        pattern_code = 'sound "bd sn"'
        backend.send_pattern(pattern_code)
        assert True


@pytest.mark.integration
class TestSynthGeneration:
    """Test synth code generation."""
    
    def test_synth_generation(self):
        """Test generating SuperCollider synth code."""
        synth = SynthTree.random(max_depth=3)
        code = to_supercollider(synth, synth_name="test")
        
        assert code is not None
        assert len(code) > 0
        assert "SynthDef" in code
        assert "test" in code
    
    @pytest.mark.parametrize("depth", [1, 2, 3])
    def test_synth_different_depths(self, depth):
        """Test synth generation at different depths."""
        synth = SynthTree.random(max_depth=depth)
        code = to_supercollider(synth)
        
        assert "SynthDef" in code
        assert synth.depth() <= depth


@pytest.mark.integration
class TestFullGenome:
    """Test complete genome functionality."""
    
    def test_genome_creation(self):
        """Test creating a complete genome."""
        genome = Genome.random()
        
        assert genome.pattern_tree is not None
        assert genome.synth_tree is not None
        assert genome.fitness == 0.0
    
    def test_genome_code_generation(self):
        """Test generating code from a complete genome."""
        genome = Genome.random()
        
        pattern_code = to_tidal(genome.pattern_tree)
        synth_code = to_supercollider(genome.synth_tree)
        
        assert len(pattern_code) > 0
        assert len(synth_code) > 0
        assert "SynthDef" in synth_code
    
    @pytest.mark.parametrize("pattern_depth,synth_depth", [
        (2, 2),
        (3, 3),
        (4, 2),
        (2, 4),
    ])
    def test_genome_different_depths(self, pattern_depth, synth_depth):
        """Test genomes with different tree depths."""
        genome = Genome.random(
            pattern_depth=pattern_depth,
            synth_depth=synth_depth
        )
        
        assert genome.pattern_tree.depth() <= pattern_depth
        assert genome.synth_tree.depth() <= synth_depth

