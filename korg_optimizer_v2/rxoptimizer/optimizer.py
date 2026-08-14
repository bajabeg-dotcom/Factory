"""
MIDI Optimizer - Optimizacija MIDI fajlova na osnovu DNA pravila
"""

import mido
from typing import Dict, List, Any, Optional
import os
import copy
from .dna_analyzer import DNAAnalyzer


class MIDIOptimizer:
    """Optimizuje MIDI fajlove koristeći pravila iz DNA analize"""
    
    def __init__(self, rules: Optional[Dict[str, Any]] = None):
        """
        Inicijalizuj optimizer sa pravilima
        
        Args:
            rules: Pravila optimizacije iz DNA analize
        """
        self.rules = rules or {
            'essential_cc': [1, 7, 10, 11, 64, 91, 93],
            'style_markers': ['INTRO', 'VAR', 'FILL', 'BREAK', 'ENDING'],
            'remove_zero_velocity': True,
            'remove_duplicate_notes': True,
            'clean_redundant_cc': True,
            'merge_tracks': False,
            'normalize_velocities': False
        }
        
        self.stats = {
            'notes_removed': 0,
            'cc_removed': 0,
            'tracks_merged': 0,
            'markers_preserved': 0
        }
    
    def optimize_midi(self, input_path: str, output_path: Optional[str] = None, 
                     detailed: bool = False) -> Dict[str, Any]:
        """
        Optimizuj MIDI fajl
        
        Args:
            input_path: Putanja do ulaznog MIDI fajla
            output_path: Putanja za izlazni fajl (None za inplace)
            detailed: Vrati detaljnu statistiku
            
        Returns:
            Dictionary sa rezultatima optimizacije
        """
        if not os.path.exists(input_path):
            return {'error': f'File not found: {input_path}'}
        
        try:
            mid = mido.MidiFile(input_path)
        except Exception as e:
            return {'error': f'Failed to load MIDI: {str(e)}'}
        
        # Resetuj statistiku
        self.stats = {
            'notes_removed': 0,
            'cc_removed': 0,
            'tracks_merged': 0,
            'markers_preserved': 0,
            'original_size': os.path.getsize(input_path)
        }
        
        original_stats = self._get_midi_stats(mid)
        
        # Primjeni pravila optimizacije
        mid = self._remove_zero_velocity_notes(mid)
        mid = self._remove_duplicate_notes(mid)
        mid = self._clean_redundant_cc(mid)
        mid = self._preserve_style_markers(mid)
        
        if self.rules.get('merge_tracks'):
            mid = self._merge_tracks(mid)
        
        if self.rules.get('normalize_velocities'):
            mid = self._normalize_velocities(mid)
        
        final_stats = self._get_midi_stats(mid)
        
        # Sačuvaj rezultujući fajl
        if output_path:
            mid.save(output_path)
            self.stats['final_size'] = os.path.getsize(output_path)
        else:
            mid.save(input_path)
            self.stats['final_size'] = os.path.getsize(input_path)
        
        # Pripremi rezultate
        results = {
            'success': True,
            'input_file': input_path,
            'output_file': output_path or input_path,
            'original_stats': original_stats,
            'final_stats': final_stats,
            'optimization_stats': self.stats,
            'reduction_percentage': self._calculate_reduction(original_stats, final_stats)
        }
        
        if detailed:
            results['rules_applied'] = self.rules
        
        return results
    
    def _get_midi_stats(self, mid: mido.MidiFile) -> Dict[str, int]:
        """Izračunaj statistiku MIDI fajla"""
        stats = {
            'tracks': len(mid.tracks),
            'notes': 0,
            'cc_events': 0,
            'program_changes': 0,
            'markers': 0
        }
        
        for track in mid.tracks:
            for msg in track:
                if msg.type == 'note_on' and msg.velocity > 0:
                    stats['notes'] += 1
                elif msg.type == 'control_change':
                    stats['cc_events'] += 1
                elif msg.type == 'program_change':
                    stats['program_changes'] += 1
                elif msg.type == 'marker':
                    stats['markers'] += 1
        
        return stats
    
    def _remove_zero_velocity_notes(self, mid: mido.MidiFile) -> mido.MidiFile:
        """Ukloni note sa zero velocity"""
        if not self.rules.get('remove_zero_velocity', True):
            return mid
        
        new_mid = copy.deepcopy(mid)
        
        for track in new_mid.tracks:
            new_track = []
            for msg in track:
                if msg.type == 'note_on' and msg.velocity == 0:
                    self.stats['notes_removed'] += 1
                    continue
                new_track.append(msg)
            
            track[:] = new_track
        
        return new_mid
    
    def _remove_duplicate_notes(self, mid: mido.MidiFile) -> mido.MidiFile:
        """Ukloni duplikate nota na istom kanalu i vremenu"""
        if not self.rules.get('remove_duplicate_notes', True):
            return mid
        
        new_mid = copy.deepcopy(mid)
        
        for track in new_mid.tracks:
            seen_notes = {}
            new_track = []
            
            for msg in track:
                if msg.type == 'note_on' and msg.velocity > 0:
                    key = (msg.channel, msg.note, msg.time)
                    if key in seen_notes:
                        self.stats['notes_removed'] += 1
                        continue
                    seen_notes[key] = True
                
                new_track.append(msg)
            
            track[:] = new_track
        
        return new_mid
    
    def _clean_redundant_cc(self, mid: mido.MidiFile) -> mido.MidiFile:
        """Očisti redundantne control change evente"""
        if not self.rules.get('clean_redundant_cc', True):
            return mid
        
        essential_cc = set(self.rules.get('essential_cc', [1, 7, 10, 11, 64, 91, 93]))
        new_mid = copy.deepcopy(mid)
        
        for track in new_mid.tracks:
            new_track = []
            last_cc_values = {}
            
            for msg in track:
                if msg.type == 'control_change':
                    cc_key = (msg.channel, msg.control)
                    current_value = (msg.channel, msg.control, msg.value)
                    
                    # Uvijek zadrži esencijalne CC
                    if msg.control in essential_cc:
                        new_track.append(msg)
                        last_cc_values[cc_key] = msg.value
                        continue
                    
                    # Preskoči ako je ista vrijednost kao posljednja
                    if cc_key in last_cc_values and last_cc_values[cc_key] == msg.value:
                        self.stats['cc_removed'] += 1
                        continue
                    
                    new_track.append(msg)
                    last_cc_values[cc_key] = msg.value
                else:
                    new_track.append(msg)
            
            track[:] = new_track
        
        return new_mid
    
    def _preserve_style_markers(self, mid: mido.MidiFile) -> mido.MidiFile:
        """Očuvaj style markere i broji ih"""
        style_markers = self.rules.get('style_markers', ['INTRO', 'VAR', 'FILL', 'BREAK', 'ENDING'])
        
        for track in mid.tracks:
            for msg in track:
                if msg.type == 'marker':
                    marker_text = msg.text.upper()
                    if any(marker in marker_text for marker in style_markers):
                        self.stats['markers_preserved'] += 1
        
        return mid
    
    def _merge_tracks(self, mid: mido.MidiFile) -> mido.MidiFile:
        """Spoji sve track-ove u jedan (opcionalno)"""
        if len(mid.tracks) <= 1:
            return mid
        
        new_mid = mido.MidiFile(ticks_per_beat=mid.ticks_per_beat)
        merged_track = mido.MidiTrack()
        
        for track in mid.tracks:
            merged_track.extend(track)
        
        new_mid.tracks.append(merged_track)
        self.stats['tracks_merged'] = len(mid.tracks) - 1
        
        return new_mid
    
    def _normalize_velocities(self, mid: mido.MidiFile) -> mido.MidiFile:
        """Normalizuj velocity vrijednosti (opcionalno)"""
        new_mid = copy.deepcopy(mid)
        
        velocities = []
        for track in new_mid.tracks:
            for msg in track:
                if msg.type == 'note_on' and msg.velocity > 0:
                    velocities.append(msg.velocity)
        
        if not velocities:
            return new_mid
        
        avg_velocity = sum(velocities) / len(velocities)
        scale_factor = 100 / avg_velocity if avg_velocity > 0 else 1
        
        for track in new_mid.tracks:
            for msg in track:
                if msg.type == 'note_on' and msg.velocity > 0:
                    new_velocity = int(msg.velocity * scale_factor)
                    msg.velocity = max(1, min(127, new_velocity))
        
        return new_mid
    
    def _calculate_reduction(self, original: Dict, final: Dict) -> float:
        """Izračunaj procenat redukcije"""
        original_total = original['notes'] + original['cc_events']
        final_total = final['notes'] + final['cc_events']
        
        if original_total == 0:
            return 0.0
        
        return round((1 - final_total / original_total) * 100, 2)


