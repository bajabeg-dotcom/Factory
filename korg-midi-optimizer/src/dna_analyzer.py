"""
MIDI DNA Analyzer for Korg Styles

Analyzes MIDI files to extract musical DNA patterns including:
- Chord progressions
- Rhythmic patterns
- Instrumentation
- Note density and distribution
- Tempo and timing characteristics
"""

import mido
from collections import defaultdict
from typing import Dict, List, Any, Tuple
import os


class MIDIDNAAnalyzer:
    """Analyzes MIDI files to extract musical DNA patterns."""
    
    def __init__(self):
        self.dna_database = {}
    
    def analyze_file(self, filepath: str) -> Dict[str, Any]:
        """Analyze a single MIDI file and extract DNA features."""
        try:
            mid = mido.MidiFile(filepath)
        except Exception as e:
            return {'error': str(e), 'filepath': filepath}
        
        dna = {
            'filename': os.path.basename(filepath),
            'type': mid.type,
            'ticks_per_beat': mid.ticks_per_beat,
            'num_tracks': len(mid.tracks),
            'tracks': [],
            'global_features': {}
        }
        
        # Extract global tempo and time signature
        tempo = 500000  # Default 120 BPM
        time_sig = (4, 4)
        
        for track in mid.tracks:
            for msg in track:
                if msg.type == 'set_tempo':
                    tempo = msg.tempo
                elif msg.type == 'time_signature':
                    time_sig = (msg.numerator, msg.denominator)
        
        dna['global_features'] = {
            'tempo_bpm': 60000000 / tempo,
            'time_signature': time_sig,
            'duration_ticks': 0  # Will be calculated below
        }
        
        # Calculate total duration
        total_duration = 0
        for track in mid.tracks:
            current_time = 0
            for msg in track:
                current_time += msg.time
            if current_time > total_duration:
                total_duration = current_time
        
        dna['global_features']['duration_ticks'] = total_duration
        
        # Analyze each track
        for i, track in enumerate(mid.tracks):
            track_dna = self._analyze_track(track, i)
            dna['tracks'].append(track_dna)
        
        return dna
    
    def _analyze_track(self, track, track_index: int) -> Dict[str, Any]:
        """Analyze a single MIDI track."""
        track_info = {
            'index': track_index,
            'name': getattr(track, 'name', ''),
            'message_count': len(track),
            'message_types': defaultdict(int),
            'channels': set(),
            'notes': [],
            'instruments': [],
            'rhythm_pattern': []
        }
        
        current_time = 0
        note_events = []
        
        for msg in track:
            current_time += msg.time
            track_info['message_types'][msg.type] += 1
            
            if hasattr(msg, 'channel'):
                track_info['channels'].add(msg.channel)
            
            if msg.type == 'program_change':
                track_info['instruments'].append({
                    'program': msg.program,
                    'channel': msg.channel,
                    'time': current_time
                })
            
            if msg.type in ('note_on', 'note_off'):
                note_events.append({
                    'type': msg.type,
                    'note': msg.note,
                    'velocity': msg.velocity,
                    'time': current_time,
                    'channel': msg.channel
                })
        
        # Convert sets to lists for JSON serialization
        track_info['channels'] = list(track_info['channels'])
        track_info['message_types'] = dict(track_info['message_types'])
        
        # Extract rhythm pattern from notes
        if note_events:
            track_info['rhythm_pattern'] = self._extract_rhythm_pattern(note_events)
            on_notes = [n for n in note_events if n['type'] == 'note_on']
            if on_notes:
                track_info['note_range'] = {
                    'min': min(n['note'] for n in on_notes),
                    'max': max(n['note'] for n in on_notes)
                }
        
        return track_info
    
    def _extract_rhythm_pattern(self, note_events: List[Dict]) -> List[float]:
        """Extract rhythmic pattern from note events."""
        on_events = [e for e in note_events if e['type'] == 'note_on' and e['velocity'] > 0]
        if len(on_events) < 2:
            return []
        
        # Calculate inter-onset intervals
        intervals = []
        for i in range(1, len(on_events)):
            interval = on_events[i]['time'] - on_events[i-1]['time']
            if interval > 0:  # Only positive intervals
                intervals.append(interval)
        
        # Normalize to beat units (simplified)
        if intervals:
            avg_interval = sum(intervals) / len(intervals)
            if avg_interval > 0:  # Avoid division by zero
                normalized = [i / avg_interval for i in intervals[:20]]  # First 20 intervals
                return normalized
        
        return []
    
    def analyze_directory(self, directory: str, pattern: str = '*.mid') -> Dict[str, Any]:
        """Analyze all MIDI files in a directory."""
        import glob
        
        results = {
            'directory': directory,
            'files_analyzed': 0,
            'errors': [],
            'dna_samples': []
        }
        
        midi_files = glob.glob(os.path.join(directory, '**', '*.mid'), recursive=True)
        midi_files += glob.glob(os.path.join(directory, '**', '*.MID'), recursive=True)
        
        for filepath in midi_files:
            dna = self.analyze_file(filepath)
            if 'error' in dna:
                results['errors'].append(dna)
            else:
                results['dna_samples'].append(dna)
                results['files_analyzed'] += 1
        
        return results
    
    def create_style_profile(self, dna_samples: List[Dict]) -> Dict[str, Any]:
        """Create a composite profile from multiple DNA samples."""
        if not dna_samples:
            return {}
        
        profile = {
            'sample_count': len(dna_samples),
            'tempo_distribution': [],
            'common_instruments': defaultdict(int),
            'typical_track_structure': [],
            'rhythmic_characteristics': []
        }
        
        tempos = []
        for sample in dna_samples:
            if 'global_features' in sample:
                tempos.append(sample['global_features'].get('tempo_bpm', 120))
            
            for track in sample.get('tracks', []):
                for inst in track.get('instruments', []):
                    profile['common_instruments'][inst['program']] += 1
        
        if tempos:
            profile['tempo_distribution'] = {
                'min': min(tempos),
                'max': max(tempos),
                'avg': sum(tempos) / len(tempos)
            }
        
        profile['common_instruments'] = dict(profile['common_instruments'])
        
        return profile
