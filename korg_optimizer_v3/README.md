# Korg MIDI Optimizer

Aplikacija za optimizaciju MIDI fajlova na osnovu Factory Styles i Gold DNA pattern-a.

## Instalacija (Windows)

1. Otvori Command Prompt u ovom folderu
2. Pokreni: `install.bat`
3. Sačekaj da se instaliraju biblioteke

## Upotreba

### Preko run.bat (preporučeno)

```batch
run.bat analyze data\gold -o rules.json     # Analiziraj DNA
run.bat optimize input.mid -o output.mid    # Optimizuj fajl
run.bat batch input output -d               # Batch optimizacija
run.bat test                                # Pokreni testove
```

### Direktno preko Python-a

```bash
# Analiza DNA iz Factory Styles ili Gold foldera
python main.py analyze ./data/gold -o rules.json

# Optimizacija pojedinačnog fajla
python main.py optimize input.mid -o output.mid

# Optimizacija sa custom pravilima
python main.py optimize input.mid -o output.mid -r rules.json

# Batch optimizacija
python main.py batch ./input ./output -d

# Pokretanje testova
python -m pytest tests/ -v
```

## Pravila Optimizacije

Aplikacija primjenjuje sljedeća pravila:

1. **Uklanjanje zero-velocity nota** - Čisti note bez zvuka
2. **Uklanjanje duplikata** - Spaja identične note na istom kanalu
3. **Čišćenje redundantnih CC** - Uklanja duplicate control change evente
4. **Očuvanje esencijalnih CC** - Zadržava važne parametre:
   - CC1: Modulation
   - CC7: Volume
   - CC10: Pan
   - CC11: Expression
   - CC64: Sustain
   - CC91: Reverb
   - CC93: Chorus
5. **Očuvanje Style Markera** - INTRO, VAR, FILL, BREAK, ENDING

## Struktura Projekta

```
korg_optimizer_v3/
├── rxoptimizer/          # Glavni modul
│   ├── __init__.py
│   ├── dna_analyzer.py   # DNA analiza
│   └── optimizer.py      # MIDI optimizacija
├── tests/                # Testovi
│   └── test_optimizer.py
├── data/                 # Podaci za analizu
│   ├── gold/            # Gold DNA fajlovi
│   └── factory/         # Factory Styles
├── input/               # Ulazni MIDI fajlovi
├── output/              # Izlazni optimizovani fajlovi
├── main.py              # CLI aplikacija
├── install.bat          # Windows instalacija
├── run.bat              # Windows pokretač
├── requirements.txt     # Python zavisnosti
└── README.md            # Dokumentacija
```

## API Upotreba

```python
from rxoptimizer import analyze_dna, optimize, optimize_batch

# Analiza DNA
results = analyze_dna('./data/gold', output_path='rules.json')

# Optimizacija fajla
result = optimize('input.mid', 'output.mid', detailed=True)
print(f"Redukcija: {result['reduction_percentage']}%")

# Batch optimizacija
results = optimize_batch('./input', './output', detailed=True)
print(f"Obrađeno: {results['successful']} od {results['total_files']}")
```

## Zahtjevi

- Python 3.7+
- mido >= 1.2.10
- pytest >= 7.0.0 (za testove)

## Licenca

MIT License
