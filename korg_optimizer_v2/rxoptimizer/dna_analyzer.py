"""
DNA Analyzer - Analiza Factory Styles i Gold DNA pattern-a
Izvlači pravila za optimizaciju MIDI fajlova
"""

import mido
from collections import defaultdict
from typing import Dict, List, Tuple, Any
import os


class DNAAnalyzer:
    """Analizira MIDI pattern-e iz Factory Styles i Gold DNA"""
    
    # Esencijalni control change-ovi koje treba očuvati
    ESSENTIAL_CC = {1, 7, 10, 11, 64, 91, 93}
    
    # Style markeri koje treba očuvati
    STYLE_MARKERS = ['INTRO', 'VAR', 'FILL', 'BREAK', 'ENDING']
    
    def __init__(self):
        self.note_patterns = defaultdict(list)
        self.cc_patterns = defaultdict(lambda: defaultdict(list))
        self.velocity_ranges = defaultdict(lambda: {'min': 127, 'max': 0, 'avg': []})
        self.channel_usage = defaultdict(int)
        self.program_changes = defaultdict(set)
        
    def analyze_midi_file(self, filepath: str) -> Dict[str, Any]:
        """Analizira pojedinačni MIDI fajl"""
        try:
            mid = mido.MidiFile(filepath)
        except Exception as e:
            return {'error': str(e)}
        
        analysis = {
            'filename': os.path.basename(filepath),
            'tracks': len(mid.tracks),
            'ticks_per_beat': mid.ticks_per_beat,
            'notes': [],
            'cc_events': [],
            'program_changes': [],
            'tempo_changes': [],
            'markers': [],
            'duration_ticks': 0
        }
        
        current_time = 0
        active_notes = {}
        
        for track_idx, track in enumerate(mid.tracks):
            track_notes = []
            track_cc = []
            track_programs = []
            
            for msg in track:
                current_time += msg.time
                
                if msg.type == 'note_on' and msg.velocity > 0:
                    active_notes[(msg.channel, msg.note)] = current_time
                    track_notes.append({
                        'channel': msg.channel,
                        'note': msg.note,
                        'velocity': msg.velocity,
                        'time': current_time
                    })
                    
                elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                    key = (msg.channel, msg.note)
                    if key in active_notes:
                        start_time = active_notes.pop(key)
                        duration = current_time - start_time
                        analysis['notes'].append({
                            'channel': msg.channel,
                            'note': msg.note,
                            'velocity': track_notes[-1]['velocity'] if track_notes else 0,
                            'start': start_time,
                            'duration': duration
                        })
                
                elif msg.type == 'control_change':
                    track_cc.append({
                        'channel': msg.channel,
                        'control': msg.control,
                        'value': msg.value,
                        'time': current_time
                    })
                
                elif msg.type == 'program_change':
                    track_programs.append({
                        'channel': msg.channel,
                        'program': msg.program,
                        'time': current_time
                    })
                
                elif msg.type == 'set_tempo':
                    analysis['tempo_changes'].append({
                        'tempo': msg.tempo,
                        'time': current_time
                    })
                
                elif msg.type == 'marker':
                    analysis['markers'].append({
                        'text': msg.text,
                        'time': current_time
                    })
            
            analysis['cc_events'].extend(track_cc)
            analysis['program_changes'].extend(track_programs)
        
        analysis['duration_ticks'] = current_time
        return analysis
    
    def analyze_directory(self, directory: str) -> Dict[str, Any]:
        """Analizira sve MIDI fajlove u direktorijumu"""
        results = {
            'total_files': 0,
            'successful': 0,
            'failed': 0,
            'files': [],
            'statistics': {}
        }
        
        if not os.path.exists(directory):
            return results
        
        for filename in os.listdir(directory):
            if filename.lower().endswith('.mid') or filename.lower().endswith('.midi'):
                filepath = os.path.join(directory, filename)
                analysis = self.analyze_midi_file(filepath)
                
                results['total_files'] += 1
                if 'error' not in analysis:
                    results['successful'] += 1
                    results['files'].append(analysis)
                else:
                    results['failed'] += 1
        
        # Izračunaj statistiku
        if results['files']:
            results['statistics'] = self._calculate_statistics(results['files'])
        
        return results
    
    def _calculate_statistics(self, files: List[Dict]) -> Dict[str, Any]:
        """Izračunaj statistiku iz analiziranih fajlova"""
        total_notes = sum(len(f['notes']) for f in files)
        total_cc = sum(len(f['cc_events']) for f in files)
        
        # Analiza channel usage
        channel_notes = defaultdict(int)
        for f in files:
            for note in f['notes']:
                channel_notes[note['channel']] += 1
        
        # Analiza CC usage
        cc_usage = defaultdict(int)
        for f in files:
            for cc in f['cc_events']:
                cc_usage[cc['control']] += 1
        
        # Velocity statistika
        velocities = [n['velocity'] for f in files for n in f['notes']]
        avg_velocity = sum(velocities) / len(velocities) if velocities else 0
        
        return {
            'total_notes': total_notes,
            'total_cc_events': total_cc,
            'avg_notes_per_file': total_notes / len(files),
            'avg_cc_per_file': total_cc / len(files),
            'channel_distribution': dict(channel_notes),
            'cc_usage': dict(cc_usage),
            'avg_velocity': avg_velocity,
            'min_velocity': min(velocities) if velocities else 0,
            'max_velocity': max(velocities) if velocities else 0
        }
    
    def extract_optimization_rules(self, directory: str) -> Dict[str, Any]:
        """Izvlači pravila optimizacije na osnovu analize DNA"""
        analysis = self.analyze_directory(directory)
        
        if not analysis['files']:
            return {'error': 'No valid MIDI files found'}
        
        stats = analysis['statistics']
        
        rules = {
            'essential_cc': list(self.ESSENTIAL_CC),
            'style_markers': self.STYLE_MARKERS,
            'recommended_channels': sorted(stats['channel_distribution'].keys()),
            'common_cc': [cc for cc, count in stats['cc_usage'].items() 
                         if count > stats['total_cc_events'] * 0.1],
            'velocity_threshold': {
                'min_recommended': max(1, stats['min_velocity']),
                'max_recommended': min(127, stats['max_velocity']),
                'average': int(stats['avg_velocity'])
            },
            'max_overlapping_notes': self._calculate_max_overlapping(analysis['files']),
            'typical_track_count': int(stats['avg_notes_per_file'] / 100) if stats['avg_notes_per_file'] > 0 else 4
        }
        
        return rules
    
    def _calculate_max_overlapping(self, files: List[Dict]) -> int:
        """Izračunaj maksimalan broj preklapajućih nota"""
        max_overlap = 0
        
        for f in files:
            events = []
            for note in f['notes']:
                events.append((note['start'], 1))
                events.append((note['start'] + note['duration'], -1))
            
            events.sort()
            current_overlap = 0
            
            for _, delta in events:
                current_overlap += delta
                max_overlap = max(max_overlap, current_overlap)
        
        return max_overlap


def analyze_dna(dna_directory: str) -> Dict[str, Any]:
    """Glavna funkcija za analizu DNA"""
    analyzer = DNAAnalyzer()
    return analyzer.extract_optimization_rules(dna_directory)
