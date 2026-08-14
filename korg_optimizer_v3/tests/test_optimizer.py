"""
Testovi za Korg MIDI Optimizer
"""

import pytest
import os
import sys
import tempfile
import json

# Dodaj parent directory u path za import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rxoptimizer.dna_analyzer import DNAAnalyzer, analyze_dna
from rxoptimizer.optimizer import MIDIOptimizer, optimize, optimize_batch


class TestDNAAnalyzer:
    """Testovi za DNA Analyzer"""
    
    def test_init(self):
        """Test inicijalizacije"""
        analyzer = DNAAnalyzer()
        assert analyzer.essential_cc == [1, 7, 10, 11, 64, 91, 93]
        assert 'INTRO' in analyzer.style_markers
    
    def test_analyze_nonexistent_directory(self):
        """Test analize nepostojećeg direktorijuma"""
        analyzer = DNAAnalyzer()
        result = analyzer.analyze_directory('/nonexistent/path')
        assert 'error' in result
    
    def test_analyze_empty_directory(self):
        """Test analize praznog direktorijuma"""
        with tempfile.TemporaryDirectory() as tmpdir:
            analyzer = DNAAnalyzer()
            result = analyzer.analyze_directory(tmpdir)
            assert result['total_files'] == 0
            assert result['analyzed_files'] == 0
    
    def test_save_and_load_rules(self):
        """Test čuvanja i učitavanja pravila"""
        analyzer = DNAAnalyzer()
        rules = {'test': 'value', 'cc': [1, 2, 3]}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            # Sačuvaj pravila
            assert analyzer.save_rules(rules, temp_path) == True
            
            # Učitaj pravila
            loaded = analyzer.load_rules(temp_path)
            assert loaded is not None
            assert loaded['test'] == 'value'
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestMIDIOptimizer:
    """Testovi za MIDI Optimizer"""
    
    def test_init_default_rules(self):
        """Test inicijalizacije sa default pravilima"""
        optimizer = MIDIOptimizer()
        assert optimizer.rules['remove_zero_velocity'] == True
        assert optimizer.rules['remove_duplicate_notes'] == True
    
    def test_init_custom_rules(self):
        """Test inicijalizacije sa custom pravilima"""
        custom_rules = {'essential_cc': [7, 10], 'custom': True}
        optimizer = MIDIOptimizer(custom_rules)
        assert optimizer.rules['essential_cc'] == [7, 10]
        assert optimizer.rules['custom'] == True
    
    def test_optimize_nonexistent_file(self):
        """Test optimizacije nepostojećeg fajla"""
        result = optimize('/nonexistent/file.mid')
        assert 'error' in result
        assert 'not found' in result['error'].lower()
    
    def test_optimize_with_temp_file(self):
        """Test optimizacije sa privremenim fajlom"""
        import mido
        
        # Kreiraj jednostavan MIDI fajl
        mid = mido.MidiFile()
        track = mido.MidiTrack()
        track.append(mido.Message('note_on', note=60, velocity=100, time=0))
        track.append(mido.Message('note_off', note=60, velocity=0, time=480))
        mid.tracks.append(track)
        
        with tempfile.NamedTemporaryFile(suffix='.mid', delete=False) as f:
            input_path = f.name
            mid.save(input_path)
        
        output_path = input_path.replace('.mid', '_opt.mid')
        
        try:
            result = optimize(input_path, output_path)
            assert result['success'] == True
            assert os.path.exists(output_path)
        finally:
            if os.path.exists(input_path):
                os.unlink(input_path)
            if os.path.exists(output_path):
                os.unlink(output_path)


class TestOptimizeFunction:
    """Testovi za optimize funkciju"""
    
    def test_optimize_returns_dict(self):
        """Test da optimize vraća dictionary"""
        result = optimize('/nonexistent.mid')
        assert isinstance(result, dict)
    
    def test_optimize_error_handling(self):
        """Test handlinga grešaka"""
        result = optimize('')
        assert 'error' in result


class TestOptimizeBatch:
    """Testovi za batch optimizaciju"""
    
    def test_batch_nonexistent_directory(self):
        """Test batch optimizacije nepostojećeg direktorijuma"""
        result = optimize_batch('/nonexistent/dir', '/tmp/output')
        assert 'error' in result
    
    def test_batch_empty_directory(self):
        """Test batch optimizacije praznog direktorijuma"""
        with tempfile.TemporaryDirectory() as tmpdir:
            with tempfile.TemporaryDirectory() as outdir:
                result = optimize_batch(tmpdir, outdir)
                assert result['total_files'] == 0
                assert result['successful'] == 0


class TestIntegration:
    """Integracioni testovi"""
    
    def test_full_workflow(self):
        """Test kompletnog workflow-a"""
        import mido
        
        # Kreiraj test MIDI
        mid = mido.MidiFile()
        track = mido.MidiTrack()
        
        # Dodaj note sa različitim velocity
        track.append(mido.Message('note_on', note=60, velocity=0, time=0))  # Zero velocity
        track.append(mido.Message('note_on', note=62, velocity=100, time=0))  # Normal
        track.append(mido.Message('control_change', control=7, value=80, time=0))  # Essential CC
        track.append(mido.Message('control_change', control=99, value=50, time=0))  # Non-essential
        
        mid.tracks.append(track)
        
        with tempfile.NamedTemporaryFile(suffix='.mid', delete=False) as f:
            input_path = f.name
            mid.save(input_path)
        
        output_path = input_path.replace('.mid', '_opt.mid')
        
        try:
            # Optimizuj
            result = optimize(input_path, output_path, detailed=True)
            
            assert result['success'] == True
            assert 'original_stats' in result
            assert 'final_stats' in result
            assert 'reduction_percentage' in result
            
        finally:
            if os.path.exists(input_path):
                os.unlink(input_path)
            if os.path.exists(output_path):
                os.unlink(output_path)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
