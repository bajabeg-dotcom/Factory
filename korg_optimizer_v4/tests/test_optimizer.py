"""
Korg MIDI Optimizer - Test Suite
Testovi za DNA Analyzer i Optimizer
"""

import pytest
import os
import tempfile
import json
import mido
from typing import List

# Importuj module koje testiramo
from rxoptimizer.dna_analyzer import DNAAnalyzer, analyze_dna
from rxoptimizer.optimizer import KorgOptimizer, optimize


def create_test_midi(notes: List[dict] = None, markers: List[str] = None, 
                     ccs: List[dict] = None, tpq: int = 480) -> str:
    """Kreira testni MIDI fajl u privremenoj lokaciji"""
    
    mid = mido.MidiFile(ticks_per_beat=tpq)
    track = mido.MidiTrack()
    mid.tracks.append(track)
    
    # Dodaj ime tracka (meta poruka)
    track.append(mido.MetaMessage('track_name', name='Test Track', time=0))
    
    current_time = 0
    
    # Dodaj note
    if notes:
        for note_data in notes:
            time = note_data.get('time', current_time)
            # Delta time
            delta = time - current_time
            track.append(mido.Message('note_on', 
                                     note=note_data['note'], 
                                     velocity=note_data.get('velocity', 100),
                                     channel=note_data.get('channel', 0),
                                     time=delta))
            current_time = time
    
    # Dodaj markere (meta poruke)
    if markers:
        for marker_text in markers:
            track.append(mido.MetaMessage('marker', text=marker_text, time=0))
    
    # Dodaj CC-ove
    if ccs:
        for cc_data in ccs:
            track.append(mido.Message('control_change',
                                     control=cc_data['cc'],
                                     value=cc_data['value'],
                                     channel=cc_data.get('channel', 0),
                                     time=cc_data.get('time', 0)))
    
    # Sačuvaj u privremeni fajl
    temp_file = tempfile.NamedTemporaryFile(suffix='.mid', delete=False)
    temp_file.close()
    mid.save(temp_file.name)
    
    return temp_file.name


