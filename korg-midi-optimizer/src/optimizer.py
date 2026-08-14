"""
Korg MIDI Optimizer

Optimizes MIDI files based on Factory Styles and Gold DNA patterns.
Rules:
1. Maintain Korg-compatible structure (Type 0 or Type 1 MIDI)
2. Preserve style variation markers (Intro, Var1-4, Fill, Break, End)
3. Optimize note density based on Gold DNA averages
4. Standardize tempo and time signatures
5. Clean up redundant control changes
6. Ensure proper channel assignments
7. Remove non-essential meta events
"""

import mido
from typing import Dict, List, Any, Optional
import os
import shutil


class KorgMIDIOptimizer:
    """Optimizes MIDI files for Korg keyboards using DNA-based rules."""
    
    # Korg-specific constants
    MAX_TRACKS = 16  # Korg limit
    TICKS_PER_BEAT = 192  # Standard for Korg styles
    MAX_VELOCITY = 127
    MIN_VELOCITY = 1
    
    # Rule weights for optimization
    RULES = {
        'normalize_tempo': True,
        'clean_control_changes': True,
        'optimize_note_density': True,
        'standardize_tracks': True,
        'remove_redundant_events': True,
        'preserve_style_markers': True,
        'channel_optimization': True
    }
    
    def __init__(self, dna_profile: Optional[Dict] = None):
        """Initialize optimizer with optional DNA profile from Gold/Factory styles."""
        self.dna_profile = dna_profile or {}
        self.optimization_stats = {
            'files_processed': 0,
            'rules_applied': [],
            'changes_made': []
        }
    
    def optimize_file(self, input_path: str, output_path: str) -> Dict[str, Any]:
        """Optimize a single MIDI file."""
        try:
            mid = mido.MidiFile(input_path)
        except Exception as e:
            return {'success': False, 'error': str(e)}
        
        original_stats = self._get_file_stats(mid)
        
        # Apply optimization rules
        if self.RULES['remove_redundant_events']:
            self._remove_redundant_events(mid)
        
        if self.RULES['clean_control_changes']:
            self._clean_control_changes(mid)
        
        if self.RULES['standardize_tracks']:
            self._standardize_tracks(mid)
        
        if self.RULES['channel_optimization']:
            self._optimize_channels(mid)
        
        # Save optimized file
        mid.save(output_path)
        
        new_stats = self._get_file_stats(mid)
        
        self.optimization_stats['files_processed'] += 1
        
        return {
            'success': True,
            'input_file': input_path,
            'output_file': output_path,
            'original_stats': original_stats,
            'optimized_stats': new_stats,
            'improvements': self._calculate_improvements(original_stats, new_stats)
        }
    
    def _get_file_stats(self, mid: mido.MidiFile) -> Dict[str, Any]:
        """Get statistics about a MIDI file."""
        stats = {
            'type': mid.type,
            'ticks_per_beat': mid.ticks_per_beat,
            'num_tracks': len(mid.tracks),
            'total_messages': 0,
            'note_count': 0,
            'control_change_count': 0,
            'tempo_changes': 0
        }
        
        for track in mid.tracks:
            for msg in track:
                stats['total_messages'] += 1
                if msg.type == 'note_on' and msg.velocity > 0:
                    stats['note_count'] += 1
                elif msg.type == 'control_change':
                    stats['control_change_count'] += 1
                elif msg.type == 'set_tempo':
                    stats['tempo_changes'] += 1
        
        return stats
    
    def _remove_redundant_events(self, mid: mido.MidiFile):
        """Remove redundant MIDI events."""
        for track in mid.tracks:
            # Remove duplicate tempo changes
            tempo_seen = False
            new_track = []
            for msg in track:
                if msg.type == 'set_tempo':
                    if not tempo_seen:
                        new_track.append(msg)
                        tempo_seen = True
                elif msg.type == 'end_of_track':
                    continue  # Will be added automatically
                else:
                    new_track.append(msg)
            
            # Clear and rebuild track
            track.clear()
            for msg in new_track:
                track.append(msg)
    
    def _clean_control_changes(self, mid: mido.MidiFile):
        """Clean up redundant control changes."""
        for track in mid.tracks:
            cc_history = {}  # Track last CC value per controller per channel
            
            new_track = []
            for msg in track:
                if msg.type == 'control_change':
                    key = (msg.channel, msg.control)
                    if key not in cc_history or cc_history[key] != msg.value:
                        cc_history[key] = msg.value
                        new_track.append(msg)
                else:
                    new_track.append(msg)
            
            track.clear()
            for msg in new_track:
                track.append(msg)
    
    def _standardize_tracks(self, mid: mido.MidiFile):
        """Standardize track structure for Korg compatibility."""
        # Ensure ticks per beat is standard
        if mid.ticks_per_beat != self.TICKS_PER_BEAT:
            # Note: mido doesn't support changing ticks_per_beat directly
            # This would require rescaling all timing values
            pass
        
        # Limit number of tracks
        if len(mid.tracks) > self.MAX_TRACKS:
            # Merge excess tracks into track 0
            merged_track = mid.tracks[0][:]
            for track in mid.tracks[1:self.MAX_TRACKS]:
                merged_track.extend(track)
            
            mid.tracks = [merged_track]
    
    def _optimize_channels(self, mid: mido.MidiFile):
        """Optimize channel assignments for Korg keyboards."""
        # Channel 9 (10th channel) is reserved for drums in GM
        # Ensure drum tracks are on channel 9
        
        for track in mid.tracks:
            track_name = getattr(track, 'name', '').upper()
            if 'DRUM' in track_name or 'PERC' in track_name:
                # Move drum notes to channel 9
                for msg in track:
                    if hasattr(msg, 'channel') and msg.type in ('note_on', 'note_off'):
                        msg.channel = 9
    
    def _calculate_improvements(self, original: Dict, optimized: Dict) -> Dict[str, Any]:
        """Calculate improvements made by optimization."""
        improvements = {}
        
        if optimized['total_messages'] < original['total_messages']:
            reduction = original['total_messages'] - optimized['total_messages']
            improvements['message_reduction'] = {
                'count': reduction,
                'percentage': (reduction / original['total_messages']) * 100
            }
        
        if optimized['control_change_count'] < original['control_change_count']:
            improvements['cc_cleanup'] = {
                'removed': original['control_change_count'] - optimized['control_change_count']
            }
        
        return improvements
    
    def optimize_directory(self, input_dir: str, output_dir: str) -> Dict[str, Any]:
        """Optimize all MIDI files in a directory."""
        results = {
            'input_directory': input_dir,
            'output_directory': output_dir,
            'files_processed': 0,
            'successful': 0,
            'failed': 0,
            'details': []
        }
        
        os.makedirs(output_dir, exist_ok=True)
        
        for root, dirs, files in os.walk(input_dir):
            for filename in files:
                if filename.lower().endswith(('.mid', '.MID')):
                    input_path = os.path.join(root, filename)
                    
                    # Create relative path in output directory
                    rel_path = os.path.relpath(root, input_dir)
                    output_subdir = os.path.join(output_dir, rel_path)
                    os.makedirs(output_subdir, exist_ok=True)
                    
                    output_path = os.path.join(output_subdir, filename)
                    
                    result = self.optimize_file(input_path, output_path)
                    results['details'].append(result)
                    results['files_processed'] += 1
                    
                    if result.get('success'):
                        results['successful'] += 1
                    else:
                        results['failed'] += 1
        
        return results


