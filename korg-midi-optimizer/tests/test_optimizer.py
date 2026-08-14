"""
Tests for Korg MIDI Optimizer.
"""

import pytest
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

# Import with absolute paths since we added src to path
from dna_analyzer import DNAAnalyzer
from optimizer import MIDIOptimizer


class TestMIDIOptimizer:
    """Test suite for MIDIOptimizer class."""
    
    @pytest.fixture
    def analyzer(self):
        """Create a DNAAnalyzer instance for testing."""
        return DNAAnalyzer()
    
    @pytest.fixture
    def optimizer(self, analyzer):
        """Create a MIDIOptimizer instance for testing."""
        return MIDIOptimizer(dna_analyzer=analyzer)
    
    @pytest.fixture
    def sample_midi_file(self, tmp_path):
        """Create a test MIDI file with various events."""
        import mido
        
        mid = mido.MidiFile()
        track1 = mido.MidiTrack()
        track1.append(mido.MetaMessage('track_name', name='Test VAR1', time=0))
        track1.append(mido.Message('program_change', program=5, channel=0, time=0))
        track1.append(mido.Message('note_on', note=60, velocity=64, channel=0, time=0))
        track1.append(mido.Message('note_off', note=60, velocity=64, channel=0, time=0))
        # Add duplicate note at same tick (should be removed)
        track1.append(mido.Message('note_on', note=60, velocity=64, channel=0, time=0))
        track1.append(mido.Message('note_off', note=60, velocity=64, channel=0, time=0))
        # Add another note
        track1.append(mido.Message('note_on', note=64, velocity=72, channel=0, time=480))
        track1.append(mido.Message('note_off', note=64, velocity=72, channel=0, time=480))
        # Add control changes - duplicate essential CC
        track1.append(mido.Message('control_change', control=7, value=100, channel=0, time=0))
        track1.append(mido.Message('control_change', control=7, value=100, channel=0, time=0))  # Duplicate
        # Non-essential CCs with same value
        track1.append(mido.Message('control_change', control=99, value=50, channel=0, time=0))
        track1.append(mido.Message('control_change', control=99, value=50, channel=0, time=0))  # Duplicate
        track1.append(mido.MetaMessage('end_of_track', time=0))
        mid.tracks.append(track1)
        
        midi_path = tmp_path / "test.mid"
        mid.save(str(midi_path))
        return str(midi_path)
    
    def test_optimizer_initialization(self, optimizer):
        """Test that optimizer initializes correctly."""
        assert optimizer is not None
        assert isinstance(optimizer.rules, dict)
        assert optimizer.rules['remove_duplicate_notes'] == True
        assert optimizer.rules['preserve_style_markers'] == True
    
    def test_set_rule(self, optimizer):
        """Test rule modification."""
        optimizer.set_rule('remove_duplicate_notes', False)
        assert optimizer.rules['remove_duplicate_notes'] == False
        
        with pytest.raises(ValueError):
            optimizer.set_rule('nonexistent_rule', True)
    
    def test_optimize_file_basic(self, optimizer, sample_midi_file, tmp_path):
        """Test basic file optimization."""
        output_path = str(tmp_path / "optimized.mid")
        result = optimizer.optimize_file(sample_midi_file, output_path)
        
        assert 'error' not in result
        assert result['saved'] == True
        assert os.path.exists(output_path)
        assert 'original_events' in result
        assert 'optimized_events' in result
    
    def test_duplicate_note_removal(self, optimizer, sample_midi_file, tmp_path):
        """Test that duplicate notes are removed."""
        output_path = str(tmp_path / "optimized.mid")
        result = optimizer.optimize_file(sample_midi_file, output_path)
        
        # Should have removed at least one duplicate note and one duplicate CC
        assert result['optimized_events'] < result['original_events']
        stats = optimizer.get_stats()
        assert stats['notes_removed'] > 0 or stats['events_removed'] > 0
    
    def test_control_change_cleaning(self, optimizer, sample_midi_file):
        """Test control change cleaning."""
        optimizer.set_rule('clean_control_changes', True)
        result = optimizer.optimize_file(sample_midi_file)
        
        # Non-essential duplicate CCs should be removed
        assert result['optimized_events'] < result['original_events']
    
    def test_preserve_essential_control_changes(self, optimizer, sample_midi_file, tmp_path):
        """Test that essential control changes are preserved."""
        output_path = str(tmp_path / "optimized.mid")
        result = optimizer.optimize_file(sample_midi_file, output_path)
        
        # Load optimized file and check for volume CC (control 7)
        import mido
        optimized_mid = mido.MidiFile(output_path)
        found_volume_cc = False
        
        for track in optimized_mid.tracks:
            for msg in track:
                if msg.type == 'control_change' and msg.control == 7:
                    found_volume_cc = True
                    break
        
        assert found_volume_cc, "Essential volume CC should be preserved"
    
    def test_style_marker_preservation(self, optimizer, sample_midi_file, tmp_path):
        """Test that style markers are preserved."""
        output_path = str(tmp_path / "optimized.mid")
        result = optimizer.optimize_file(sample_midi_file, output_path)
        
        import mido
        optimized_mid = mido.MidiFile(output_path)
        found_marker = False
        
        for track in optimized_mid.tracks:
            for msg in track:
                if msg.type == 'track_name' and 'VAR1' in msg.name:
                    found_marker = True
                    break
        
        assert found_marker, "Style marker should be preserved"
    
    def test_optimize_nonexistent_file(self, optimizer):
        """Test handling of non-existent files."""
        result = optimizer.optimize_file('/nonexistent/path/file.mid')
        
        assert 'error' in result
        stats = optimizer.get_stats()
        assert stats['errors'] == 1
    
    def test_optimize_directory(self, optimizer, tmp_path):
        """Test directory optimization."""
        import mido
        
        # Create test MIDI files
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        
        for i in range(2):
            mid = mido.MidiFile()
            track = mido.MidiTrack()
            track.append(mido.Message('note_on', note=60+i, velocity=64, channel=0, time=0))
            track.append(mido.Message('note_off', note=60+i, velocity=64, channel=0, time=480))
            track.append(mido.MetaMessage('end_of_track', time=0))
            mid.tracks.append(track)
            
            midi_path = input_dir / f"test_{i}.mid"
            mid.save(str(midi_path))
        
        results = optimizer.optimize_directory(str(input_dir), str(output_dir))
        
        assert len(results) == 2
        for result in results:
            assert 'error' not in result
            assert result['saved'] == True
        
        # Verify output files exist
        for i in range(2):
            output_path = output_dir / f"test_{i}.mid"
            assert output_path.exists()
    
    def test_stats_tracking(self, optimizer, sample_midi_file, tmp_path):
        """Test statistics tracking."""
        optimizer.reset_stats()
        output_path = str(tmp_path / "optimized.mid")
        
        # Process multiple files
        optimizer.optimize_file(sample_midi_file, output_path)
        optimizer.optimize_file(sample_midi_file, output_path)
        
        stats = optimizer.get_stats()
        assert stats['files_processed'] == 2
    
    def test_reset_stats(self, optimizer, sample_midi_file, tmp_path):
        """Test stats reset."""
        output_path = str(tmp_path / "optimized.mid")
        optimizer.optimize_file(sample_midi_file, output_path)
        
        stats_before = optimizer.get_stats()
        assert stats_before['files_processed'] > 0
        
        optimizer.reset_stats()
        stats_after = optimizer.get_stats()
        assert stats_after['files_processed'] == 0
        assert stats_after['events_removed'] == 0
    
    def test_zero_velocity_note_handling(self, tmp_path):
        """Test handling of zero-velocity notes."""
        import mido
        
        # Create MIDI with zero-velocity note_on (should be treated as note_off)
        mid = mido.MidiFile()
        track = mido.MidiTrack()
        track.append(mido.Message('note_on', note=60, velocity=0, channel=0, time=0))
        track.append(mido.MetaMessage('end_of_track', time=0))
        mid.tracks.append(track)
        
        midi_path = tmp_path / "zero_vel.mid"
        mid.save(str(midi_path))
        
        analyzer = DNAAnalyzer()
        optimizer = MIDIOptimizer(dna_analyzer=analyzer)
        optimizer.set_rule('remove_zero_velocity_notes', True)
        
        output_path = str(tmp_path / "optimized.mid")
        result = optimizer.optimize_file(str(midi_path), output_path)
        
        assert 'error' not in result
    
    def test_program_change_preservation(self, optimizer, sample_midi_file, tmp_path):
        """Test that program changes are preserved."""
        output_path = str(tmp_path / "optimized.mid")
        result = optimizer.optimize_file(sample_midi_file, output_path)
        
        import mido
        optimized_mid = mido.MidiFile(output_path)
        found_program_change = False
        
        for track in optimized_mid.tracks:
            for msg in track:
                if msg.type == 'program_change':
                    found_program_change = True
                    assert msg.program == 5  # Original program
                    break
        
        assert found_program_change, "Program change should be preserved"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
