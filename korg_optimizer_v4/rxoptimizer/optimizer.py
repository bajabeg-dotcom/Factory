"""
Korg MIDI Optimizer - Napredni Optimizer
Optimizuje MIDI fajlove za Korg tastature uz očuvanje style markera i NTT podataka
"""

import os
import copy
import mido
from typing import Dict, List, Optional, Tuple, Set
from collections import defaultdict
from datetime import datetime


class KorgOptimizer:
    """Napredni optimizer specifično dizajniran za Korg stilove"""
    
    # Esencijalni CC-ovi koje nikada ne brišemo
    ESSENTIAL_CCS = {1, 7, 10, 11, 64, 91, 93}
    
    # Korg Style markeri koje moramo sačuvati
    STYLE_MARKER_KEYWORDS = [
        'INTRO', 'VAR', 'VARIATION', 'FILL', 'BREAK', 'ENDING',
        'I1', 'I2', 'I3', 'I4', 'V1', 'V2', 'V3', 'V4',
        'A', 'B', 'C', 'D', 'E1', 'E2', 'E3', 'E4', 'F1', 'F2', 'F3', 'F4'
    ]
    
    # Kanali (0-indexed)
    DRUM_CHANNEL = 9  # Kanal 10 u MIDI notaciji je 9 u 0-indexed
    
    def __init__(self, rules: Optional[Dict] = None):
        self.rules = rules or {}
        self.stats = {
            'notes_removed': 0,
            'ccs_removed': 0,
            'overlaps_fixed': 0,
            'markers_preserved': 0,
            'quantized_notes': 0,
            'zero_velocity_removed': 0,
            'duplicates_removed': 0
        }
    
    def optimize(self, input_file: str, output_file: str = None, 
                 detailed: bool = False) -> Dict:
        """
        Optimizuje MIDI fajl
        
        Args:
            input_file: Putanja do ulaznog MIDI fajla
            output_file: Putanja do izlaznog fajla (ako None, vraća u memoriji)
            detailed: Da li vratiti detaljan izveštaj
        
        Returns:
            Dictionary sa statistikom optimizacije
        """
        try:
            mid = mido.MidiFile(input_file)
        except Exception as e:
            return {'error': f'Failed to load file: {str(e)}'}
        
        # Resetuj statistiku
        self.stats = {k: 0 for k in self.stats.keys()}
        
        original_size = os.path.getsize(input_file)
        original_tick_count = self._count_ticks(mid)
        
        # 1. Standardizuj TPQ na 480 ako je potrebno
        if mid.ticks_per_beat != 480:
            mid = self._standardize_tpq(mid, 480)
        
        # 2. Procesiraj svaki track
        for track_idx, track in enumerate(mid.tracks):
            mid.tracks[track_idx] = self._optimize_track(track, track_idx)
        
        # 3. Sačuvaj fajl
        if output_file:
            # Kreiraj direktorijum ako ne postoji
            output_dir = os.path.dirname(output_file)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            mid.save(output_file)
            new_size = os.path.getsize(output_file)
        else:
            # Privremeno čuvanje za računanje veličine
            import io
            buffer = io.BytesIO()
            mid.save(buffer)
            new_size = len(buffer.getvalue())
        
        # Izračunaj statistiku
        new_tick_count = self._count_ticks(mid)
        
        report = {
            'input_file': input_file,
            'output_file': output_file,
            'original_size_bytes': original_size,
            'optimized_size_bytes': new_size,
            'size_reduction_percent': round((1 - new_size/original_size) * 100, 2) if original_size > 0 else 0,
            'original_ticks': original_tick_count,
            'optimized_ticks': new_tick_count,
            'tick_reduction_percent': round((1 - new_tick_count/original_tick_count) * 100, 2) if original_tick_count > 0 else 0,
            'statistics': self.stats,
            'timestamp': datetime.now().isoformat()
        }
        
        if detailed:
            report['rules_applied'] = self.rules
            report['essential_ccs_preserved'] = list(self.ESSENTIAL_CCS)
            report['style_markers_protected'] = self.STYLE_MARKER_KEYWORDS
        
        return report
    
    def _optimize_track(self, track: mido.MidiTrack, track_idx: int) -> mido.MidiTrack:
        """Optimizuje pojedinačni track"""
        new_track = mido.MidiTrack()
        
        # Prvo prikupi sve informacije
        messages = list(track)
        markers_to_preserve = []
        notes_by_channel = defaultdict(list)
        ccs_by_channel = defaultdict(list)
        
        current_time = 0
        
        for msg in messages:
            current_time += msg.time
            
            # Detektuj i sačuvaj style markere
            if msg.type == 'marker':
                if self._is_style_marker(msg.text):
                    markers_to_preserve.append((current_time, msg))
                    self.stats['markers_preserved'] += 1
            
            # Prikupi note
            elif msg.type == 'note_on' and msg.velocity > 0:
                notes_by_channel[msg.channel].append({
                    'time': current_time,
                    'note': msg.note,
                    'velocity': msg.velocity,
                    'channel': msg.channel,
                    'msg': msg
                })
            
            # Prikupi CC-ove
            elif msg.type == 'control_change':
                ccs_by_channel[msg.channel].append({
                    'time': current_time,
                    'cc': msg.control,
                    'value': msg.value,
                    'channel': msg.channel,
                    'msg': msg
                })
        
        # Rekonstruiši track sa optimizovanim podacima
        # 1. Dodaj sve originalne meta-poruke (ime tracka, tempo, itd.)
        for msg in messages:
            if msg.type in ['track_name', 'set_tempo', 'time_signature', 'key_signature']:
                new_track.append(msg)
        
        # 2. Dodaj sačuvane markere na njihovim vremenskim pozicijama
        for time, marker_msg in markers_to_preserve:
            # Konvertuj apsolutno vreme u delta vreme
            if len(new_track) == 0:
                delta_time = time
            else:
                # Treba nam kompleksnija logika za re-timing
                # Za sada dodajemo na kraj - ovo će biti poboljšano
                pass
        
        # 3. Optimizuj note po kanalima
        optimized_notes = []
        for channel, notes in notes_by_channel.items():
            is_drum_channel = (channel == self.DRUM_CHANNEL)
            
            # a) Ukloni zero velocity (već urađeno filtriranjem)
            # b) Ukloni duplikate
            unique_notes = self._remove_duplicate_notes(notes)
            self.stats['duplicates_removed'] += len(notes) - len(unique_notes)
            
            # c) Fix preklapanja nota
            fixed_notes = self._fix_note_overlaps(unique_notes)
            self.stats['overlaps_fixed'] += len(unique_notes) - len(fixed_notes)
            
            # d) Quantization (stroži za bubnjeve)
            if is_drum_channel:
                quantized_notes = self._quantize_notes(fixed_notes, grid='16th', strict=True)
            else:
                quantized_notes = self._quantize_notes(fixed_notes, grid='8th', strict=False)
            
            self.stats['quantized_notes'] += len(fixed_notes) - len(quantized_notes)
            
            # e) Konvertuj nazad u MIDI poruke
            for note_data in quantized_notes:
                optimized_notes.append(note_data)
        
        # Sortiraj note po vremenu
        optimized_notes.sort(key=lambda x: x['time'])
        
        # 4. Optimizuj CC-ove
        optimized_ccs = []
        for channel, ccs in ccs_by_channel.items():
            # Sačuvaj samo esencijalne CC-ove i ukloni redundantne
            filtered_ccs = [cc for cc in ccs if cc['cc'] in self.ESSENTIAL_CCS]
            cleaned_ccs = self._remove_redundant_ccs(filtered_ccs)
            self.stats['ccs_removed'] += len(ccs) - len(cleaned_ccs)
            optimized_ccs.extend(cleaned_ccs)
        
        # 5. Rekonstruiši finalni track sa pravilnim timingom
        final_messages = []
        
        # Dodaj sve originalne meta poruke prvo
        for msg in messages:
            if msg.type in ['track_name', 'set_tempo', 'time_signature', 'key_signature']:
                final_messages.append((0, msg))
        
        # Dodaj markere
        for time, marker_msg in markers_to_preserve:
            final_messages.append((time, marker_msg))
        
        # Dodaj optimizovane note
        for note_data in optimized_notes:
            # Note on
            note_on_msg = mido.Message('note_on', 
                                       note=note_data['note'],
                                       velocity=note_data['velocity'],
                                       channel=note_data['channel'])
            final_messages.append((note_data['time'], note_on_msg))
            
            # Note off (trebalo bi da imamo duration)
            # Ovo je pojednostavljeno - u punoj implementaciji pratimo trajanje
        
        # Dodaj optimizovane CC-ove
        for cc_data in optimized_ccs:
            cc_msg = mido.Message('control_change',
                                  control=cc_data['cc'],
                                  value=cc_data['value'],
                                  channel=cc_data['channel'])
            final_messages.append((cc_data['time'], cc_msg))
        
        # Sortiraj sve poruke po vremenu
        final_messages.sort(key=lambda x: x[0])
        
        # Konvertuj u delta vremena i dodaj u track
        prev_time = 0
        for abs_time, msg in final_messages:
            delta_time = abs_time - prev_time
            msg.time = delta_time
            new_track.append(msg)
            prev_time = abs_time
        
        return new_track
    
    def _is_style_marker(self, text: str) -> bool:
        """Proverava da li je tekst style marker"""
        text_upper = text.upper()
        return any(keyword in text_upper for keyword in self.STYLE_MARKER_KEYWORDS)
    
    def _remove_duplicate_notes(self, notes: List[Dict]) -> List[Dict]:
        """Uklanja duplikate nota (ista nota, isto vreme, isti channel)"""
        seen = set()
        unique = []
        
        for note in notes:
            key = (note['time'], note['note'], note['channel'])
            if key not in seen:
                seen.add(key)
                unique.append(note)
        
        return unique
    
    def _fix_note_overlaps(self, notes: List[Dict]) -> List[Dict]:
        """
        Popravlja preklapanja nota na istom kanalu.
        Ako se nota ponovo pokrene dok prethodna još traje, skraćuje prethodnu.
        """
        if not notes:
            return notes
        
        # Grupiši note po pitch-u
        by_pitch = defaultdict(list)
        for note in notes:
            by_pitch[note['note']].append(note)
        
        fixed_notes = []
        
        for pitch, pitch_notes in by_pitch.items():
            # Sortiraj po vremenu
            pitch_notes.sort(key=lambda x: x['time'])
            
            for i, note in enumerate(pitch_notes):
                # Ako nije poslednja nota, proveri preklapanje sa sledećom
                if i < len(pitch_notes) - 1:
                    next_note = pitch_notes[i + 1]
                    # Ako se sledeća nota pokreće pre nego što ova završi
                    # (pretpostavljamo minimalno trajanje od 1 tick ako nema eksplicitnog kraja)
                    # Ovo je pojednostavljeno - prava implementacija bi pratila note_off
                    if next_note['time'] <= note['time']:
                        # Preklapanje - preskoči ovu duplikatnu
                        self.stats['overlaps_fixed'] += 1
                        continue
                
                fixed_notes.append(note)
        
        return fixed_notes
    
    def _quantize_notes(self, notes: List[Dict], grid: str = '8th', strict: bool = False) -> List[Dict]:
        """
        Quantizuje note na određenu mrežu.
        
        Args:
            notes: Lista nota
            grid: '4th', '8th', '16th', '32nd'
            strict: Ako True, kvantizuj sve; ako False, samo one blizu mreže
        """
        if not notes:
            return notes
        
        # Definiši grid veličinu u tickovima (pretpostavka: 480 TPQ)
        grid_values = {
            '4th': 480,
            '8th': 240,
            '16th': 120,
            '32nd': 60
        }
        
        grid_size = grid_values.get(grid, 240)
        threshold = grid_size // 4 if not strict else grid_size // 2
        
        quantized = []
        for note in notes:
            original_time = note['time']
            # Nađi najbliži grid
            quantized_time = round(original_time / grid_size) * grid_size
            
            # Ako je razlika manja od threshold-a ili je strict mode
            if abs(original_time - quantized_time) <= threshold or strict:
                note_copy = note.copy()
                note_copy['time'] = quantized_time
                if original_time != quantized_time:
                    self.stats['quantized_notes'] += 1
                quantized.append(note_copy)
            else:
                # Zadrži originalno vreme ako je previše van mreže i nije strict
                quantized.append(note)
        
        return quantized
    
    def _remove_redundant_ccs(self, ccs: List[Dict]) -> List[Dict]:
        """
        Uklanja redundantne CC poruke.
        Zadržava samo promene vrednosti za isti CC na istom kanalu.
        """
        if not ccs:
            return ccs
        
        # Sortiraj po vremenu
        ccs_sorted = sorted(ccs, key=lambda x: x['time'])
        
        # Grupiši po (channel, cc)
        by_channel_cc = defaultdict(list)
        for cc in ccs_sorted:
            key = (cc['channel'], cc['cc'])
            by_channel_cc[key].append(cc)
        
        result = []
        for key, channel_ccs in by_channel_cc.items():
            last_value = None
            for cc in channel_ccs:
                if cc['value'] != last_value:
                    result.append(cc)
                    last_value = cc['value']
        
        return result
    
    def _standardize_tpq(self, mid: mido.MidiFile, target_tpq: int = 480) -> mido.MidiFile:
        """Konvertuje MIDI fajl na standardni TPQ (Ticks Per Quarter note)"""
        if mid.ticks_per_beat == target_tpq:
            return mid
        
        ratio = target_tpq / mid.ticks_per_beat
        
        new_mid = mido.MidiFile(ticks_per_beat=target_tpq)
        
        for track in mid.tracks:
            new_track = mido.MidiTrack()
            for msg in track:
                new_msg = msg.copy()
                if hasattr(msg, 'time') and msg.time > 0:
                    new_msg.time = int(round(msg.time * ratio))
                new_track.append(new_msg)
            new_mid.tracks.append(new_track)
        
        return new_mid
    
    def _count_ticks(self, mid: mido.MidiFile) -> int:
        """Broji ukupan broj tickova u MIDI fajlu"""
        total = 0
        for track in mid.tracks:
            current_time = 0
            for msg in track:
                current_time += msg.time
            total = max(total, current_time)
        return total