def optimize(input_path: str, output_path: Optional[str] = None, 
             rules: Optional[Dict[str, Any]] = None, detailed: bool = False) -> Dict[str, Any]:
    """
    Glavna funkcija za optimizaciju MIDI fajla
    
    Args:
        input_path: Putanja do ulaznog MIDI fajla
        output_path: Putanja za izlazni fajl (None za inplace)
        rules: Pravila optimizacije
        detailed: Vrati detaljnu statistiku
        
    Returns:
        Dictionary sa rezultatima optimizacije
    """
    optimizer = MIDIOptimizer(rules)
    return optimizer.optimize_midi(input_path, output_path, detailed)


def optimize_batch(input_dir: str, output_dir: str, 
                   rules: Optional[Dict[str, Any]] = None, 
                   detailed: bool = False) -> Dict[str, Any]:
    """
    Optimizuj batch MIDI fajlova
    
    Args:
        input_dir: Direktorijum sa ulaznim fajlovima
        output_dir: Direktorijum za izlazne fajlove
        rules: Pravila optimizacije
        detailed: Vrati detaljnu statistiku
        
    Returns:
        Dictionary sa ukupnom statistikom
    """
    if not os.path.exists(input_dir):
        return {'error': f'Directory not found: {input_dir}'}
    
    os.makedirs(output_dir, exist_ok=True)
    
    results = {
        'total_files': 0,
        'successful': 0,
        'failed': 0,
        'files': [],
        'total_reduction': 0
    }
    
    optimizer = MIDIOptimizer(rules)
    
    for filename in os.listdir(input_dir):
        if filename.lower().endswith('.mid') or filename.lower().endswith('.midi'):
            input_path = os.path.join(input_dir, filename)
            output_path = os.path.join(output_dir, filename)
            
            results['total_files'] += 1
            
            result = optimizer.optimize_midi(input_path, output_path, detailed)
            
            if result.get('success'):
                results['successful'] += 1
                results['files'].append({
                    'filename': filename,
                    'reduction': result.get('reduction_percentage', 0)
                })
                results['total_reduction'] += result.get('reduction_percentage', 0)
            else:
                results['failed'] += 1
                results['files'].append({
                    'filename': filename,
                    'error': result.get('error')
                })
    
    if results['successful'] > 0:
        results['avg_reduction'] = round(results['total_reduction'] / results['successful'], 2)
    
    return results
