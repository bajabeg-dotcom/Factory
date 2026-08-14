"""
Test suite for Korg MIDI Optimizer

Tests cover:
1. DNA Analyzer functionality
2. Optimizer rules application
3. File processing pipeline
4. Edge cases and error handling
"""

import pytest
import os
import sys
import tempfile
import shutil
import mido

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.dna_analyzer import MIDIDNAAnalyzer
from src.optimizer import KorgMIDIOptimizer, create_dna_profile_from_samples


class TestMIDIDNAAnalyzer:
    """Test the MIDI DNA Analyzer."""
    
    @pytest.fixture
    def analyzer(self):
        """Create a fresh analyzer instance."""
        return MIDIDNAAnalyzer()
    
    @pytest.fixture
    def sample_midi_file(self, tmp_path):
        """Create a sample MIDI file for testing."""
        mid = mido.MidiFile()
        track = mido.MidiTrack()
        
        # Add basic messages
        track.append(mido.MetaMessage('set_tempo', tempo=500000))
        track.append(mido.MetaMessage('time_signature', numerator=4, denominator=4))
        track.append(mido.Message('program_change', program=0, channel=0))
        track.append(mido.Message('note_on', note=60, velocity=64, channel=0, time=0))
        track.append(mido.Message('note_off', note=60, velocity=64, channel=0, time=480))
        track.append(mido.MetaMessage('end_of_track', time=0))
        
        mid.tracks.append(track)
        
        filepath = tmp_path / "test.mid"
        mid.save(filepath)
        
        return str(filepath)
    
    def test_analyze_file_basic(self, analyzer, sample_midi_file):
        """Test basic file analysis."""
        result = analyzer.analyze_file(sample_midi_file)
        
        assert 'filename' in result
        assert 'type' in result
        assert 'ticks_per_beat' in result
        assert 'num_tracks' in result
        assert 'tracks' in result
        assert 'global_features' in result
        
        assert result['global_features']['tempo_bpm'] == 120.0
        assert result['global_features']['time_signature'] == (4, 4)
    
    def test_analyze_file_error_handling(self, analyzer):
        """Test error handling for invalid files."""
        result = analyzer.analyze_file('/nonexistent/file.mid')
        
        assert 'error' in result
        assert 'filepath' in result
    
    def test_track_analysis(self, analyzer, sample_midi_file):
        """Test track-level analysis."""
        result = analyzer.analyze_file(sample_midi_file)
        
        assert len(result['tracks']) > 0
        track = result['tracks'][0]
        
        assert 'index' in track
        assert 'message_count' in track
        assert 'message_types' in track
        assert 'channels' in track
    
    def test_rhythm_pattern_extraction(self, analyzer):
        """Test rhythm pattern extraction."""
        # Create MIDI with clear rhythm
        mid = mido.MidiFile()
        track = mido.MidiTrack()
        
        track.append(mido.Message('note_on', note=60, velocity=64, time=0))
        track.append(mido.Message('note_off', note=60, velocity=64, time=100))
        track.append(mido.Message('note_on', note=62, velocity=64, time=100))
        track.append(mido.Message('note_off', note=62, velocity=64, time=100))
        track.append(mido.Message('note_on', note=64, velocity=64, time=100))
        track.append(mido.MetaMessage('end_of_track', time=0))
        
        mid.tracks.append(track)
        
        with tempfile.NamedTemporaryFile(suffix='.mid', delete=False) as f:
            mid.save(f.name)
            result = analyzer.analyze_file(f.name)
            os.unlink(f.name)
        
        assert len(result['tracks']) > 0
        # Rhythm pattern should be extracted
        assert 'rhythm_pattern' in result['tracks'][0]


