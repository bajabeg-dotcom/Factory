"""
KORG PA800 SOUND REGISTRY
Izvor Istine za sve zvukove, baziran na GM standardu i Korg PA800 implementaciji.

Struktura:
BankMSB, BankLSB, PC, Name, Category, Type, VelAbsMin, VelWorkMin, VelWorkMax, VelAbsMax, KeyMin, KeyMax, DNC_Support, RX_Layers
"""

# Format: (MSB, LSB, PC, "Name", "Category", "Type", v_abs_min, v_work_min, v_work_max, v_abs_max, k_min, k_max, dnc, rx)
# Napomene za Type:
# - BASS: Stroga pravila za čistoću (max 95-100), monofono ponašanje.
# - KEYS: Širok dinamički opseg.
# - GUITAR: DNC podrška za slide/hammer.
# - DRUMS: Specifične mape za channel 10.
# - STRINGS/BRASS: DNC za artikulacije.

KORG_SOUND_REGISTRY = [
    # PIANO (PC 0-7)
    (0, 0, 0, "Stereo Piano", "Piano", "KEYS", 10, 30, 110, 127, 21, 108, False, 2),
    (0, 0, 1, "Bright Piano", "Piano", "KEYS", 10, 40, 115, 127, 21, 108, False, 2),
    (0, 0, 2, "E.Piano", "E.Piano", "KEYS", 5, 20, 100, 127, 28, 108, False, 1),
    (0, 0, 3, "Club E.Piano", "E.Piano", "KEYS", 5, 20, 95, 120, 28, 108, False, 1),
    (0, 0, 4, "Harpsichord", "Harpsichord", "KEYS", 20, 50, 90, 100, 41, 96, False, 0),
    (0, 0, 5, "Vibraphone", "Mallet", "KEYS", 10, 30, 100, 120, 48, 84, True, 1),
    (0, 0, 6, "Organ", "Organ", "KEYS", 10, 40, 100, 127, 36, 96, False, 0),
    
    # CHROMATIC PERCUSSION
    (0, 0, 8, "Music Box", "Mallet", "KEYS", 10, 30, 80, 100, 48, 84, False, 0),
    (0, 0, 9, "Celesta", "Mallet", "KEYS", 10, 30, 90, 110, 48, 96, False, 0),
    
    # BASS (PC 32-39) - KRITIČNO ZA PRAVILO "NE PREĆI 95"
    (0, 0, 32, "Acoustic Bass", "Bass", "BASS", 20, 40, 85, 95, 28, 64, False, 1), # Finger Bass
    (0, 0, 33, "Electric Bass", "Bass", "BASS", 20, 45, 90, 100, 28, 64, False, 1), # Pick Bass
    (0, 0, 34, "Fretless Bass", "Bass", "BASS", 20, 40, 85, 95, 28, 64, True, 1),  # Fretless (DNC Slide)
    (0, 0, 35, "Slap Bass 1", "Bass", "BASS", 30, 60, 100, 115, 28, 64, False, 2), # Slap (High Dynamics)
    (0, 0, 36, "Slap Bass 2", "Bass", "BASS", 30, 60, 100, 115, 28, 64, False, 2),
    (0, 0, 37, "Synth Bass 1", "Bass", "BASS_SYNTH", 10, 40, 90, 110, 24, 72, False, 0),
    (0, 0, 38, "Synth Bass 2", "Bass", "BASS_SYNTH", 10, 40, 90, 110, 24, 72, False, 0),
    
    # GUITAR (PC 24-31) - DNC ZONA
    (0, 0, 24, "Nylon Guitar", "Guitar", "GUITAR", 20, 40, 90, 110, 40, 84, True, 1),
    (0, 0, 25, "Steel Guitar", "Guitar", "GUITAR", 20, 45, 95, 115, 40, 84, True, 1),
    (0, 0, 26, "Jazz Guitar", "Guitar", "GUITAR", 20, 40, 85, 105, 40, 84, True, 1),
    (0, 0, 27, "Clean Guitar", "Guitar", "GUITAR", 20, 45, 95, 115, 40, 84, True, 1),
    (0, 0, 28, "Muted Guitar", "Guitar", "GUITAR", 30, 50, 90, 100, 40, 84, True, 1),
    (0, 0, 29, "Overdrive Guitar", "Guitar", "GUITAR", 40, 60, 100, 120, 40, 84, True, 1),
    (0, 0, 30, "Distortion Guitar", "Guitar", "GUITAR", 50, 70, 110, 127, 40, 84, True, 1),
    
    # STRINGS (PC 40-47)
    (0, 0, 40, "Violin", "Strings", "STRINGS", 10, 30, 100, 120, 55, 96, True, 1),
    (0, 0, 41, "Viola", "Strings", "STRINGS", 10, 30, 95, 115, 48, 91, True, 1),
    (0, 0, 42, "Cello", "Strings", "STRINGS", 10, 30, 90, 110, 36, 84, True, 1),
    (0, 0, 43, "Contrabass", "Strings", "STRINGS", 15, 35, 85, 100, 28, 64, True, 1),
    (0, 0, 44, "Tremolo Strings", "Strings", "STRINGS", 20, 40, 90, 110, 48, 96, False, 1),
    (0, 0, 45, "Pizzicato", "Strings", "STRINGS", 20, 40, 85, 100, 48, 96, False, 1),
    (0, 0, 46, "Harp", "Strings", "KEYS", 10, 30, 90, 110, 23, 108, False, 0),
    
    # BRASS (PC 56-63) - DNC ZONA (Falls, Doits)
    (0, 0, 56, "Trumpet", "Brass", "BRASS", 20, 50, 110, 127, 58, 96, True, 1),
    (0, 0, 57, "Trombone", "Brass", "BRASS", 20, 50, 105, 120, 34, 84, True, 1),
    (0, 0, 58, "Tuba", "Brass", "BRASS", 20, 40, 95, 110, 28, 64, True, 1),
    (0, 0, 59, "Muted Trumpet", "Brass", "BRASS", 20, 40, 90, 105, 58, 96, True, 1),
    (0, 0, 60, "French Horn", "Brass", "BRASS", 20, 40, 90, 110, 41, 84, True, 1),
    
    # REED (PC 64-71)
    (0, 0, 64, "Soprano Sax", "Reed", "REED", 20, 50, 105, 120, 58, 96, True, 1),
    (0, 0, 65, "Alto Sax", "Reed", "REED", 20, 50, 105, 120, 58, 96, True, 1),
    (0, 0, 66, "Tenor Sax", "Reed", "REED", 20, 50, 105, 120, 48, 91, True, 1),
    (0, 0, 67, "Baritone Sax", "Reed", "REED", 20, 40, 95, 110, 41, 84, True, 1),
    
    # PIPE (PC 72-79)
    (0, 0, 72, "Flute", "Pipe", "REED", 10, 30, 90, 110, 60, 96, True, 1),
    (0, 0, 73, "Recorder", "Pipe", "REED", 10, 30, 80, 100, 60, 96, False, 0),
    
    # SYNTH LEAD (PC 80-87)
    (0, 0, 80, "Square Lead", "Synth", "SYNTH", 10, 40, 100, 127, 21, 108, False, 0),
    (0, 0, 81, "Sawtooth Lead", "Synth", "SYNTH", 10, 40, 100, 127, 21, 108, False, 0),
    (0, 0, 82, "Calliope", "Synth", "SYNTH", 20, 50, 100, 120, 48, 96, False, 0),
    (0, 0, 83, "Chiff Lead", "Synth", "SYNTH", 10, 30, 90, 110, 48, 96, False, 0),
    
    # SYNTH PAD (PC 88-95)
    (0, 0, 88, "Fantasia", "Synth", "SYNTH", 10, 30, 80, 100, 36, 96, False, 0),
    (0, 0, 89, "Warm Pad", "Synth", "SYNTH", 10, 20, 70, 90, 36, 96, False, 0),
    
    # DRUMS (Channel 10 Special Handling)
    # Ovdje PC definira Kit. Velocity zone su ključne.
    (128, 0, 0, "Standard Kit", "Drums", "DRUMS", 1, 20, 110, 127, 24, 108, False, 3),
    (128, 0, 8, "Room Kit", "Drums", "DRUMS", 1, 20, 100, 120, 24, 108, False, 3),
    (128, 0, 16, "Power Kit", "Drums", "DRUMS", 1, 30, 115, 127, 24, 108, False, 3),
    (128, 0, 24, "Electronic Kit", "Drums", "DRUMS", 1, 20, 100, 127, 24, 108, False, 3),
    (128, 0, 32, "TR-808", "Drums", "DRUMS", 1, 20, 90, 110, 24, 108, False, 2),
    (128, 0, 40, "Jazz Kit", "Drums", "DRUMS", 1, 10, 80, 100, 24, 108, False, 3),
    (128, 0, 48, "Brush Kit", "Drums", "DRUMS", 1, 5, 60, 85, 24, 108, False, 3),
    (128, 0, 56, "Orchestra Kit", "Drums", "DRUMS", 1, 10, 70, 100, 24, 108, False, 3),
]

