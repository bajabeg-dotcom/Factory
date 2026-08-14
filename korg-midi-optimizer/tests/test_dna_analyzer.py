"""
Tests for Korg MIDI Optimizer DNA Analyzer.
"""

import pytest
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from dna_analyzer import DNAAnalyzer


class TestDNAAnalyzer:
    """Test suite for DNAAnalyzer class."""
    
    @pytest.fixture
    def analyzer(self):
        """Create a DNAAnalyzer instance for testing."""
        return DNAAnalyzer()
    
    @pytest.fixture
    def sample_midi_file(self, tmp_path):
        """Create a simple test MIDI file."""
        import mido
        
        mid = mido.MidiFile()
        track = mido.MidiTrack()
        track.append(mido.MetaMessage('track_name', name='Test Track VAR1', time=0))
        track.append(mido.Message('program_change', program=0, channel=0, time=0))
        track.append(mido.Message('note_on', note=60, velocity=64, channel=0, time=0))
        track.append(mido.Message('note_off', note=60, velocity=64, channel=0, time=480))
        track.append(mido.Message('note_on', note=64, velocity=72, channel=0, time=0))
        track.append(mido.Message('note_off', note=64, velocity=72, channel=0, time=480))
        track.append(mido.MetaMessage('end_of_track', time=0))
        mid.tracks.append(track)
        
        midi_path = tmp_path / "test.mid"
        mid.save(str(midi_path))
        return str(midi_path)
    
    def test_analyzer_initialization(self, analyzer):
        """Test that analyzer initializes correctly."""
        assert analyzer is not None
        assert isinstance(analyzer.STYLE_MARKERS, dict)
        assert 'VAR1' in analyzer.STYLE_MARKERS
        assert 'FILL1' in analyzer.STYLE_MARKERS
    
    def test_analyze_file_basic(self, analyzer, sample_midi_file):
        """Test basic file analysis."""
        result = analyzer.analyze_file(sample_midi_file)
        
        assert 'error' not in result
        assert 'filename' in result
        assert 'tracks' in result
        assert 'instruments' in result
        assert 'style_markers' in result
        assert result['total_tracks'] == 1
        assert result['total_notes'] == 2
    
    def test_style_marker_detection(self, analyzer, sample_midi_file):
        """Test that style markers are detected correctly."""
        result = analyzer.analyze_file(sample_midi_file)
        
        assert len(result['style_markers']) > 0
        marker = result['style_markers'][0]
        assert marker['type'] == 'VAR1'
        assert 'Variation 1' in marker['name']
    
    def test_instrument_detection(self, analyzer, sample_midi_file):
        """Test instrument detection."""
        result = analyzer.analyze_file(sample_midi_file)
        
        assert 0 in result['instruments']
        assert result['instruments'][0] == 0  # Program 0
    
    def test_note_statistics(self, analyzer, sample_midi_file):
        """Test note statistics collection."""
        result = analyzer.analyze_file(sample_midi_file)
        
        assert 'note_statistics' in result
        assert 60 in result['note_statistics']
        assert 64 in result['note_statistics']
        assert result['note_statistics'][60] == 1
        assert result['note_statistics'][64] == 1
    
    def test_analyze_nonexistent_file(self, analyzer):
        """Test handling of non-existent files."""
        result = analyzer.analyze_file('/nonexistent/path/file.mid')
        
        assert 'error' in result
        assert 'path' in result
    
    def test_analyze_directory(self, analyzer, tmp_path):
        """Test directory analysis."""
        import mido
        
        # Create two test MIDI files
        for i in range(2):
            mid = mido.MidiFile()
            track = mido.MidiTrack()
            track.append(mido.MetaMessage('track_name', name=f'Track {i}', time=0))
            track.append(mido.Message('note_on', note=60+i, velocity=64, channel=0, time=0))
            track.append(mido.Message('note_off', note=60+i, velocity=64, channel=0, time=480))
            track.append(mido.MetaMessage('end_of_track', time=0))
            mid.tracks.append(track)
            
            midi_path = tmp_path / f"test_{i}.mid"
            mid.save(str(midi_path))
        
        results = analyzer.analyze_directory(str(tmp_path))
        
        assert len(results) == 2
        for result in results:
            assert 'error' not in result
            assert 'filename' in result
    
    def test_build_pattern_database(self, analyzer, sample_midi_file):
        """Test pattern database building."""
        db = analyzer.build_pattern_database([sample_midi_file])
        
        assert 'files_analyzed' in db
        assert db['files_analyzed'] == 1
        assert 'common_instruments' in db
        assert 'style_variations' in db
    
    def test_ticks_per_beat_preservation(self, analyzer, sample_midi_file):
        """Test that ticks per beat is captured."""
        result = analyzer.analyze_file(sample_midi_file)
        
        assert 'ticks_per_beat' in result
        assert result['ticks_per_beat'] > 0
    
    def test_duration_calculation(self, analyzer, sample_midi_file):
        """Test duration calculation."""
        result = analyzer.analyze_file(sample_midi_file)
        
        assert 'duration_ticks' in result
        assert result['duration_ticks'] > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