class TestKorgMIDIOptimizer:
    """Test the Korg MIDI Optimizer."""
    
    @pytest.fixture
    def optimizer(self):
        """Create a fresh optimizer instance."""
        return KorgMIDIOptimizer()
    
    @pytest.fixture
    def sample_midi_file(self, tmp_path):
        """Create a sample MIDI file with redundant events."""
        mid = mido.MidiFile()
        track = mido.MidiTrack()
        
        # Add multiple tempo changes (redundant)
        track.append(mido.MetaMessage('set_tempo', tempo=500000))
        track.append(mido.MetaMessage('set_tempo', tempo=600000))
        track.append(mido.MetaMessage('set_tempo', tempo=500000))
        
        # Add redundant control changes
        track.append(mido.Message('control_change', control=7, value=100, channel=0))
        track.append(mido.Message('control_change', control=7, value=100, channel=0))
        track.append(mido.Message('control_change', control=7, value=100, channel=0))
        
        # Add notes
        track.append(mido.Message('note_on', note=60, velocity=64, channel=0, time=0))
        track.append(mido.Message('note_off', note=60, velocity=64, channel=0, time=480))
        track.append(mido.MetaMessage('end_of_track', time=0))
        
        mid.tracks.append(track)
        
        filepath = tmp_path / "test_input.mid"
        mid.save(filepath)
        
        return str(filepath)
    
    def test_optimize_file_basic(self, optimizer, sample_midi_file, tmp_path):
        """Test basic file optimization."""
        output_path = tmp_path / "test_output.mid"
        
        result = optimizer.optimize_file(sample_midi_file, str(output_path))
        
        assert result['success'] is True
        assert os.path.exists(output_path)
        assert 'original_stats' in result
        assert 'optimized_stats' in result
    
    def test_redundant_event_removal(self, optimizer, sample_midi_file, tmp_path):
        """Test removal of redundant events."""
        output_path = tmp_path / "test_output.mid"
        
        result = optimizer.optimize_file(sample_midi_file, str(output_path))
        
        # Load optimized file
        optimized_mid = mido.MidiFile(str(output_path))
        
        # Count tempo changes
        tempo_count = 0
        for track in optimized_mid.tracks:
            for msg in track:
                if msg.type == 'set_tempo':
                    tempo_count += 1
        
        # Should have only one tempo change after optimization
        assert tempo_count == 1
    
    def test_control_change_cleanup(self, optimizer, sample_midi_file, tmp_path):
        """Test control change cleanup."""
        output_path = tmp_path / "test_output.mid"
        
        result = optimizer.optimize_file(sample_midi_file, str(output_path))
        
        # Load optimized file
        optimized_mid = mido.MidiFile(str(output_path))
        
        # Count control changes
        cc_count = 0
        for track in optimized_mid.tracks:
            for msg in track:
                if msg.type == 'control_change':
                    cc_count += 1
        
        # Should have fewer CCs after cleanup (removed duplicates)
        assert cc_count < 3
    
    def test_optimize_directory(self, optimizer, tmp_path):
        """Test directory optimization."""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        
        # Create multiple MIDI files
        for i in range(3):
            mid = mido.MidiFile()
            track = mido.MidiTrack()
            track.append(mido.Message('note_on', note=60, velocity=64, time=0))
            track.append(mido.MetaMessage('end_of_track', time=0))
            mid.tracks.append(track)
            mid.save(input_dir / f"test_{i}.mid")
        
        result = optimizer.optimize_directory(str(input_dir), str(output_dir))
        
        assert result['files_processed'] == 3
        assert result['successful'] == 3
        assert result['failed'] == 0
        assert os.path.exists(output_dir)


