"""
Korg MIDI Optimizer - Module for analyzing DNA patterns from Factory Styles and Gold styles.
Extracts musical patterns, instrument usage, rhythm structures, and style markers.
"""

import mido
import os
from collections import defaultdict
from typing import Dict, List, Any, Tuple
from pathlib import Path


class DNAAnalyzer:
    """Analyzes MIDI files to extract DNA patterns for Korg style optimization."""
    
    # Korg style marker types
    STYLE_MARKERS = {
        'INTRO1': 'Intro 1',
        'INTRO2': 'Intro 2', 
        'INTRO3': 'Intro 3',
        'VAR1': 'Variation 1',
        'VAR2': 'Variation 2',
        'VAR3': 'Variation 3',
        'VAR4': 'Variation 4',
        'FILL1': 'Fill 1',
        'FILL2': 'Fill 2',
        'FILL3': 'Fill 3',
        'FILL4': 'Fill 4',
        'BREAK': 'Break',
        'END1': 'Ending 1',
        'END2': 'Ending 2',
        'ENDING1': 'Ending 1',
        'ENDING2': 'Ending 2',
    }
    
    def __init__(self):
        self.dna_database = {}
        
    def analyze_file(self, midi_path: str) -> Dict[str, Any]:
        """Analyze a single MIDI file and extract DNA information."""
        try:
            mid = mido.MidiFile(midi_path)
        except Exception as e:
            return {'error': str(e), 'path': midi_path}
        
        dna = {
            'filename': os.path.basename(midi_path),
            'path': midi_path,
            'ticks_per_beat': mid.ticks_per_beat,
            'duration_ticks': 0,
            'tracks': [],
            'instruments': {},
            'rhythm_patterns': [],
            'style_markers': [],
            'note_statistics': defaultdict(int),
            'channel_usage': defaultdict(lambda: {'notes': 0, 'control_changes': 0}),
        }
        
        total_ticks = 0
        for track_idx, track in enumerate(mid.tracks):
            track_info = {
                'index': track_idx,
                'name': '',
                'events': [],
                'notes': [],
                'instrument': None,
                'channel': None,
            }
            
            tick_position = 0
            for msg in track:
                tick_position += msg.time
                
                if msg.type == 'set_instrument':
                    track_info['instrument'] = msg.instrument
                    dna['instruments'][track_idx] = msg.instrument
                    
                elif msg.type == 'track_name':
                    track_info['name'] = msg.name
                    # Check for style markers in track name
                    for marker_key, marker_name in self.STYLE_MARKERS.items():
                        if marker_key in msg.name.upper():
                            dna['style_markers'].append({
                                'type': marker_key,
                                'name': marker_name,
                                'track': track_idx,
                                'tick': tick_position
                            })
                            
                elif msg.type == 'note_on' and msg.velocity > 0:
                    track_info['notes'].append({
                        'note': msg.note,
                        'velocity': msg.velocity,
                        'tick': tick_position,
                        'channel': msg.channel if hasattr(msg, 'channel') else None
                    })
                    dna['note_statistics'][msg.note] += 1
                    if hasattr(msg, 'channel'):
                        dna['channel_usage'][msg.channel]['notes'] += 1
                        
                elif msg.type == 'control_change':
                    if hasattr(msg, 'channel'):
                        dna['channel_usage'][msg.channel]['control_changes'] += 1
                    track_info['events'].append({
                        'type': msg.type,
                        'control': msg.control,
                        'value': msg.value,
                        'tick': tick_position,
                        'channel': msg.channel if hasattr(msg, 'channel') else None
                    })
                    
                elif msg.type == 'program_change':
                    track_info['instrument'] = msg.program
                    dna['instruments'][track_idx] = msg.program
                    
                total_ticks = max(total_ticks, tick_position)
                
            track_info['event_count'] = len(track_info['events'])
            track_info['note_count'] = len(track_info['notes'])
            dna['tracks'].append(track_info)
            
        dna['duration_ticks'] = total_ticks
        dna['total_tracks'] = len(mid.tracks)
        dna['total_notes'] = sum(dna['note_statistics'].values())
        
        # Convert defaultdicts to regular dicts for JSON serialization
        dna['note_statistics'] = dict(dna['note_statistics'])
        dna['channel_usage'] = dict(dna['channel_usage'])
        
        return dna
    
    def analyze_directory(self, directory: str, pattern: str = "*.mid") -> List[Dict[str, Any]]:
        """Analyze all MIDI files in a directory."""
        results = []
        path = Path(directory)
        
        for midi_file in path.rglob(pattern):
            dna = self.analyze_file(str(midi_file))
            results.append(dna)
            
        return results
    
    def build_pattern_database(self, midi_files: List[str]) -> Dict[str, Any]:
        """Build a comprehensive DNA pattern database from multiple MIDI files."""
        db = {
            'common_instruments': defaultdict(int),
            'common_note_patterns': defaultdict(int),
            'typical_channel_usage': defaultdict(lambda: defaultdict(int)),
            'style_variations': defaultdict(list),
            'files_analyzed': 0,
            'errors': []
        }
        
        for file_path in midi_files:
            dna = self.analyze_file(file_path)
            if 'error' in dna:
                db['errors'].append(dna)
                continue
                
            db['files_analyzed'] += 1
            
            # Track instrument usage
            for track_idx, instrument in dna['instruments'].items():
                db['common_instruments'][instrument] += 1
                
            # Track note patterns (simplified: just note sequences per channel)
            for track in dna['tracks']:
                if track['notes']:
                    notes = tuple(n['note'] for n in track['notes'][:10])  # First 10 notes
                    db['common_note_patterns'][notes] += 1
                    
            # Track channel usage patterns
            for channel, usage in dna['channel_usage'].items():
                db['typical_channel_usage'][channel]['notes'] += usage['notes']
                db['typical_channel_usage'][channel]['control_changes'] += usage['control_changes']
                
            # Categorize by style variation
            for marker in dna['style_markers']:
                db['style_variations'][marker['type']].append(dna['filename'])
                
        # Convert defaultdicts
        db['common_instruments'] = dict(db['common_instruments'])
        db['common_note_patterns'] = dict(db['common_note_patterns'])
        db['typical_channel_usage'] = {k: dict(v) for k, v in db['typical_channel_usage'].items()}
        db['style_variations'] = dict(db['style_variations'])
        
        return db


def main():
    """Test the DNA analyzer."""
    analyzer = DNAAnalyzer()
    
    # Test on Gold DNA files
    gold_dir = "/workspace/korg-midi-optimizer/data/gold/Gold DNA"
    print(f"Analyzing Gold DNA files in {gold_dir}...")
    
    dna_results = analyzer.analyze_directory(gold_dir)
    print(f"Analyzed {len(dna_results)} files")
    
    if dna_results:
        sample = dna_results[0]
        print(f"\nSample analysis for {sample.get('filename', 'unknown')}:")
        print(f"  Tracks: {sample.get('total_tracks', 0)}")
        print(f"  Notes: {sample.get('total_notes', 0)}")
        print(f"  Duration (ticks): {sample.get('duration_ticks', 0)}")
        print(f"  Style markers: {len(sample.get('style_markers', []))}")
        print(f"  Instruments: {sample.get('instruments', {})}")
    
    return dna_results


if __name__ == "__main__":
    main()