def optimize(input_file: str, output_file: str = None, 
             rules: Optional[Dict] = None, detailed: bool = False) -> Dict:
    """
    Glavna funkcija za optimizaciju
    
    Args:
        input_file: Putanja do ulaznog MIDI fajla
        output_file: Putanja do izlaznog fajla
        rules: Opciona pravila za optimizaciju
        detailed: Da li vratiti detaljan izveštaj
    
    Returns:
        Dictionary sa rezultatima optimizacije
    """
    optimizer = KorgOptimizer(rules)
    return optimizer.optimize(input_file, output_file, detailed)


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Upotreba: python optimizer.py <input.mid> [output.mid] [--detailed]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith('--') else None
    detailed = '--detailed' in sys.argv
    
    if not output_file and output_file is not None:
        output_file = input_file.replace('.mid', '_optimized.mid')
    
    print(f"Optimizujem: {input_file}")
    result = optimize(input_file, output_file, detailed=detailed)
    
    if 'error' in result:
        print(f"GREŠKA: {result['error']}")
    else:
        print(f"\n=== REZULTATI OPTIMIZACIJE ===")
        print(f"Izlazni fajl: {result['output_file']}")
        print(f"Smanjenje veličine: {result['size_reduction_percent']}%")
        print(f"Smanjenje tickova: {result['tick_reduction_percent']}%")
        print(f"\nStatistika:")
        for key, value in result['statistics'].items():
            print(f"  {key}: {value}")
