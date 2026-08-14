"""
Korg MIDI Optimizer - DNA Analyzer
Analizira Factory Styles i Gold DNA za generisanje pravila optimizacije
"""

import mido
from typing import Dict, List, Any, Optional
import os
import json
from collections import defaultdict


class DNAAnalyzer:
    """Analizira MIDI pattern-e iz Factory Styles i Gold DNA"""
    
    def __init__(self):
        self.essential_cc = [1, 7, 10, 11, 64, 91, 93]
        self.style_markers = ['INTRO', 'VAR', 'FILL', 'BREAK', 'ENDING']
        self.patterns = {
            'cc_usage': defaultdict(int),
            'note_patterns': [],
            'velocity_ranges': {},
            'marker_positions': []
        }
    
    def analyze_directory(self, directory: str) -> Dict[str, Any]:
        """
        Analiziraj sve MIDI fajlove u direktorijumu
        
        Args:
            directory: Putanja do direktorijuma sa MIDI fajlovima
            
        Returns:
            Dictionary sa analiziranim DNA podacima
        """
        if not os.path.exists(directory):
            return {'error': f'Directory not found: {directory}'}
        
        results = {
            'total_files': 0,
            'analyzed_files': 0,
            'failed_files': 0,
            'dna_rules': {
                'essential_cc': self.essential_cc.copy(),
                'style_markers': self.style_markers.copy(),
                'common_cc': [],
                'velocity_profile': {},
                'note_density': {},
                'marker_structure': []
            },
            'files_analyzed': []
        }
        
        cc_counter = defaultdict(int)
        velocity_data = []
        note_counts = []
        
        for filename in os.listdir(directory):
            if filename.lower().endswith('.mid') or filename.lower().endswith('.midi'):
                results['total_files'] += 1
                filepath = os.path.join(directory, filename)
                
                try:
                    analysis = self._analyze_midi_file(filepath)
                    results['analyzed_files'] += 1
                    results['files_analyzed'].append({
                        'filename': filename,
                        'status': 'success',
                        'stats': analysis.get('stats', {})
                    })
                    
                    # Agregiraj podatke
                    for cc_num in analysis.get('cc_usage', []):
                        cc_counter[cc_num] += 1
                    
                    velocity_data.extend(analysis.get('velocities', []))
                    note_counts.append(analysis.get('stats', {}).get('notes', 0))
                    
                    if analysis.get('markers'):
                        results['dna_rules']['marker_structure'].extend(analysis['markers'])
                    
                except Exception as e:
                    results['failed_files'] += 1
                    results['files_analyzed'].append({
                        'filename': filename,
                        'status': 'failed',
                        'error': str(e)
                    })
        
        # Generiši pravila na osnovu analize
        if cc_counter:
            common_cc = sorted(cc_counter.keys(), key=lambda x: cc_counter[x], reverse=True)[:15]
            results['dna_rules']['common_cc'] = common_cc
        
        if velocity_data:
            results['dna_rules']['velocity_profile'] = {
                'min': min(velocity_data),
                'max': max(velocity_data),
                'avg': round(sum(velocity_data) / len(velocity_data), 2),
                'count': len(velocity_data)
            }
        
        if note_counts:
            results['dna_rules']['note_density'] = {
                'min': min(note_counts),
                'max': max(note_counts),
                'avg': round(sum(note_counts) / len(note_counts), 2)
            }
        
        return results
    
    def _analyze_midi_file(self, filepath: str) -> Dict[str, Any]:
        """
        Analiziraj pojedinačni MIDI fajl
        
        Args:
            filepath: Putanja do MIDI fajla
            
        Returns:
            Dictionary sa analizom fajla
        """
        try:
            mid = mido.MidiFile(filepath)
        except Exception as e:
            return {'error': str(e)}
        
        analysis = {
            'stats': {
                'tracks': len(mid.tracks),
                'notes': 0,
                'cc_events': 0,
                'program_changes': 0,
                'markers': 0
            },
            'cc_usage': [],
            'velocities': [],
            'markers': []
        }
        
        cc_seen = set()
        
        for track in mid.tracks:
            for msg in track:
                if msg.type == 'note_on' and msg.velocity > 0:
                    analysis['stats']['notes'] += 1
                    analysis['velocities'].append(msg.velocity)
                elif msg.type == 'control_change':
                    analysis['stats']['cc_events'] += 1
                    if msg.control not in cc_seen:
                        cc_seen.add(msg.control)
                        analysis['cc_usage'].append(msg.control)
                elif msg.type == 'program_change':
                    analysis['stats']['program_changes'] += 1
                elif msg.type == 'marker':
                    analysis['stats']['markers'] += 1
                    marker_text = msg.text.upper()
                    if any(marker in marker_text for marker in self.style_markers):
                        analysis['markers'].append(marker_text)
        
        return analysis
    
    def save_rules(self, rules: Dict[str, Any], output_path: str) -> bool:
        """
        Sačuvaj DNA pravila u JSON fajl
        
        Args:
            rules: DNA pravila
            output_path: Putanja za izlazni fajl
            
        Returns:
            True ako je uspješno, False inače
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(rules, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving rules: {e}")
            return False
    
    def load_rules(self, input_path: str) -> Optional[Dict[str, Any]]:
        """
        Učitaj DNA pravila iz JSON fajla
        
        Args:
            input_path: Putanja do ulaznog fajla
            
        Returns:
            Dictionary sa pravilima ili None ako greška
        """
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading rules: {e}")
            return None


def analyze_dna(directory: str, output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Glavna funkcija za DNA analizu
    
    Args:
        directory: Direktorijum sa MIDI fajlovima
        output_path: Putanja za čuvanje rezultata (opcionalno)
        
    Returns:
        Dictionary sa DNA analizom
    """
    analyzer = DNAAnalyzer()
    results = analyzer.analyze_directory(directory)
    
    if output_path and 'error' not in results:
        analyzer.save_rules(results['dna_rules'], output_path)
        results['rules_saved_to'] = output_path
    
    return results
