"""
Testovi za Korg MIDI Optimizer
"""

import pytest
import os
import sys
import tempfile
import mido

# Dodaj parent directory za import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rxoptimizer.dna_analyzer import DNAAnalyzer, analyze_dna
from rxoptimizer.optimizer import MIDIOptimizer, optimize, optimize_batch


def create_test_midi(filename: str, notes: list = None, cc_events: list = None, 
                     markers: list = None, zero_velocity: bool = False) -> str:
    """Kreiraj testni MIDI fajl"""
    mid = mido.MidiFile()
    track = mido.MidiTrack()
    mid.tracks.append(track)
    
    # Dodaj note
    if notes:
        for note_info in notes:
            channel = note_info.get('channel', 0)
            note = note_info.get('note', 60)
            velocity = note_info.get('velocity', 100)
            time = note_info.get('time', 0)
            
            track.append(mido.Message('note_on', channel=channel, note=note, 
                                     velocity=velocity, time=time))
            track.append(mido.Message('note_off', channel=channel, note=note, 
                                     velocity=0, time=100))
    
    # Dodaj zero velocity note ako je specificirano
    if zero_velocity:
        track.append(mido.Message('note_on', channel=0, note=60, velocity=0, time=0))
    
    # Dodaj CC evente
    if cc_events:
        for cc_info in cc_events:
            channel = cc_info.get('channel', 0)
            control = cc_info.get('control', 7)
            value = cc_info.get('value', 100)
            time = cc_info.get('time', 0)
            
            track.append(mido.Message('control_change', channel=channel, 
                                     control=control, value=value, time=time))
    
    # Dodaj markere
    if markers:
        for marker_text in markers:
            track.append(mido.MetaMessage('marker', text=marker_text, time=0))
    
    # Sačuvaj fajl
    mid.save(filename)
    return filename


class TestDNAAnalyzer:
    """Testovi za DNA Analyzer"""
    
    def test_analyze_midi_file(self, tmp_path):
        """Test analize pojedinačnog MIDI fajla"""
        test_file = str(tmp_path / "test.mid")
        create_test_midi(test_file, 
                        notes=[{'note': 60, 'velocity': 100}, {'note': 64, 'velocity': 80}],
                        cc_events=[{'control': 7, 'value': 100}])
        
        analyzer = DNAAnalyzer()
        result = analyzer.analyze_midi_file(test_file)
        
        assert 'error' not in result
        assert result['filename'] == "test.mid"
        assert len(result['notes']) == 2
        assert len(result['cc_events']) == 1
    
    def test_analyze_nonexistent_file(self):
        """Test analize nepostojećeg fajla"""
        analyzer = DNAAnalyzer()
        result = analyzer.analyze_midi_file("nonexistent.mid")
        
        assert 'error' in result
    
    def test_extract_optimization_rules(self, tmp_path):
        """Test izvlačenja pravila optimizacije"""
        # Kreiraj više testnih fajlova
        for i in range(3):
            test_file = str(tmp_path / f"test{i}.mid")
            create_test_midi(test_file,
                           notes=[{'note': 60 + i, 'velocity': 80 + i * 10}],
                           cc_events=[{'control': 7, 'value': 100}, {'control': 1, 'value': 50}])
        
        rules = analyze_dna(str(tmp_path))
        
        assert 'error' not in rules
        assert 'essential_cc' in rules
        assert 'style_markers' in rules
        assert 'velocity_threshold' in rules