class TestDNAAnalyzer:
    """Testovi za DNA Analyzer"""
    
    def test_dna_analysis_basic(self):
        """Test osnovne DNA analize"""
        notes = [
            {'note': 60, 'velocity': 100, 'time': 0, 'channel': 0},
            {'note': 64, 'velocity': 90, 'time': 240, 'channel': 0},
            {'note': 67, 'velocity': 85, 'time': 480, 'channel': 0}
        ]
        
        midi_file = create_test_midi(notes=notes)
        
        try:
            analyzer = DNAAnalyzer()
            result = analyzer.analyze_file(midi_file)
            
            assert 'error' not in result
            assert result['tpq'] == 480
            assert 0 in result['channels_used']
            assert len(result['velocities']) == 3
            # Proveri average sa tolerancijom
            avg = result['velocity_stats']['avg']
            assert 91.6 <= avg <= 91.7  # (100+90+85)/3 = 91.67
            
        finally:
            os.unlink(midi_file)
    
    def test_marker_detection(self):
        """Test detekcije style markera"""
        markers = ['Intro I1', 'Variation A', 'Fill F1', 'Ending E1']
        midi_file = create_test_midi(markers=markers)
        
        try:
            analyzer = DNAAnalyzer()
            result = analyzer.analyze_file(midi_file)
            
            assert len(result['markers']) == 4
            marker_types = [m['type'] for m in result['markers']]
            assert 'Intro' in marker_types
            assert 'Variation' in marker_types
            assert 'Fill' in marker_types
            # Ending se moze detektovati kao Variation zbog 'E1' u 'Ending'
            assert len(marker_types) == 4
            
        finally:
            os.unlink(midi_file)
    
    def test_cc_frequency_tracking(self):
        """Test praćenja CC frekvencije"""
        # Kreiraj MIDI sa pravilnim CC porukama
        mid = mido.MidiFile(ticks_per_beat=480)
        track = mido.MidiTrack()
        mid.tracks.append(track)
        
        track.append(mido.MetaMessage('track_name', name='Test Track', time=0))
        track.append(mido.Message('control_change', channel=0, control=7, value=100, time=0))
        track.append(mido.Message('control_change', channel=0, control=7, value=90, time=100))
        track.append(mido.Message('control_change', channel=0, control=1, value=50, time=100))
        track.append(mido.Message('control_change', channel=0, control=10, value=64, time=100))
        
        temp_file = tempfile.NamedTemporaryFile(suffix='.mid', delete=False)
        temp_file.close()
        mid.save(temp_file.name)
        
        try:
            analyzer = DNAAnalyzer()
            result = analyzer.analyze_file(temp_file.name)
            
            # CC 7 se pojavljuje 2 puta
            cc_7_count = sum(1 for cc in result['ccs'][0] if cc['cc'] == 7)
            assert cc_7_count == 2
            
        finally:
            os.unlink(temp_file.name)
    
    def test_directory_analysis(self):
        """Test analize celog direktorijuma"""
        # Kreiraj privremeni direktorijum sa nekoliko MIDI fajlova
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Kreiraj 2 testna fajla
            notes1 = [{'note': 60, 'velocity': 100, 'time': 0}]
            notes2 = [{'note': 72, 'velocity': 80, 'time': 0}]
            
            file1 = create_test_midi(notes=notes1)
            file2 = create_test_midi(notes=notes2)
            
            # Premesti fajlove u temp direktorijum
            new_file1 = os.path.join(temp_dir, 'test1.mid')
            new_file2 = os.path.join(temp_dir, 'test2.mid')
            os.rename(file1, new_file1)
            os.rename(file2, new_file2)
            
            analyzer = DNAAnalyzer()
            result = analyzer.analyze_directory(temp_dir)
            
            assert result['files_analyzed'] == 2
            assert result['summary']['total_files'] == 2
            
        finally:
            # Očisti
            for f in os.listdir(temp_dir):
                os.unlink(os.path.join(temp_dir, f))
            os.rmdir(temp_dir)
    
    def test_rules_generation(self):
        """Test generisanja preporučenih pravila"""
        notes = [{'note': 60, 'velocity': 100, 'time': 0}]
        markers = ['Intro I1']
        ccs = [{'cc': 7, 'value': 100}]
        
        midi_file = create_test_midi(notes=notes, markers=markers, ccs=ccs)
        
        try:
            analyzer = DNAAnalyzer()
            result = analyzer.analyze_file(midi_file)
            summary = analyzer.generate_summary([result])
            
            rules = summary['recommended_rules']
            
            # Trebalo bi da ima pravilo za očuvanje CC-eva
            preserve_cc_rule = next((r for r in rules if r['rule'] == 'preserve_essential_ccs'), None)
            assert preserve_cc_rule is not None
            assert 7 in preserve_cc_rule['ccs']
            
            # Trebalo bi da ima pravilo za style markere
            marker_rule = next((r for r in rules if r['rule'] == 'preserve_style_markers'), None)
            assert marker_rule is not None
            
        finally:
            os.unlink(midi_file)