class TestIntegration:
    """Integration tests for the complete pipeline."""
    
    @pytest.fixture
    def test_environment(self, tmp_path):
        """Set up a test environment with sample data."""
        base_dir = tmp_path / "test_env"
        base_dir.mkdir()
        
        gold_dir = base_dir / "gold_dna"
        gold_dir.mkdir()
        
        factory_dir = base_dir / "factory_styles"
        factory_dir.mkdir()
        
        output_dir = base_dir / "output"
        output_dir.mkdir()
        
        # Create sample Gold DNA file
        mid = mido.MidiFile()
        track = mido.MidiTrack()
        track.append(mido.MetaMessage('set_tempo', tempo=500000))
        track.append(mido.Message('note_on', note=60, velocity=80, channel=0, time=0))
        track.append(mido.MetaMessage('end_of_track', time=480))
        mid.tracks.append(track)
        mid.save(gold_dir / "sample_gold.mid")
        
        # Create sample Factory Style file
        mid2 = mido.MidiFile(ticks_per_beat=192)
        track2 = mido.MidiTrack()
        track2.append(mido.MetaMessage('set_tempo', tempo=500000))
        track2.append(mido.Message('note_on', note=36, velocity=100, channel=9, time=0))
        track2.append(mido.MetaMessage('end_of_track', time=192))
        mid2.tracks.append(track2)
        mid2.save(factory_dir / "sample_factory.mid")
        
        return {
            'base_dir': str(base_dir),
            'gold_dir': str(gold_dir),
            'factory_dir': str(factory_dir),
            'output_dir': str(output_dir)
        }
    
    def test_dna_profile_creation(self, test_environment):
        """Test DNA profile creation from samples."""
        profile = create_dna_profile_from_samples(
            test_environment['gold_dir'],
            test_environment['factory_dir']
        )
        
        assert 'gold_dna_profile' in profile
        assert 'factory_style_profile' in profile
        assert 'combined_rules' in profile
    
    def test_full_optimization_pipeline(self, test_environment):
        """Test complete optimization pipeline."""
        from src.optimizer import KorgMIDIOptimizer
        
        # Create optimizer with DNA profile
        profile = create_dna_profile_from_samples(
            test_environment['gold_dir'],
            test_environment['factory_dir']
        )
        
        optimizer = KorgMIDIOptimizer(dna_profile=profile)
        
        # Optimize the Gold DNA sample
        gold_file = os.path.join(test_environment['gold_dir'], "sample_gold.mid")
        output_file = os.path.join(test_environment['output_dir'], "optimized.mid")
        
        result = optimizer.optimize_file(gold_file, output_file)
        
        assert result['success'] is True
        assert os.path.exists(output_file)


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_empty_midi_file(self):
        """Test handling of empty MIDI file."""
        analyzer = MIDIDNAAnalyzer()
        
        mid = mido.MidiFile()
        
        with tempfile.NamedTemporaryFile(suffix='.mid', delete=False) as f:
            mid.save(f.name)
            result = analyzer.analyze_file(f.name)
            os.unlink(f.name)
        
        assert result is not None
        assert 'error' not in result or result.get('num_tracks') == 0
    
    def test_corrupted_midi_file(self):
        """Test handling of corrupted MIDI file."""
        optimizer = KorgMIDIOptimizer()
        
        with tempfile.NamedTemporaryFile(suffix='.mid', delete=False) as f:
            f.write(b"This is not a valid MIDI file")
            temp_path = f.name
        
        try:
            with tempfile.NamedTemporaryFile(suffix='.mid', delete=False) as out:
                output_path = out.name
            
            result = optimizer.optimize_file(temp_path, output_path)
            
            assert result['success'] is False
            assert 'error' in result
        finally:
            os.unlink(temp_path)
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    def test_large_midi_file(self):
        """Test handling of large MIDI file."""
        analyzer = MIDIDNAAnalyzer()
        
        mid = mido.MidiFile()
        track = mido.MidiTrack()
        
        # Add many notes
        for i in range(1000):
            track.append(mido.Message('note_on', note=60 + (i % 12), velocity=64, time=0))
            track.append(mido.Message('note_off', note=60 + (i % 12), velocity=64, time=10))
        
        track.append(mido.MetaMessage('end_of_track', time=0))
        mid.tracks.append(track)
        
        with tempfile.NamedTemporaryFile(suffix='.mid', delete=False) as f:
            mid.save(f.name)
            result = analyzer.analyze_file(f.name)
            os.unlink(f.name)
        
        assert result is not None
        assert 'tracks' in result
        assert len(result['tracks']) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
