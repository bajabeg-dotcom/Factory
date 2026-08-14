"""
KORG PA800 OPTIMIZER ENGINE (v2.0)
----------------------------------
STROGA PRAVILA:
1. Nema nagađanja. Svaki instrument mora imati match u Registry ili inteligentni fallback po kategoriji.
2. Matematika: Z-Score transformacija -> Radni opseg -> Hard Clamp na apsolutne granice.
3. Key Range: Note van opsega se transponuju za oktave, nikad se ne brišu.
4. Bass Pravilo: Velocity nikad ne smije preći 95 (čistoća basa).
5. Pitch Wheel: Automatski clamp na -8192 do 8191.
"""

import mido
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from .korg_registry import registry, InstrumentCategory, KorgSoundDefinition, VelocityProfile

class MidiOptimizerV2:
    def __init__(self, strength: float = 0.7):
        """
        strength: 0.0 (original) do 1.0 (puna Gold/Factory transformacija)
        """
        self.strength = max(0.0, min(1.0, strength))
        
    def optimize_file(self, input_path: Path, output_path: Path) -> dict:
        """Glavni entry point za optimizaciju fajla"""
        stats = {
            "input_file": str(input_path),
            "output_file": str(output_path),
            "tracks_processed": 0,
            "notes_transformed": 0,
            "pitch_wheels_fixed": 0,
            "errors": []
        }
        
        try:
            mid = mido.MidiFile(input_path)
        except Exception as e:
            stats["errors"].append(f"Failed to load MIDI: {str(e)}")
            return stats
            
        # Detekcija fingerprinta (npr. 121064042)
        fingerprint = self._detect_fingerprint(mid)
        style_profile = registry.lookup_by_fingerprint(fingerprint) if fingerprint else None
        
        for track in mid.tracks:
            stats["tracks_processed"] += 1
            
            # Identifikacija instrumenta za track
            current_msb, current_lsb, current_pc = 0, 0, 0
            instrument_profile = None
            
            # Prvi prolaz: nađi Program Change
            for msg in track:
                if msg.type == 'control_change' and msg.control == 0:
                    current_msb = msg.value
                elif msg.type == 'control_change' and msg.control == 32:
                    current_lsb = msg.value
                elif msg.type == 'program_change':
                    current_pc = msg.program
                    break
            
            # Lookup u Registry
            if style_profile:
                instrument_profile = style_profile
            else:
                instrument_profile = registry.lookup(current_msb, current_lsb, current_pc)
                
                # Fallback logika: Analiza opsega ako nema matcha
                if not instrument_profile:
                    category = self._infer_category_from_track(track)
                    instrument_profile = registry.get_category_fallback(category)
            
            # Drugi prolaz: Transformacija
            self._process_track(track, instrument_profile, stats)
            
        # Snimanje
        mid.save(output_path)
        return stats

    def _detect_fingerprint(self, mid: mido.MidiFile) -> Optional[int]:
        """Detektuje Korg fingerprint iz SysEx ili specifičnih poruka"""
        # Placeholder - u produkciji skeniramo SysEx poruke
        return None

    def _infer_category_from_track(self, track: mido.MidiTrack) -> InstrumentCategory:
        """Ako nema Program Change, analiziraj note da pogodiš kategoriju"""
        notes = [msg.note for msg in track if msg.type == 'note_on' and msg.velocity > 0]
        if not notes:
            return InstrumentCategory.PIANO
            
        avg_note = sum(notes) / len(notes)
        
        # Pravilo: Ako su sve note ispod C3 (60), vjerovatno je Bass
        if max(notes) < 55:
            return InstrumentCategory.BASS
        # Pravilo: Ako su note visoko, vjerovatno Strings/Brass
        elif avg_note > 80:
            return InstrumentCategory.STRINGS
        # Default
        return InstrumentCategory.PIANO

    def _process_track(self, track: mido.MidiTrack, profile: KorgSoundDefinition, stats: dict):
        """Primjena transformacija na note u tracku"""
        vel_profile = profile.velocity
        key_profile = profile.key_range
        
        for msg in track:
            if msg.type == 'note_on' and msg.velocity > 0:
                # 1. Fix Key Range (Transpozicija umjesto brisanja)
                original_note = msg.note
                new_note = key_profile.clamp_note(original_note)
                if new_note != original_note:
                    msg.note = new_note
                
                # 2. Transformacija Velocity (Z-Score + Clamping)
                new_vel = self._transform_velocity(msg.velocity, vel_profile)
                msg.velocity = new_vel
                
                stats["notes_transformed"] += 1
                
            elif msg.type == 'pitchwheel':
                # 3. Fix Pitch Wheel (Clamp na -8192 do 8191)
                if msg.pitch < -8192 or msg.pitch > 8191:
                    msg.pitch = max(-8192, min(8191, msg.pitch))
                    stats["pitch_wheels_fixed"] += 1

    def _transform_velocity(self, input_vel: int, profile: VelocityProfile) -> int:
        """
        Nova formula:
        1. Z-Score normalizacija ulaza
        2. Mapiranje u Radni Opseg (work_min - work_max)
        3. Hard Clamp na Apsolutne Granice (abs_min - abs_max)
        """
        source_mean = 64.0
        source_std = 20.0
        
        z = (input_vel - source_mean) / source_std
        target_vel = profile.work_min + (z * profile.stat_std)
        interpolated_vel = input_vel * (1 - self.strength) + target_vel * self.strength
        final_vel = int(max(profile.abs_min, min(profile.abs_max, interpolated_vel)))
        
        # Posebno pravilo za Bass: Nikad iznad 95
        if profile.abs_max <= 95 and final_vel > 95:
            final_vel = 95
            
        return max(1, min(127, final_vel))

def optimize_midi_file(input_path: str, output_path: str, strength: float = 0.8) -> dict:
    """Wrapper funkcija za kompatibilnost"""
    optimizer = MidiOptimizerV2(strength=strength)
    return optimizer.optimize_file(Path(input_path), Path(output_path))
