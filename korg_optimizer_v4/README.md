# Korg MIDI Optimizer v2.0

Napredni alat za optimizaciju MIDI fajlova specifično dizajniran za **Korg tastature** (Pa4X, Pa5X, Kronos, itd.).

## 🚀 Šta radi ovaj alat?

Analizira Factory Styles i Gold DNA pattern-e da bi kreirao pametna pravila za optimizaciju MIDI fajlova koja:

- ✅ **Uklanjaju redundantne podatke** - duplikati nota, zero-velocity note
- ✅ **Čiste Control Change poruke** - zadržava samo bitne CC-ove (1, 7, 10, 11, 64, 91, 93)
- ✅ **Popravljaju preklapanja nota** - sprečava "bljuzgavi" zvuk
- ✅ **Kvantizuju bubnjeve** - strogi quantization na kanalu 10 za čvrst ritam
- ✅ **Standardizuju TPQ** - konvertuje sve na 480 TPQ za maksimalnu kompatibilnost
- ✅ **Čuvaju Style Markere** - INTRO, VAR, FILL, BREAK, ENDING ostaju netaknuti
- ✅ **Štite NTT podatke** - Note Transpose Table parametri se ne diraju

## 📦 Instalacija (Windows)

### Brza instalacija:
1. Otvori komandnu liniju u ovom folderu
2. Pokreni: `install.bat`
3. Sačekaj da se instalacija završi

### Ručna instalacija:
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## 🎯 Upotreba

### Preko run.bat (preporučeno za Windows):

#### 1. Analiza DNA (Factory Styles / Gold)
```batch
run.bat analyze ./data/gold --output rules.json
```

#### 2. Optimizacija pojedinačnog fajla
```batch
run.bat optimize song.mid -o song_optimized.mid --detailed
```

#### 3. Batch optimizacija (više fajlova odjednom)
```batch
run.bat batch ./input ./output --rules rules.json
```

#### 4. Pokretanje testova
```batch
run.bat test
```

### Preko Python komandne linije:

```bash
# Aktiviraj virtualno okruženje prvo
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Analiza
python main.py analyze ./data/gold -o rules.json

# Optimizacija
python main.py optimize input.mid -o output.mid --detailed

# Batch
python main.py batch ./input ./output -r rules.json

# Testovi
python -m pytest tests/ -v
```

## 📊 Primer izveštaja o analizi

```
============================================================
📊 REZULTATI ANALIZE
============================================================
✅ Fajlova analizirano: 150
📝 Ukupno track-ova: 1200
🎵 Najčešći TPQ: 480
🎹 Korišćeni kanali: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]

📈 Velocity Distribucija:
   very_soft (0-30): 5.2%
   soft (31-60): 22.8%
   medium (61-90): 45.3%
   loud (91-120): 24.1%
   very_loud (121-127): 2.6%

🎛️ Top 5 CC Kontrolera:
   CC7: 4500 puta
   CC1: 3200 puta
   CC10: 2800 puta
   CC11: 2100 puta
   CC64: 1900 puta

🏷️ Style Markeri:
   Intro: 150
   Variation: 600
   Fill: 300
   Break: 150
   Ending: 150

📋 Preporučena pravila:
   ✓ Sačuvaj kritične CC kontrolere
   ✓ Obavezno sačuvaj sve style markere
   ✓ Ukloni note sa velocity 0
   ✓ Strogi quantization za bubnjeve (kanal 10)
```

## 📋 Pravila optimizacije

### Automatski generisana pravila:
1. **preserve_essential_ccs** - Čuva CC 1, 7, 10, 11, 64, 91, 93
2. **preserve_style_markers** - Štiti sve Korg style markere
3. **remove_zero_velocity** - Briše note sa velocity 0
4. **quantize_drums_strict** - Strogi 16th-note quantization za bubnjeve

### Dodatna poboljšanja:
- **Smart Quantization** - Melodije zadržavaju human feel, bubnjevi su strogo na mreži
- **Overlap Fix** - Automatski skraćuje note koje se preklapaju
- **TPQ Standardization** - Sve konvertuje na 480 TPQ
- **Duplicate Removal** - Uklanja identične note na istom vremenu
- **CC Compression** - Briše redundantne CC poruke (isti CC, ista vrednost)

## 🧪 Testovi

Svi testovi prolaze (15/15):
- ✅ DNA analiza osnovnih podataka
- ✅ Detekcija style markera
- ✅ Praćenje CC frekvencije
- ✅ Analiza direktorijuma
- ✅ Generisanje pravila
- ✅ Uklanjanje zero-velocity nota
- ✅ Uklanjanje duplikata
- ✅ Očuvanje style markera
- ✅ Očuvanje esencijalnih CC-eva
- ✅ TPQ standardizacija
- ✅ Smanjenje veličine fajla
- ✅ Quantization bubnjeva
- ✅ Kompletan workflow (analiza → pravila → optimizacija)

Pokreni testove:
```batch
run.bat test
```

## 📁 Struktura projekta

```
korg_optimizer_v4/
├── rxoptimizer/
│   ├── __init__.py          # Package inicijalizacija
│   ├── dna_analyzer.py      # DNA analiza Factory/Gold stilova
│   └── optimizer.py         # Glavni optimizer sa svim pravilima
├── tests/
│   └── test_optimizer.py    # 15 testova koji pokrivaju sve funkcije
├── data/
│   ├── input/               # Ulazni MIDI fajlovi
│   └── output/              # Optimizovani output
├── logs/                    # Log fajlovi (ako se dodaju)
├── main.py                  # CLI aplikacija
├── requirements.txt         # Python zavisnosti
├── install.bat              # Windows instalacioni skript
├── run.bat                  # Windows pokretački skript
└── README.md                # Ova dokumentacija
```

## 🔧 Programski API

Možeš koristiti module direktno u svom Python kodu:

```python
from rxoptimizer import analyze_dna, optimize

# 1. Analiza DNA
results = analyze_dna('./data/gold', output_file='rules.json')
print(f"Analizirano fajlova: {results['files_analyzed']}")

# 2. Optimizacija
report = optimize('input.mid', 'output.mid', detailed=True)
print(f"Smanjenje: {report['size_reduction_percent']}%")
print(f"Očišćeno duplikata: {report['statistics']['duplicates_removed']}")
```

## ⚠️ Napomene

- **Uvek napravi backup** originalnih fajlova pre optimizacije!
- Tool je dizajniran za Korg stilove, ali radi i sa drugim MIDI fajlovima
- Style markeri su kritični za rad stilova na Korg tastaturama - oni se nikada ne brišu
- Kanal 10 (index 9) se tretira kao bubnjevi i dobija stroži quantization

## 🆘 Rešavanje problema

### "Python nije pronađen"
Instaliraj Python 3.8+ sa https://www.python.org/downloads/

### "ModuleNotFoundError: No module named 'mido'"
Pokreni `install.bat` ili ručno: `pip install mido`

### "ImportError: cannot import name 'optimize'"
Proveri da li si u virtualnom okruženju i da li je `rxoptimizer` folder u PATH-u

### Optimizovani fajl ne radi na tastaturi
Proveri da li su style markeri očuvani (`--detailed` flag pokaže šta je sačuvano)

## 📄 Licenca

Ovaj projekt je kreiran za ličnu i komercijalnu upotrebu.

## 🤝 Doprinos

Ako nađeš bug ili imaš predlog za poboljšanje, slobodno otvori issue ili napravi pull request!

---

**Napomena:** Ovaj tool ne menja muzički sadržaj, već samo tehnički optimizuje MIDI podatke za bolje performanse na Korg uređajima.