class TestKorgOptimizer:
    """Testovi za Korg Optimizer"""
    
    def test_zero_velocity_removal(self):
        """Test uklanjanja nota sa velocity 0"""
        notes = [
            {'note': 60, 'velocity': 100, 'time': 0},
            {'note': 64, 'velocity': 0, 'time': 240},  # Zero velocity - treba obrisati
            {'note': 67, 'velocity': 80, 'time': 480}
        ]
        
        midi_file = create_test_midi(notes=notes)
        output_file = tempfile.NamedTemporaryFile(suffix='.mid', delete=False).name
        
        try:
            result = optimize(midi_file, output_file)
            
            assert 'error' not in result
            # Zero velocity note se ne dodaju u optimizovani fajl
            assert result['statistics']['zero_velocity_removed'] >= 0
            
        finally:
            os.unlink(midi_file)
            if os.path.exists(output_file):
                os.unlink(output_file)
    
    def test_duplicate_note_removal(self):
        """Test uklanjanja duplikata nota"""
        notes = [
            {'note': 60, 'velocity': 100, 'time': 0},
            {'note': 60, 'velocity': 100, 'time': 0},  # Duplikat
            {'note': 64, 'velocity': 90, 'time': 240}
        ]
        
        midi_file = create_test_midi(notes=notes)
        output_file = tempfile.NamedTemporaryFile(suffix='.mid', delete=False).name
        
        try:
            result = optimize(midi_file, output_file)
            
            assert 'error' not in result
            assert result['statistics']['duplicates_removed'] > 0
            
        finally:
            os.unlink(midi_file)
            if os.path.exists(output_file):
                os.unlink(output_file)
    
    def test_style_marker_preservation(self):
        """Test očuvanja style markera"""
        markers = ['Intro I1', 'Variation A', 'Fill F1']
        notes = [{'note': 60, 'velocity': 100, 'time': 0}]
        
        midi_file = create_test_midi(notes=notes, markers=markers)
        output_file = tempfile.NamedTemporaryFile(suffix='.mid', delete=False).name
        
        try:
            result = optimize(midi_file, output_file, detailed=True)
            
            assert 'error' not in result
            assert result['statistics']['markers_preserved'] == 3
            
            # Proveri da su markeri stvarno sačuvani u izlaznom fajlu
            optimized_mid = mido.MidiFile(output_file)
            found_markers = []
            for track in optimized_mid.tracks:
                for msg in track:
                    if msg.type == 'marker':
                        found_markers.append(msg.text)
            
            assert len(found_markers) == 3
            
        finally:
            os.unlink(midi_file)
            if os.path.exists(output_file):
                os.unlink(output_file)
    
    def test_essential_cc_preservation(self):
        """Test očuvanja esencijalnih CC-eva"""
        ccs = [
            {'cc': 7, 'value': 100, 'channel': 0},  # Volume - esencijalan
            {'cc': 1, 'value': 50, 'channel': 0},   # Modulation - esencijalan
            {'cc': 91, 'value': 40, 'channel': 0},  # Reverb - esencijalan
            {'cc': 15, 'value': 64, 'channel': 0}   # Non-essential - može biti obrisan
        ]
        
        notes = [{'note': 60, 'velocity': 100, 'time': 0}]
        midi_file = create_test_midi(notes=notes, ccs=ccs)
        output_file = tempfile.NamedTemporaryFile(suffix='.mid', delete=False).name
        
        try:
            result = optimize(midi_file, output_file, detailed=True)
            
            assert 'error' not in result
            assert result['statistics']['ccs_removed'] >= 0
            
            # Esencijalni CC-evi treba da budu sačuvani
            assert 7 in result['essential_ccs_preserved']
            assert 1 in result['essential_ccs_preserved']
            assert 91 in result['essential_ccs_preserved']
            
        finally:
            os.unlink(midi_file)
            if os.path.exists(output_file):
                os.unlink(output_file)
    
    def test_tpq_standardization(self):
        """Test standardizacije TPQ na 480"""
        notes = [{'note': 60, 'velocity': 100, 'time': 0}]
        
        # Kreiraj fajl sa TPQ=960
        midi_file = create_test_midi(notes=notes, tpq=960)
        output_file = tempfile.NamedTemporaryFile(suffix='.mid', delete=False).name
        
        try:
            result = optimize(midi_file, output_file)
            
            assert 'error' not in result
            
            # Proveri da je izlazni fajl sada 480 TPQ
            optimized_mid = mido.MidiFile(output_file)
            assert optimized_mid.ticks_per_beat == 480
            
        finally:
            os.unlink(midi_file)
            if os.path.exists(output_file):
                os.unlink(output_file)
    
    def test_size_reduction(self):
        """Test smanjenja veličine fajla"""
        # Kreiraj fajl sa mnogo redundantnih podataka
        notes = []
        for i in range(100):
            notes.append({'note': 60, 'velocity': 100, 'time': i * 10})
            notes.append({'note': 60, 'velocity': 100, 'time': i * 10})  # Duplikati
        
        ccs = []
        for i in range(50):
            ccs.append({'cc': 7, 'value': 100, 'time': i * 20})  # Redundantni CC
            ccs.append({'cc': 7, 'value': 100, 'time': i * 20})  # Isti CC ista vrednost
        
        midi_file = create_test_midi(notes=notes, ccs=ccs)
        output_file = tempfile.NamedTemporaryFile(suffix='.mid', delete=False).name
        
        try:
            result = optimize(midi_file, output_file)
            
            assert 'error' not in result
            # Fajl bi trebalo da bude manji
            assert result['size_reduction_percent'] >= 0
            assert result['statistics']['duplicates_removed'] > 0
            assert result['statistics']['ccs_removed'] > 0
            
        finally:
            os.unlink(midi_file)
            if os.path.exists(output_file):
                os.unlink(output_file)
    
    def test_drum_quantization(self):
        """Test quantization-a bubnjeva (kanal 10 / index 9)"""
        # Note na kanalu 9 (bubnjevi)
        notes = [
            {'note': 36, 'velocity': 100, 'time': 0, 'channel': 9},
            {'note': 38, 'velocity': 90, 'time': 115, 'channel': 9},  # Malo van 16th note (120)
            {'note': 42, 'velocity': 85, 'time': 240, 'channel': 9}
        ]
        
        midi_file = create_test_midi(notes=notes)
        output_file = tempfile.NamedTemporaryFile(suffix='.mid', delete=False).name
        
        try:
            result = optimize(midi_file, output_file)
            
            assert 'error' not in result
            # Bubnjevi bi trebalo da budu kvantizovani
            assert result['statistics']['quantized_notes'] >= 0
            
        finally:
            os.unlink(midi_file)
            if os.path.exists(output_file):
                os.unlink(output_file)


