# Korg MIDI Optimizer

Optimizacija MIDI fajlova na osnovu **Factory Styles** i **Gold DNA** pattern-a za Korg keyboardove.

## 📦 Instalacija

```bash
pip install mido pytest
```

## 🚀 Upotreba

### 1. Analiza DNA (Factory Styles / Gold)

Prvo analiziraj Factory Styles ili Gold DNA da generišeš pravila:

```bash
python main.py analyze ./data/gold --output rules.json
```

Ovo će kreirati `rules.json` sa svim pravilima optimizacije.

### 2. Optimizacija pojedinačnog fajla

```bash
python main.py optimize input.mid --output output.mid --detailed
```

Sa custom pravilima:

```bash
python main.py optimize input.mid --output output.mid --rules rules.json --detailed
```

### 3. Batch optimizacija cijelog direktorijuma

```bash
python main.py batch ./input_midi ./output_midi --detailed
```

Sa custom pravilima:

```bash
python main.py batch ./input_midi ./output_midi --rules rules.json --detailed
```

## 📋 Pravila Optimizacije

Aplikacija primjenjuje sljedeća pravila:

### ✅ Uvijek se primjenjuje:
- **Uklanjanje zero-velocity nota** - Note sa velocity=0 se uklanjaju
- **Uklanjanje duplih nota** - Iste note na istom kanalu i vremenu
- **Čišćenje redundantnih CC-eva** - Ponovljeni control change event-i

### 🛡️ Uvijek se očuvava:
- **Esencijalni CC-evi**: 1 (Modulation), 7 (Volume), 10 (Pan), 11 (Expression), 64 (Sustain), 91 (Reverb), 93 (Chorus)
- **Style markeri**: INTRO, VAR, FILL, BREAK, ENDING
- **Program change event-i**
- **Tempo promjene**

### ⚙️ Opcionalno (preko pravila):
- **Spajanje track-ova** (`merge_tracks: true`)
- **Normalizacija velocity-ja** (`normalize_velocities: true`)

## 🧪 Testovi

Pokreni sve testove:

```bash
cd /workspace/korg_optimizer_v2
python -m pytest tests/ -v
```

## 📁 Struktura Projekta

```
korg_optimizer_v2/
├── rxoptimizer/
│   ├── __init__.py          # Package inicijalizacija
│   ├── dna_analyzer.py      # DNA analiza Factory Styles/Gold
│   └── optimizer.py         # MIDI optimizator
├── tests/
│   └── test_optimizer.py    # Testovi (23 testa)
├── main.py                  # CLI aplikacija
├── requirements.txt         # Dependencije
└── README.md               # Dokumentacija
```

## 🔧 API Upotreba

### Python API

```python
from rxoptimizer.dna_analyzer import analyze_dna
from rxoptimizer.optimizer import optimize, optimize_batch

# Analiziraj DNA i generiši pravila
rules = analyze_dna("./data/gold")

# Optimizuj jedan fajl
result = optimize("input.mid", "output.mid", rules, detailed=True)
print(f"Redukcija: {result['reduction_percentage']}%")

# Batch optimizacija
results = optimize_batch("./input", "./output", rules, detailed=True)
print(f"Prosječna redukcija: {results['avg_reduction']}%")
```

## 📊 Primjer Rezultata

```
⚙️ Optimizacija: song.mid
==================================================

✅ Optimizacija uspješna!
   Izlazni fajl: song_optimized.mid
   Redukcija: 15.5%

📊 Detaljna statistika:
   Originalno:
      - Nota: 1250
      - CC eventa: 340
      - Trackova: 8
   Nakon optimizacije:
      - Nota: 1080
      - CC eventa: 295
      - Trackova: 8
```

## 🎯 Zašto Koristiti?

1. **Manja veličina fajlova** - Do 20-30% redukcije
2. **Čišći MIDI** - Bez redundantnih event-a
3. **Kompatibilnost** - Radi na svim Korg modelima
4. **Očuvani style markeri** - INTRO/VAR/FILL/BREAK/ENDING ostaju netaknuti
5. **Fleksibilnost** - Custom pravila za specifične potrebe

## 📝 Napomene

- Aplikacija ne mijenja originalne fajlove osim ako ne specificirate `--output`
- Style markeri su kritični za Korg style-ove i uvijek se očuvavaju
- Esencijalni CC-evi (volume, expression, sustain) se nikada ne uklanjaju

## 🤝 Doprinos

Slobodno dodajte nove testove ili poboljšanja pravila optimizacije!