class TestMIDIOptimizer:
    """Testovi za MIDI Optimizer"""
    
    def test_remove_zero_velocity_notes(self, tmp_path):
        """Test uklanjanja nota sa zero velocity"""
        input_file = str(tmp_path / "input.mid")
        output_file = str(tmp_path / "output.mid")
        
        create_test_midi(input_file,
                        notes=[{'note': 60, 'velocity': 100}],
                        zero_velocity=True)
        
        result = optimize(input_file, output_file)
        
        assert result['success']
        assert result['optimization_stats']['notes_removed'] >= 1
    
    def test_remove_duplicate_notes(self, tmp_path):
        """Test uklanjanja duplih nota"""
        input_file = str(tmp_path / "input.mid")
        output_file = str(tmp_path / "output.mid")
        
        # Kreiraj fajl sa duplim notama
        mid = mido.MidiFile()
        track = mido.MidiTrack()
        mid.tracks.append(track)
        
        # Dodaj istu notu dva puta na isto vrijeme
        track.append(mido.Message('note_on', channel=0, note=60, velocity=100, time=0))
        track.append(mido.Message('note_on', channel=0, note=60, velocity=100, time=0))
        track.append(mido.Message('note_off', channel=0, note=60, velocity=0, time=100))
        
        mid.save(input_file)
        
        result = optimize(input_file, output_file)
        
        assert result['success']
    
    def test_preserve_essential_cc(self, tmp_path):
        """Test očuvanja esencijalnih CC-eva"""
        input_file = str(tmp_path / "input.mid")
        output_file = str(tmp_path / "output.mid")
        
        # Kreiraj fajl sa esencijalnim i ne-esencijalnim CC-evima
        mid = mido.MidiFile()
        track = mido.MidiTrack()
        mid.tracks.append(track)
        
        # Esencijalni CC (7 - volume)
        track.append(mido.Message('control_change', channel=0, control=7, value=100, time=0))
        # Ne-esencijalni CC (ponovljen)
        track.append(mido.Message('control_change', channel=0, control=92, value=50, time=0))
        track.append(mido.Message('control_change', channel=0, control=92, value=50, time=10))
        
        mid.save(input_file)
        
        result = optimize(input_file, output_file)
        
        assert result['success']
        assert result['optimization_stats']['cc_removed'] >= 1
    
    def test_preserve_style_markers(self, tmp_path):
        """Test očuvanja style markera"""
        input_file = str(tmp_path / "input.mid")
        output_file = str(tmp_path / "output.mid")
        
        create_test_midi(input_file,
                        markers=['INTRO', 'VAR1', 'FILL A', 'BREAK', 'ENDING'])
        
        result = optimize(input_file, output_file, detailed=True)
        
        assert result['success']
        assert result['optimization_stats']['markers_preserved'] >= 1
    
    def test_optimize_nonexistent_file(self):
        """Test optimizacije nepostojećeg fajla"""
        result = optimize("nonexistent.mid", "output.mid")
        
        assert 'error' in result
    
    def test_optimize_with_custom_rules(self, tmp_path):
        """Test optimizacije sa custom pravilima"""
        input_file = str(tmp_path / "input.mid")
        output_file = str(tmp_path / "output.mid")
        
        create_test_midi(input_file,
                        notes=[{'note': 60, 'velocity': 100}],
                        cc_events=[{'control': 7, 'value': 100}])
        
        custom_rules = {
            'essential_cc': [7, 10],
            'remove_zero_velocity': True,
            'remove_duplicate_notes': True,
            'clean_redundant_cc': False  # Isključi čišćenje CC
        }
        
        result = optimize(input_file, output_file, rules=custom_rules, detailed=True)
        
        assert result['success']
        assert 'rules_applied' in result
        assert result['rules_applied']['clean_redundant_cc'] == False


class TestBatchOptimization:
    """Testovi za batch optimizaciju"""
    
    def test_batch_optimize(self, tmp_path):
        """Test batch optimizacije direktorijuma"""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        
        # Kreiraj više testnih fajlova
        for i in range(3):
            test_file = input_dir / f"test{i}.mid"
            create_test_midi(str(test_file),
                           notes=[{'note': 60 + i, 'velocity': 80 + i * 10}])
        
        result = optimize_batch(str(input_dir), str(output_dir))
        
        assert result['total_files'] == 3
        assert result['successful'] == 3
        assert result['failed'] == 0
        assert 'avg_reduction' in result
    
    def test_batch_optimize_empty_directory(self, tmp_path):
        """Test batch optimizacije praznog direktorijuma"""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        
        result = optimize_batch(str(input_dir), str(output_dir))
        
        assert result['total_files'] == 0
        assert result['successful'] == 0
    
    def test_batch_optimize_nonexistent_directory(self):
        """Test batch optimizacije nepostojećeg direktorijuma"""
        result = optimize_batch("nonexistent_dir", "output_dir")
        
        assert 'error' in result


class TestEdgeCases:
    """Testovi za rubne slučajeve"""
    
    def test_empty_midi_file(self, tmp_path):
        """Test optimizacije praznog MIDI fajla"""
        input_file = str(tmp_path / "empty.mid")
        output_file = str(tmp_path / "output.mid")
        
        mid = mido.MidiFile()
        track = mido.MidiTrack()
        mid.tracks.append(track)
        mid.save(input_file)
        
        result = optimize(input_file, output_file)
        
        assert result['success']
        assert result['reduction_percentage'] == 0.0
    
    def test_midi_with_only_program_changes(self, tmp_path):
        """Test MIDI fajla samo sa program change eventima"""
        input_file = str(tmp_path / "prog.mid")
        output_file = str(tmp_path / "output.mid")
        
        mid = mido.MidiFile()
        track = mido.MidiTrack()
        mid.tracks.append(track)
        
        track.append(mido.Message('program_change', channel=0, program=1, time=0))
        track.append(mido.Message('program_change', channel=1, program=2, time=100))
        
        mid.save(input_file)
        
        result = optimize(input_file, output_file)
        
        assert result['success']
    
    def test_large_velocity_values(self, tmp_path):
        """Test sa ekstremnim velocity vrijednostima"""
        input_file = str(tmp_path / "large.mid")
        output_file = str(tmp_path / "output.mid")
        
        mid = mido.MidiFile()
        track = mido.MidiTrack()
        mid.tracks.append(track)
        
        # Dodaj note sa max i min velocity
        track.append(mido.Message('note_on', channel=0, note=60, velocity=127, time=0))
        track.append(mido.Message('note_on', channel=0, note=64, velocity=1, time=100))
        track.append(mido.Message('note_off', channel=0, note=60, velocity=0, time=100))
        track.append(mido.Message('note_off', channel=0, note=64, velocity=0, time=100))
        
        mid.save(input_file)
        
        result = optimize(input_file, output_file)
        
        assert result['success']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