# Helper dictionary za brzi lookup po (MSB, LSB, PC)
SOUND_MAP = {
    (msb, lsb, pc): {
        "name": name,
        "category": category,
        "type": inst_type,
        "vel_abs_min": v_abs_min,
        "vel_work_min": v_work_min,
        "vel_work_max": v_work_max,
        "vel_abs_max": v_abs_max,
        "key_min": k_min,
        "key_max": k_max,
        "dnc_support": dnc,
        "rx_layers": rx
    }
    for msb, lsb, pc, name, category, inst_type, v_abs_min, v_work_min, v_work_max, v_abs_max, k_min, k_max, dnc, rx in KORG_SOUND_REGISTRY
}

def get_sound_profile(msb: int, lsb: int, pc: int) -> dict | None:
    """
    Vraća detaljan profil za dati zvuk.
    Ako nije nađen, vraća None (ne fallbackuje na generički ovdje!).
    """
    return SOUND_MAP.get((msb, lsb, pc))

def get_fallback_profile_by_type(inst_type: str) -> dict:
    """
    Vraća siguran fallback profil ako specifični zvuk nije nađen,
    ali samo unutar iste kategorije (npr. Bass -> Generic Bass).
    """
    defaults = {
        "BASS": {"name": "Generic Bass", "type": "BASS", "vel_abs_min": 20, "vel_work_min": 40, "vel_work_max": 85, "vel_abs_max": 95, "key_min": 28, "key_max": 64, "dnc_support": False, "rx_layers": 1},
        "KEYS": {"name": "Generic Keys", "type": "KEYS", "vel_abs_min": 10, "vel_work_min": 30, "vel_work_max": 110, "vel_abs_max": 127, "key_min": 21, "key_max": 108, "dnc_support": False, "rx_layers": 1},
        "GUITAR": {"name": "Generic Guitar", "type": "GUITAR", "vel_abs_min": 20, "vel_work_min": 40, "vel_work_max": 95, "vel_abs_max": 115, "key_min": 40, "key_max": 84, "dnc_support": True, "rx_layers": 1},
        "DRUMS": {"name": "Generic Drums", "type": "DRUMS", "vel_abs_min": 1, "vel_work_min": 20, "vel_work_max": 110, "vel_abs_max": 127, "key_min": 24, "key_max": 108, "dnc_support": False, "rx_layers": 3},
        "STRINGS": {"name": "Generic Strings", "type": "STRINGS", "vel_abs_min": 10, "vel_work_min": 30, "vel_work_max": 100, "vel_abs_max": 120, "key_min": 36, "key_max": 96, "dnc_support": True, "rx_layers": 1},
        "BRASS": {"name": "Generic Brass", "type": "BRASS", "vel_abs_min": 20, "vel_work_min": 50, "vel_work_max": 110, "vel_abs_max": 127, "key_min": 34, "key_max": 96, "dnc_support": True, "rx_layers": 1},
        "REED": {"name": "Generic Reed", "type": "REED", "vel_abs_min": 20, "vel_work_min": 50, "vel_work_max": 105, "vel_abs_max": 120, "key_min": 41, "key_max": 96, "dnc_support": True, "rx_layers": 1},
        "SYNTH": {"name": "Generic Synth", "type": "SYNTH", "vel_abs_min": 10, "vel_work_min": 30, "vel_work_max": 100, "vel_abs_max": 127, "key_min": 21, "key_max": 108, "dnc_support": False, "rx_layers": 0},
    }
    return defaults.get(inst_type, defaults["KEYS"])
