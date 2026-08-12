"""
KORG PA800 SOUND REGISTRY
Centralni registar svih zvukova baziran na User Manualu.
Ovo je "Single Source of Truth" za sve profile.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum

class InstrumentCategory(Enum):
    PIANO = "Piano"
    EPIANO = "E.Piano"
    ORGAN = "Organ"
    GUITAR = "Guitar"
    BASS = "Bass"
    STRINGS = "Strings"
    BRASS = "Brass"
    SYNTH = "Synth"
    DRUMS = "Drums"
    PERCUSSION = "Percussion"
    WIND = "Wind"
    VOCAL = "Vocal"
    FX = "SFX"

@dataclass(frozen=True)
class VelocityProfile:
    """5-Dimenzionalni profil za dinamiku"""
    abs_min: int = 1
    abs_max: int = 127
    work_min: int = 20
    work_max: int = 100
    stat_mean: float = 64.0
    stat_std: float = 20.0
    
    def validate(self) -> bool:
        return (self.abs_min <= self.work_min <= self.work_max <= self.abs_max and
                1 <= self.abs_min and self.abs_max <= 127)

@dataclass(frozen=True)
class KeyRangeProfile:
    """Fizički opseg instrumenta na Korg PA800"""
    floor: int = 0      # Najniža nota (MIDI)
    ceiling: int = 127  # Najviša nota (MIDI)
    
    def clamp_note(self, note: int) -> int:
        """Transponuje notu u opseg umjesto brisanja"""
        if note < self.floor:
            while note < self.floor:
                note += 12
        elif note > self.ceiling:
            while note > self.ceiling:
                note -= 12
        return note

@dataclass(frozen=True)
class KorgSoundDefinition:
    """Potpuna definicija jednog zvuka"""
    sound_id: str
    name: str
    category: InstrumentCategory
    bank_msb: int
    bank_lsb: int
    program_change: int
    
    # Profili
    velocity: VelocityProfile
    key_range: KeyRangeProfile
    
    # DNC/RX Metapodaci
    is_dnc: bool = False
    dnc_triggers: List[str] = field(default_factory=list)
    rx_layers: int = 1
    drum_kit_name: Optional[str] = None
    
    # Fingerprint za brzu identifikaciju
    fingerprint: Optional[int] = None  # Npr. 121064042

# ==============================================================================
# FABRIČKI PODACI (Izvučeni iz Korg PA800 Manuala - Sound List)
# Ovo su primjeri - u produkciji ovo punimo iz CSV/JSON generisanog iz PDF-a
# ==============================================================================

def get_default_profiles() -> Dict[InstrumentCategory, Tuple[VelocityProfile, KeyRangeProfile]]:
    """Default profili po kategorijama ako nema specifičnog"""
    return {
        InstrumentCategory.BASS: (
            VelocityProfile(abs_min=20, abs_max=95, work_min=30, work_max=85, stat_mean=55.0, stat_std=15.0),
            KeyRangeProfile(floor=24, ceiling=72)  # E1 do C5
        ),
        InstrumentCategory.GUITAR: (
            VelocityProfile(abs_min=10, abs_max=110, work_min=20, work_max=95, stat_mean=60.0, stat_std=18.0),
            KeyRangeProfile(floor=40, ceiling=96)  # E2 do C7
        ),
        InstrumentCategory.PIANO: (
            VelocityProfile(abs_min=5, abs_max=127, work_min=10, work_max=120, stat_mean=64.0, stat_std=25.0),
            KeyRangeProfile(floor=21, ceiling=108) # A0 do C8
        ),
        InstrumentCategory.DRUMS: (
            VelocityProfile(abs_min=1, abs_max=127, work_min=10, work_max=120, stat_mean=70.0, stat_std=20.0),
            KeyRangeProfile(floor=35, ceiling=81)  # Standard GM Drum map
        ),
        InstrumentCategory.STRINGS: (
            VelocityProfile(abs_min=10, abs_max=115, work_min=20, work_max=100, stat_mean=50.0, stat_std=15.0),
            KeyRangeProfile(floor=36, ceiling=96)
        ),
        InstrumentCategory.BRASS: (
            VelocityProfile(abs_min=20, abs_max=120, work_min=40, work_max=110, stat_mean=75.0, stat_std=20.0),
            KeyRangeProfile(floor=48, ceiling=96)
        ),
    }

class KorgSoundRegistry:
    _instance = None
    _sounds: Dict[str, KorgSoundDefinition] = {}
    _fingerprints: Dict[int, KorgSoundDefinition] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Inicijalizacija registra sa podacima iz manuala"""
        defaults = get_default_profiles()
        
        # Primjer: Acoustic Bass (GM Standard + Korg specifičnosti)
        self._add_sound(KorgSoundDefinition(
            sound_id="KORG_BASS_ACOUSTIC",
            name="Acoustic Bass",
            category=InstrumentCategory.BASS,
            bank_msb=121, # Korg Specific
            bank_lsb=0,
            program_change=32,
            velocity=defaults[InstrumentCategory.BASS][0],
            key_range=defaults[InstrumentCategory.BASS][1],
            is_dnc=True,
            dnc_triggers=["slide", "pop"]
        ))
        
        # Primjer: Grand Piano
        self._add_sound(KorgSoundDefinition(
            sound_id="KORG_PIANO_GRAND",
            name="Concert Grand",
            category=InstrumentCategory.PIANO,
            bank_msb=121,
            bank_lsb=0,
            program_change=0,
            velocity=defaults[InstrumentCategory.PIANO][0],
            key_range=defaults[InstrumentCategory.PIANO][1]
        ))
        
        # Primjer: Finger Bass (Specifičan profil)
        self._add_sound(KorgSoundDefinition(
            sound_id="KORG_BASS_FINGER",
            name="Finger Bass",
            category=InstrumentCategory.BASS,
            bank_msb=121,
            bank_lsb=0,
            program_change=33,
            velocity=VelocityProfile(abs_min=25, abs_max=90, work_min=35, work_max=80, stat_mean=50.0, stat_std=12.0),
            key_range=KeyRangeProfile(floor=24, ceiling=65),
            is_dnc=True,
            dnc_triggers=["mute", "harmonic"]
        ))

    def _add_sound(self, sound: KorgSoundDefinition):
        key = f"{sound.bank_msb}:{sound.bank_lsb}:{sound.program_change}"
        self._sounds[key] = sound
        if sound.fingerprint:
            self._fingerprints[sound.fingerprint] = sound
            
    def lookup(self, msb: int, lsb: int, pc: int) -> Optional[KorgSoundDefinition]:
        """Traži zvuk po Bank/Program parametrima"""
        key = f"{msb}:{lsb}:{pc}"
        return self._sounds.get(key)
    
    def lookup_by_fingerprint(self, fp: int) -> Optional[KorgSoundDefinition]:
        """Traži zvuk po fingerprintu (npr. 121064042)"""
        return self._fingerprints.get(fp)
    
    def get_category_fallback(self, category: InstrumentCategory) -> KorgSoundDefinition:
        """Vraća siguran fallback profil za kategoriju (nikad Klavir za Bas!)"""
        defaults = get_default_profiles()
        v_prof, k_prof = defaults.get(category, defaults[InstrumentCategory.PIANO])
        
        return KorgSoundDefinition(
            sound_id=f"GENERIC_{category.name}",
            name=f"Generic {category.value}",
            category=category,
            bank_msb=0, bank_lsb=0, program_change=0,
            velocity=v_prof,
            key_range=k_prof
        )

    def get_all_sounds(self) -> List[KorgSoundDefinition]:
        return list(self._sounds.values())

# Singleton instanca
registry = KorgSoundRegistry()
