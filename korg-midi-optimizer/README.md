# Korg MIDI Optimizer

Aplikacija za optimizaciju MIDI fajlova na osnovu Factory Styles i Gold DNA pattern-a.

## Struktura Projekta

```
korg-midi-optimizer/
├── src/
│   ├── __init__.py
│   ├── dna_analyzer.py      # Analiza MIDI DNA pattern-a
│   └── optimizer.py         # Optimizacija MIDI fajlova
├── tests/
│   └── test_optimizer.py    # Test suite (13 testova)
├── data/
│   ├── gold_dna/            # 182 Gold DNA MIDI fajla
│   └── factory_styles/      # 3211 Factory Style MIDI fajla
├── output/                  # Output direktorijum
├── main.py                  # CLI aplikacija
└── README.md                # Dokumentacija
```

## Pravila Optimizacije

1. **Uklanjanje redundantnih eventa** - Duplicirani tempo change-ovi se uklanjaju
2. **Čišćenje control change-ova** - Uzastopni isti CC-ovi se konsoliduju
3. **Standardizacija track-ova** - Održavanje Korg-kompatibilne strukture
4. **Optimizacija kanala** - Drum track-ovi na channel 9
5. **Očuvanje style markera** - Intro, Var1-4, Fill, Break, End sekcije

## Upotreba

### Analiza direktorijuma

```bash
python main.py data/gold_dna -o output/analyzed --analyze-only
```

### Optimizacija pojedinačnog fajla

```bash
python main.py "input.mid" -o output/optimized \
    --gold-dna data/gold_dna \
    --factory-styles data/factory_styles \
    -v
```

### Optimizacija celog direktorijuma

```bash
python main.py data/gold_dna -o output/optimized \
    --gold-dna data/gold_dna \
    --factory-styles data/factory_styles \
    --report
```

### Samo analiza sa detaljnim report-om

```bash
python main.py data/gold_dna -o output/report \
    --analyze-only --report
```

## Rezultati Analize

### Gold DNA (182 fajla)
- Tempo opseg: 46 - 215 BPM
- Prosečan tempo: 115.3 BPM

### Factory Styles (3211 fajla)
- Tempo opseg: 57 - 196 BPM  
- Prosečan tempo: 112.7 BPM

## Testiranje

Svi testovi prolaze:

```bash
cd korg-midi-optimizer
python -m pytest tests/test_optimizer.py -v
```

Test coverage:
- ✅ DNA Analyzer funkcionalnost
- ✅ Optimizer pravila
- ✅ File processing pipeline
- ✅ Edge cases i error handling
- ✅ Integration testi

## Primer Optimizacije

```
Optimizing: A JA VOLIM ONO T-KORIJENI UZIVO.MID
  Output: output/optimized/A JA VOLIM ONO T-KORIJENI UZIVO.MID
  Improvements:
    - message_reduction: 79 messages (0.24%)
    - cc_cleanup: 78 removed
```

## Instalacija Zavisnosti

```bash
pip install mido pytest
```

## Napomene

- Aplikacija koristi DNA profile iz Gold i Factory Styles kolekcija
- Optimizacija je neinvazivna - čuva muzički sadržaj
- Output fajlovi su Korg keyboard kompatibilni
- Support za Type 0 i Type 1 MIDI fajlove
