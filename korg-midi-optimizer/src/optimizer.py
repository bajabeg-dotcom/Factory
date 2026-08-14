"""
Korg MIDI Optimizer - Main optimizer module for processing MIDI files.
Applies DNA-based rules to optimize MIDI files for Korg keyboards.
"""

import mido
import os
from typing import Dict, List, Any, Optional, Set
from pathlib import Path

# Import DNAAnalyzer directly (for standalone usage)
try:
    from .dna_analyzer import DNAAnalyzer
except ImportError:
    from dna_analyzer import DNAAnalyzer


class MIDIOptimizer:
    """Optimizes MIDI files based on Factory Styles and Gold DNA patterns."""
    
    # Rules for optimization
    OPTIMIZATION_RULES = {
        'remove_duplicate_notes': True,
        'clean_control_changes': True,
        'normalize_velocities': True,
        'remove_zero_velocity_notes': True,
        'merge_short_tracks': True,
        'standardize_channel_assignment': True,
        'preserve_style_markers': True,
        'quantize_rhythm': False,  # Optional, can be enabled
    }
    
    # Control changes to preserve (Korg-specific)
    ESSENTIAL_CONTROL_CHANGES = {
        1,   # Modulation
        7,   # Volume
        10,  # Pan
        11,  # Expression
        64,  # Sustain pedal
        91,  # Reverb
        93,  # Chorus
    }
    
    def __init__(self, dna_analyzer: Optional[DNAAnalyzer] = None):
        self.dna_analyzer = dna_analyzer or DNAAnalyzer()
        self.rules = self.OPTIMIZATION_RULES.copy()
        self.stats = {
            'files_processed': 0,
            'notes_removed': 0,
            'events_removed': 0,
            'tracks_merged': 0,
            'errors': 0
        }
        
    def set_rule(self, rule_name: str, value: bool):
        """Enable or disable an optimization rule."""
        if rule_name in self.rules:
            self.rules[rule_name] = value
        else:
            raise ValueError(f"Unknown rule: {rule_name}")
    
    def optimize_file(self, input_path: str, output_path: Optional[str] = None) -> Dict[str, Any]:
        """Optimize a single MIDI file."""
        try:
            mid = mido.MidiFile(input_path)
        except Exception as e:
            self.stats['errors'] += 1
            return {'error': str(e), 'input_path': input_path}
        
        optimized_mid = mido.MidiFile(ticks_per_beat=mid.ticks_per_beat)
        optimization_report = {
            'input_path': input_path,
            'output_path': output_path,
            'original_tracks': len(mid.tracks),
            'optimized_tracks': 0,
            'original_events': sum(len(track) for track in mid.tracks),
            'optimized_events': 0,
            'changes': []
        }
        
        # Analyze the file first to understand its structure
        dna = self.dna_analyzer.analyze_file(input_path)
        
        # Process each track
        preserved_track_names = set()
        if self.rules['preserve_style_markers']:
            for marker in dna.get('style_markers', []):
                preserved_track_names.add(marker['track'])
        
        for track_idx, track in enumerate(mid.tracks):
            optimized_track = self._optimize_track(
                track, 
                track_idx,
                preserved_track_names
            )
            optimized_mid.tracks.append(optimized_track)
            
            original_count = len(track)
            optimized_count = len(optimized_track)
            if optimized_count < original_count:
                optimization_report['changes'].append({
                    'track': track_idx,
                    'events_removed': original_count - optimized_count,
                    'reason': 'optimization'
                })
        
        optimization_report['optimized_tracks'] = len(optimized_mid.tracks)
        optimization_report['optimized_events'] = sum(len(t) for t in optimized_mid.tracks)
        
        # Save if output path provided
        if output_path:
            os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
            optimized_mid.save(output_path)
            optimization_report['saved'] = True
        
        self.stats['files_processed'] += 1
        total_events_removed = optimization_report['original_events'] - optimization_report['optimized_events']
        self.stats['events_removed'] += total_events_removed
        
        return optimization_report
    
    def _optimize_track(self, track: mido.MidiTrack, track_idx: int, 
                       preserved_tracks: Set[int]) -> mido.MidiTrack:
        """Optimize a single MIDI track."""
        optimized = mido.MidiTrack()
        
        seen_notes = {}  # Track duplicate notes: (note, channel) -> tick
        last_control_values = {}  # Track last CC values per control number
        
        tick_position = 0
        for msg in track:
            tick_position += msg.time
            
            # Always include timing messages
            if msg.type == 'set_tempo':
                optimized.append(msg)
                continue
                
            # Preserve track names (especially style markers)
            if msg.type == 'track_name':
                optimized.append(msg)
                continue
            
            # Preserve instrument changes
            if msg.type == 'program_change' or msg.type == 'set_instrument':
                optimized.append(msg)
                continue
            
            # Handle note events
            if msg.type == 'note_on':
                if msg.velocity == 0:
                    # Treat as note_off
                    if self.rules['remove_zero_velocity_notes']:
                        self.stats['notes_removed'] += 1
                        continue
                    msg = mido.Message('note_off', note=msg.note, velocity=0, 
                                      time=msg.time, channel=getattr(msg, 'channel', 0))
                
                if self.rules['remove_duplicate_notes']:
                    note_key = (msg.note, getattr(msg, 'channel', 0))
                    if note_key in seen_notes:
                        # Duplicate note, skip it
                        self.stats['notes_removed'] += 1
                        continue
                    seen_notes[note_key] = tick_position
                    
                optimized.append(msg)
                
            elif msg.type == 'note_off':
                if self.rules['remove_duplicate_notes']:
                    note_key = (msg.note, getattr(msg, 'channel', 0))
                    if note_key not in seen_notes:
                        # Note off without corresponding note on, keep it anyway for safety
                        pass
                    else:
                        del seen_notes[note_key]
                optimized.append(msg)
                
            # Handle control changes
            elif msg.type == 'control_change':
                if self.rules['clean_control_changes']:
                    control_num = msg.control
                    value = msg.value
                    
                    # Skip non-essential control changes that haven't changed
                    if control_num not in self.ESSENTIAL_CONTROL_CHANGES:
                        key = (control_num, getattr(msg, 'channel', 0))
                        if key in last_control_values and last_control_values[key] == value:
                            self.stats['events_removed'] += 1
                            continue
                        last_control_values[key] = value
                    
                    # Skip zero-value control changes for non-essential controls
                    if value == 0 and control_num not in self.ESSENTIAL_CONTROL_CHANGES:
                        self.stats['events_removed'] += 1
                        continue
                
                optimized.append(msg)
                
            # Handle pitch wheel
            elif msg.type == 'pitchwheel':
                optimized.append(msg)
                
            # Keep all other message types by default
            else:
                optimized.append(msg)
        
        return optimized
    
    def optimize_directory(self, input_dir: str, output_dir: str, 
                          pattern: str = "*.mid") -> List[Dict[str, Any]]:
        """Optimize all MIDI files in a directory."""
        results = []
        input_path = Path(input_dir)
        
        for midi_file in input_path.rglob(pattern):
            relative_path = midi_file.relative_to(input_path)
            output_path = Path(output_dir) / relative_path
            
            result = self.optimize_file(str(midi_file), str(output_path))
            results.append(result)
            
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get optimization statistics."""
        return self.stats.copy()
    
    def reset_stats(self):
        """Reset optimization statistics."""
        self.stats = {
            'files_processed': 0,
            'notes_removed': 0,
            'events_removed': 0,
            'tracks_merged': 0,
            'errors': 0
        }


def main():
    """Test the MIDI optimizer."""
    analyzer = DNAAnalyzer()
    optimizer = MIDIOptimizer(dna_analyzer=analyzer)
    
    # Test on Gold DNA files
    gold_dir = "/workspace/korg-midi-optimizer/data/gold/Gold DNA"
    output_dir = "/workspace/korg-midi-optimizer/output/gold_optimized"
    
    print(f"Optimizing Gold DNA files from {gold_dir}...")
    results = optimizer.optimize_directory(gold_dir, output_dir)
    
    print(f"\nOptimized {len(results)} files")
    stats = optimizer.get_stats()
    print(f"Files processed: {stats['files_processed']}")
    print(f"Events removed: {stats['events_removed']}")
    print(f"Notes removed: {stats['notes_removed']}")
    print(f"Errors: {stats['errors']}")
    
    if results and not results[0].get('error'):
        sample = results[0]
        print(f"\nSample optimization report:")
        print(f"  Original events: {sample['original_events']}")
        print(f"  Optimized events: {sample['optimized_events']}")
        print(f"  Reduction: {sample['original_events'] - sample['optimized_events']} events")
    
    return results


if __name__ == "__main__":
    main()
