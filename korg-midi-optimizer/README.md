# Korg MIDI Optimizer

Aplikacija za optimizaciju MIDI fajlova za Korg keyboard-e koristeći DNA pattern-e iz Factory Styles i Gold style-ova.

## Funkcionalnosti

- **DNA Analiza**: Ekstrahuje muzičke pattern-e, instrumente, ritam strukture i style markere iz MIDI fajlova
- **Optimizacija**: Primenuje pravila za čišćenje i optimizaciju MIDI fajlova:
  - Uklanjanje duplih nota
  - Čišćenje kontrolnih promena (Control Changes)
  - Uklanjanje nota sa nulom velocity
  - Očuvanje style markera (INTRO, VAR, FILL, BREAK, ENDING)
  - Očuvanje esencijalnih CC-eva (Volume, Pan, Modulation, Sustain, Reverb, Chorus)
- **Batch Processing**: Obrada celih direktorijuma MIDI fajlova
- **Detaljni Izveštaji**: Statistika i analize obrađenih fajlova

## Instalacija

```bash
cd korg-midi-optimizer
pip install mido pytest
```

## Upotreba

### Analiza MIDI fajlova

```bash
python main.py analyze ./data/gold/Gold\ DNA
```

### Optimizacija MIDI fajlova

```bash
python main.py optimize ./input ./output
```

### Batch obrada (analiza + optimizacija)

```bash
python main.py batch ./data/gold/Gold\ DNA ./output --detailed
```

### Opcije za optimizaciju

```bash
# Onemogući uklanjanje duplih nota
python main.py optimize ./input ./output --no-duplicates

# Onemogući čišćenje kontrolnih promena
python main.py optimize ./input ./output --no-cc-cleanup

# Zadrži note sa nulom velocity
python main.py optimize ./input ./output --no-zero-vel
```

## Pokretanje testova

```bash
cd korg-midi-optimizer
python -m pytest tests/ -v
```

## Struktura Projekta

```
korg-midi-optimizer/
├── src/
│   ├── __init__.py          # Package initialization
│   ├── dna_analyzer.py      # DNA analiza MIDI fajlova
│   └── optimizer.py         # MIDI optimizer
├── tests/
│   ├── test_dna_analyzer.py # Testovi za DNA analyzer
│   └── test_optimizer.py    # Testovi za optimizer
├── data/
│   ├── factory/             # Factory Style MIDI fajlovi
│   └── gold/                # Gold DNA MIDI fajlovi
├── output/                  # Optimizovani MIDI fajlovi
├── main.py                  # CLI aplikacija
└── README.md                # Dokumentacija
```

## Pravila Optimizacije

### Podrazumevana pravila (aktivna):
- `remove_duplicate_notes`: Uklanja duplicate note na istom tick-u
- `clean_control_changes`: Čisti redundantne kontrolne promene
- `remove_zero_velocity_notes`: Uklanja note_on poruke sa velocity=0
- `preserve_style_markers`: Čuva style markere u track imenima

### Esencijalni Control Change-evi (uvek očuvani):
- CC 1: Modulation
- CC 7: Volume
- CC 10: Pan
- CC 11: Expression
- CC 64: Sustain Pedal
- CC 91: Reverb
- CC 93: Chorus

### Style Markeri (prepoznati):
- INTRO1, INTRO2, INTRO3
- VAR1, VAR2, VAR3, VAR4
- FILL1, FILL2, FILL3, FILL4
- BREAK
- END1, END2, ENDING1, ENDING2

## API Upotreba

```python
from src.dna_analyzer import DNAAnalyzer
from src.optimizer import MIDIOptimizer

# Analiza
analyzer = DNAAnalyzer()
dna = analyzer.analyze_file('path/to/file.mid')
print(f"Style markers: {dna['style_markers']}")
print(f"Instruments: {dna['instruments']}")

# Optimizacija
optimizer = MIDIOptimizer(dna_analyzer=analyzer)
result = optimizer.optimize_file('input.mid', 'output.mid')
print(f"Events removed: {result['original_events'] - result['optimized_events']}")
```

## Autor

Kreirano za optimizaciju MIDI style-ova za Korg keyboard-e.