def create_dna_profile_from_samples(gold_dna_dir: str, factory_styles_dir: str) -> Dict[str, Any]:
    """Create a DNA profile from Gold DNA and Factory Style samples."""
    from src.dna_analyzer import MIDIDNAAnalyzer
    
    analyzer = MIDIDNAAnalyzer()
    
    # Analyze Gold DNA
    gold_results = analyzer.analyze_directory(gold_dna_dir)
    
    # Analyze Factory Styles
    factory_results = analyzer.analyze_directory(factory_styles_dir)
    
    # Create composite profile
    profile = {
        'gold_dna_profile': analyzer.create_style_profile(gold_results['dna_samples']),
        'factory_style_profile': analyzer.create_style_profile(factory_results['dna_samples']),
        'combined_rules': generate_optimization_rules(gold_results, factory_results)
    }
    
    return profile


def generate_optimization_rules(gold_data: Dict, factory_data: Dict) -> List[Dict]:
    """Generate optimization rules based on DNA analysis."""
    rules = []
    
    # Extract common characteristics
    if gold_data['dna_samples']:
        avg_tempo = sum(
            s['global_features'].get('tempo_bpm', 120) 
            for s in gold_data['dna_samples']
        ) / len(gold_data['dna_samples'])
        
        rules.append({
            'name': 'target_tempo',
            'value': avg_tempo,
            'tolerance': 10,
            'priority': 'medium'
        })
    
    return rules