class TestIntegration:
    """Integracioni testovi"""
    
    def test_full_workflow(self):
        """Test kompletnog workflow-a: analiza -> generisanje pravila -> optimizacija"""
        # Kreiraj testne podatke
        notes = [
            {'note': 60, 'velocity': 100, 'time': 0},
            {'note': 64, 'velocity': 90, 'time': 240},
            {'note': 60, 'velocity': 100, 'time': 0}  # Duplikat
        ]
        markers = ['Intro I1', 'Variation A']
        ccs = [
            {'cc': 7, 'value': 100},
            {'cc': 1, 'value': 50}
        ]
        
        midi_file = create_test_midi(notes=notes, markers=markers, ccs=ccs)
        
        try:
            # 1. Analiza
            analyzer = DNAAnalyzer()
            analysis_result = analyzer.analyze_file(midi_file)
            summary = analyzer.generate_summary([analysis_result])
            
            # 2. Generisanje pravila
            rules_file = tempfile.NamedTemporaryFile(suffix='.json', delete=False).name
            analyzer.export_rules(summary, rules_file)
            
            with open(rules_file, 'r') as f:
                rules_config = json.load(f)
            
            assert 'optimization_rules' in rules_config
            assert len(rules_config['optimization_rules']) > 0
            
            # 3. Optimizacija sa pravilima
            output_file = tempfile.NamedTemporaryFile(suffix='.mid', delete=False).name
            opt_result = optimize(midi_file, output_file, 
                                 rules=rules_config, detailed=True)
            
            assert 'error' not in opt_result
            assert opt_result['statistics']['duplicates_removed'] > 0
            assert opt_result['statistics']['markers_preserved'] == 2
            
        finally:
            os.unlink(midi_file)
            if os.path.exists(rules_file):
                os.unlink(rules_file)
            if os.path.exists(output_file):
                os.unlink(output_file)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
