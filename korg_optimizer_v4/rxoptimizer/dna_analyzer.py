"""
Korg MIDI Optimizer - DNA Analyzer
Analizira Factory Styles i Gold DNA za generisanje pravila optimizacije
"""

import os
import json
import mido
from collections import defaultdict
from typing import Dict, List, Any, Tuple
from datetime import datetime

class DNAAnalyzer:
    """Analizator DNA pattern-a za Korg stilove"""
    
    # Korg specifični markeri koje treba detektovati
    STYLE_MARKERS = {
        'Intro': ['Intro', 'INTRO', 'I1', 'I2', 'I3', 'I4'],
        'Variation': ['Var', 'VAR', 'V1', 'V2', 'V3', 'V4', 'A', 'B', 'C', 'D'],
        'Fill': ['Fill', 'FILL', 'F1', 'F2', 'F3', 'F4'],
        'Break': ['Break', 'BREAK', 'BRK'],
        'Ending': ['End', 'END', 'E1', 'E2', 'E3', 'E4']
    }
    
    # Esencijalni CC-ovi za Korg
    ESSENTIAL_CCS = {1, 7, 10, 11, 64, 91, 93}
    
    # Korg NTT (Note Transpose Table) parametri
    NTT_CHANNELS = list(range(16))
    
    def __init__(self):
        self.stats = {'cc_frequency': defaultdict(int)}
        self.markers_found = []
        self.total_files = 0
        self.total_tracks = 0
        self.total_notes = 0
        self.total_ccs = 0
        
    def analyze_file(self, filepath: str) -> Dict[str, Any]:
        """Analizira pojedinačni MIDI fajl"""
        try:
            mid = mido.MidiFile(filepath)
        except Exception as e:
            return {'error': str(e), 'filepath': filepath}
        
        file_stats = {
            'filename': os.path.basename(filepath),
            'tpq': mid.ticks_per_beat,
            'type': mid.type,
            'duration_ticks': 0,
            'tracks': [],
            'markers': [],
            'notes': defaultdict(list),
            'ccs': defaultdict(list),
            'velocities': [],
            'channels_used': set()
        }
        
        current_time = 0
        
        for track_idx, track in enumerate(mid.tracks):
            track_stats = {
                'index': track_idx,
                'name': '',
                'notes_count': 0,
                'cc_count': 0,
                'marker_count': 0,
                'channel_usage': defaultdict(int)
            }
            
            running_status = {}
            
            for msg in track:
                current_time += msg.time
                
                if msg.type == 'track_name':
                    track_stats['name'] = msg.name
                    
                elif msg.type == 'marker':
                    marker_text = msg.text
                    file_stats['markers'].append({
                        'time': current_time,
                        'text': marker_text,
                        'type': self._classify_marker(marker_text)
                    })
                    track_stats['marker_count'] += 1
                    self.markers_found.append(marker_text)
                    
                elif msg.type == 'note_on' and msg.velocity > 0:
                    note_data = {
                        'note': msg.note,
                        'velocity': msg.velocity,
                        'time': current_time,
                        'channel': msg.channel,
                        'track': track_idx
                    }
                    file_stats['notes'][msg.channel].append(note_data)
                    file_stats['velocities'].append(msg.velocity)
                    file_stats['channels_used'].add(msg.channel)
                    track_stats['notes_count'] += 1
                    track_stats['channel_usage'][msg.channel] += 1
                    self.total_notes += 1
                    
                elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                    pass  # Note off handled implicitly
                    
                elif msg.type == 'control_change':
                    cc_data = {
                        'cc': msg.control,
                        'value': msg.value,
                        'time': current_time,
                        'channel': msg.channel
                    }
                    file_stats['ccs'][msg.channel].append(cc_data)
                    file_stats['channels_used'].add(msg.channel)
                    track_stats['cc_count'] += 1
                    self.total_ccs += 1
                    
                    # Prati frekvenciju CC-eva
                    self.stats['cc_frequency'][msg.control] += 1
                    
                elif hasattr(msg, 'channel'):
                    file_stats['channels_used'].add(msg.channel)
            
            file_stats['duration_ticks'] = max(file_stats['duration_ticks'], current_time)
            file_stats['tracks'].append(track_stats)
            self.total_tracks += 1
        
        # Analiza velocity distribucije
        if file_stats['velocities']:
            file_stats['velocity_stats'] = {
                'min': min(file_stats['velocities']),
                'max': max(file_stats['velocities']),
                'avg': sum(file_stats['velocities']) / len(file_stats['velocities']),
                'distribution': self._calculate_velocity_distribution(file_stats['velocities'])
            }
        
        # Konvertuj set u listu za JSON serializaciju
        file_stats['channels_used'] = list(file_stats['channels_used'])
        
        self.total_files += 1
        return file_stats
    
    def _classify_marker(self, text: str) -> str:
        """Klasifikuje marker tip"""
        text_upper = text.upper()
        for marker_type, keywords in self.STYLE_MARKERS.items():
            if any(kw in text_upper for kw in keywords):
                return marker_type
        return 'Other'
    
    def _calculate_velocity_distribution(self, velocities: List[int]) -> Dict[str, float]:
        """Računa distribuciju velocity vrednosti"""
        ranges = {
            'very_soft (0-30)': 0,
            'soft (31-60)': 0,
            'medium (61-90)': 0,
            'loud (91-120)': 0,
            'very_loud (121-127)': 0
        }
        
        for v in velocities:
            if v <= 30:
                ranges['very_soft (0-30)'] += 1
            elif v <= 60:
                ranges['soft (31-60)'] += 1
            elif v <= 90:
                ranges['medium (61-90)'] += 1
            elif v <= 120:
                ranges['loud (91-120)'] += 1
            else:
                ranges['very_loud (121-127)'] += 1
        
        total = len(velocities)
        return {k: round(v/total*100, 2) for k, v in ranges.items()}
    
    def analyze_directory(self, directory: str, recursive: bool = True) -> Dict[str, Any]:
        """Analizira sve MIDI fajlove u direktorijumu"""
        results = {
            'directory': directory,
            'timestamp': datetime.now().isoformat(),
            'files_analyzed': 0,
            'file_results': [],
            'summary': {}
        }
        
        if recursive:
            file_iterator = []
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if file.lower().endswith(('.mid', '.midi')):
                        file_iterator.append(os.path.join(root, file))
        else:
            file_iterator = [
                os.path.join(directory, f) 
                for f in os.listdir(directory) 
                if f.lower().endswith(('.mid', '.midi'))
            ]
        
        for filepath in file_iterator:
            file_result = self.analyze_file(filepath)
            if 'error' not in file_result:
                results['file_results'].append(file_result)
                results['files_analyzed'] += 1
        
        # Generiši summary
        results['summary'] = self.generate_summary(results['file_results'])
        
        return results
    
    def generate_summary(self, file_results: List[Dict]) -> Dict[str, Any]:
        """Generiše sažetak analize"""
        if not file_results:
            return {'error': 'No files analyzed'}
        
        all_velocities = []
        all_channels = set()
        all_markers = []
        cc_freq = defaultdict(int)
        tpq_values = []
        
        for result in file_results:
            all_velocities.extend(result.get('velocities', []))
            all_channels.update(result.get('channels_used', []))
            all_markers.extend(result.get('markers', []))
            tpq_values.append(result.get('tpq', 480))
            
            for channel, ccs in result.get('ccs', {}).items():
                for cc in ccs:
                    cc_freq[cc['cc']] += 1
        
        # Najčešći TPQ
        most_common_tpq = max(set(tpq_values), key=tpq_values.count) if tpq_values else 480
        
        # Top CC-evi
        top_ccs = sorted(cc_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Marker statistika
        marker_types = defaultdict(int)
        for marker in all_markers:
            marker_types[marker.get('type', 'Other')] += 1
        
        return {
            'total_files': len(file_results),
            'total_notes': sum(len(r.get('notes', {})) for r in file_results),
            'total_tracks': sum(len(r.get('tracks', [])) for r in file_results),
            'most_common_tpq': most_common_tpq,
            'channels_used': sorted(list(all_channels)),
            'velocity_stats': self._calculate_velocity_distribution(all_velocities) if all_velocities else {},
            'top_ccs': [{'cc': cc, 'count': count} for cc, count in top_ccs],
            'marker_distribution': dict(marker_types),
            'recommended_rules': self._generate_recommended_rules(cc_freq, marker_types)
        }
    
    def _generate_recommended_rules(self, cc_freq: Dict, marker_types: Dict) -> List[Dict]:
        """Generiše preporučena pravila na osnovu analize"""
        rules = []
        
        # Pravilo za esencijalne CC-eve
        essential_preserved = [cc for cc in self.ESSENTIAL_CCS if cc_freq.get(cc, 0) > 0]
        if essential_preserved:
            rules.append({
                'rule': 'preserve_essential_ccs',
                'description': 'Sačuvaj kritične CC kontrolere',
                'ccs': essential_preserved
            })
        
        # Pravilo za style markere
        if any(count > 0 for count in marker_types.values()):
            rules.append({
                'rule': 'preserve_style_markers',
                'description': 'Obavezno sačuvaj sve style markere',
                'types': list(marker_types.keys())
            })
        
        # Pravilo za velocity threshold
        rules.append({
            'rule': 'remove_zero_velocity',
            'description': 'Ukloni note sa velocity 0',
            'threshold': 0
        })
        
        # Pravilo za quantization bubnjeva
        rules.append({
            'rule': 'quantize_drums_strict',
            'description': 'Strogi quantization za bubnjeve (kanal 10)',
            'channel': 10,
            'grid': '16th'
        })
        
        return rules
    
    def export_rules(self, summary: Dict, output_file: str):
        """Eksportuje pravila u JSON fajl"""
        rules_config = {
            'version': '2.0',
            'generated': datetime.now().isoformat(),
            'source_summary': summary,
            'optimization_rules': summary.get('recommended_rules', [])
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(rules_config, f, indent=2, ensure_ascii=False)
        
        return output_file


def analyze_dna(directory: str, output_file: str = None, recursive: bool = True) -> Dict:
    """
    Glavna funkcija za DNA analizu
    
    Args:
        directory: Putanja do foldera sa MIDI fajlovima
        output_file: Opciona putanja za eksportovanje pravila
        recursive: Da li tražiti fajlove rekurzivno
    
    Returns:
        Dictionary sa rezultatima analize
    """
    analyzer = DNAAnalyzer()
    results = analyzer.analyze_directory(directory, recursive)
    
    if output_file:
        analyzer.export_rules(results['summary'], output_file)
        print(f"Pravila eksportovana u: {output_file}")
    
    return results


if __name__ == '__main__':
    # Demo analiza
    import sys
    if len(sys.argv) > 1:
        target_dir = sys.argv[1]
    else:
        target_dir = './data/input'
    
    print(f"Analiziram DNA iz: {target_dir}")
    results = analyze_dna(target_dir, './rules.json')
    
    print(f"\n=== REZULTATI ANALIZE ===")
    print(f"Fajlova analizirano: {results['files_analyzed']}")
    summary = results['summary']
    print(f"Najčešći TPQ: {summary.get('most_common_tpq', 'N/A')}")
    print(f"Korišćeni kanali: {summary.get('channels_used', [])}")
    print(f"Distribucija velocity-ja: {summary.get('velocity_stats', {})}")
    print(f"\nPreporučena pravila:")
    for rule in summary.get('recommended_rules', []):
        print(f"  - {rule['description']}")
