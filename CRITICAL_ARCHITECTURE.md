# KRUCIJALNA ARHITEKTURA - INSTRUMENT PROFILI I TRANSFORMACIJE

## 1. STRUKTURA PROFILA (NOVI MODEL)

Svaki instrument profil mora imati **PET KLJUČNIH KOMPONENTI**:

```python
@dataclass
class InstrumentProfile:
    # 1. APSOLUTNE GRANICE (nikad ne preći - fizička ograničenja instrumenta)
    velocity_abs_min: int      # npr. Finger Bass: 30
    velocity_abs_max: int      # npr. Finger Bass: 95
    key_abs_min: int           # npr. Finger Bass: 28 (E1)
    key_abs_max: int           # npr. Finger Bass: 60 (C4)
    
    # 2. RADNI OPSEG (95% normalne svirke - za transformaciju)
    velocity_work_min: int     # npr. 45
    velocity_work_max: int     # npr. 85
    key_work_min: int          # npr. 33 (F#1)
    key_work_max: int          # npr. 55 (G3)
    
    # 3. STATISTIKA (iz Factory/Gold baza - za matematičku transformaciju)
    velocity_mean: float       # npr. 67.3
    velocity_std: float        # npr. 12.4
    key_mean: float            # npr. 42.1
    key_std: float             # npr. 8.7
    
    # 4. TIP INSTRUMENTA (određuje pravila transformacije)
    instrument_type: Literal["bass", "guitar", "strings", "lead", "drums", "keys"]
    
    # 5. RX/DNC METADATA (ako postoji)
    rx_name: str | None
    dnc_articulations: list[str]
```

### PRIMJER ZA FINGER BASS:
```json
{
  "bank_msb": 0,
  "bank_lsb": 0,
  "program": 32,
  "name": "Finger Bass",
  "velocity_abs_min": 30,
  "velocity_abs_max": 95,
  "velocity_work_min": 45,
  "velocity_work_max": 85,
  "velocity_mean": 67.3,
  "velocity_std": 12.4,
  "key_abs_min": 28,
  "key_abs_max": 60,
  "key_work_min": 33,
  "key_work_max": 55,
  "instrument_type": "bass"
}
```

---

## 2. MATEMATIČKA TRANSFORMACIJA VELOCITY-A

### PROBLEM TRENUTNOG SISTEMA:
Trenutna formula koristi SAMO prosjek i standardnu devijaciju, ali **ne poštuje granice**:

```python
# TRENUTNO (POGREŠNO):
gold_v = target_mean + (original - source_mean) * target_std / source_std
final = original * (1 - strength) + gold_v * strength
# Problem: final može biti 120+ za bass što uništava sound!
```

### NOVA FORMULA (SA ZAŠTITOM):

```python
def transform_velocity(
    original: int,
    source_mean: float,
    source_std: float,
    target_profile: InstrumentProfile,
    strength: float
) -> int:
    # KORAK 1: Normalizuj input u Z-score
    z_score = (original - source_mean) / max(1.0, source_std)
    
    # KORAK 2: Mapiraj u RADNI OPSEG cilja (ne apsolutni!)
    target_work_mean = (target_profile.velocity_work_min + target_profile.velocity_work_max) / 2
    target_work_std = (target_profile.velocity_work_max - target_profile.velocity_work_min) / 4  # 95% unutar 2 std
    
    desired = target_work_mean + z_score * target_work_std
    
    # KORAK 3: Interpoliraj sa originalom (strength kontrola)
    blended = original * (1 - strength) + desired * strength
    
    # KORAK 4: TVRD OGRANIČENJE na apsolutne granice (NIKAD ne preći!)
    clamped = max(
        target_profile.velocity_abs_min,
        min(target_profile.velocity_abs_max, round(blended))
    )
    
    return clamped
```

### ZAŠTO OVO RADI:
1. **Z-score** čuva relativnu dinamiku tvoje svirke
2. **Radni opseg** osigurava da 95% nota ostane u "slatkoj zoni" instrumenta
3. **Apsolutne granice** sprječavaju da bass note idu na 120+ (što aktivira slap sampleove!)
4. **Strength** daje kontrolu koliko Gold DNA utiče

---

## 3. TRANSFORMACIJA KEY RANGE-A (TRANSPOZICIJA, NE BRISANJE)

### PROBLEM TRENUTNOG SISTEMA:
Ako nota izađe iz opsega, sistem je možda briše ili ignoriše.

### NOVI PRISTUP (OKTAVNO POMJERANJE):

```python
def transform_note_range(
    original_note: int,
    target_profile: InstrumentProfile
) -> int:
    note = original_note
    
    # Dok je nota van apsolutnog opsega, pomjeraj za oktave
    while note > target_profile.key_abs_max:
        note -= 12  # Spusti za oktavu
    
    while note < target_profile.key_abs_min:
        note += 12  # Podigni za oktavu
    
    # Dodatna zaštita: ako je i dalje van radnog opsega, blago pomjeri
    if note > target_profile.key_work_max:
        note = target_profile.key_work_max
    elif note < target_profile.key_work_min:
        note = target_profile.key_work_min
    
    return note
```

### PRIMJER:
- **Input**: C5 (note 72)
- **Finger Bass opseg**: 28-60
- **Rezultat**: C3 (note 48) - automatski transponovano za 2 oktave niže!
- **Nije obrisano**, već **muzikalno prilagođeno**.

---

## 4. GLAVNI PROBLEM: PRIMJENA POGREŠNOG PROFILA

### DIJAGNOZA:

U `optimizer.py`, linije 136-175, sistem radi ovo:

```python
# TRENUTNA LOGIKA (PROBLEMATIČNA):
key = (*banks[ch], program, role)
target = index.get(key)  # Traži mapping

if target:
    # Primjeni RX mapping
    event.data1 = int(target["target_program"])
    # ... dodaje Bank Select poruke
```

**PROBLEM**: Ako `role` nije ispravno detektovan, ili ako mapping ne postoji, sistem:
1. Koristi fallback na "melodic"
2. Može primijeniti profil za Piano na Bass track!
3. Ne provjerava da li je `target` kompatibilan sa originalnim instrumentom

### RJEŠENJE (STROGA VALIDACIJA):

```python
def safe_apply_mapping(event, banks, ch, program, assignments, index, profiles_db):
    role = assignments.get((track_index, ch), {}).get("role") or _role(ch, program)
    
    # KORAK 1: Traži exact match
    key = (*banks[ch], program, role)
    target = index.get(key)
    
    # KORAK 2: Ako nema matcha, probaj sa "melodic" fallback ALI samo za melodic instrumente
    if not target and role in ("bass", "guitar"):
        # NIKAD ne fallback-uj bass na melodic profile!
        target = None  # Ostani bez mappinga umjesto pogrešnog
    
    # KORAK 3: Provjeri kompatibilnost prije primjene
    if target:
        source_identity = get_identity(program, role)
        target_identity = get_identity(target["target_program"], target.get("role"))
        
        if not identities_compatible(source_identity, target_identity):
            # ODBACI MAPPING ako su instrumenti nekompatibilni
            log_rejection(...)
            target = None
    
    # KORAK 4: Ako još uvijek nema targeta, koristi preporuku iz intelligence
    if not target and assign_unknown_sounds:
        recommendation = get_recommendation_for_unknown(banks[ch], program, role)
        if recommendation and recommendation.compatible:
            target = recommendation
    
    return target
```

### KLJUČNA PRAVILA:
1. **Bass nikad ne koristi Melodic profile**
2. **Gitara nikad ne koristi Drum profile**
3. **Ako mapping nije 100% siguran, bolje ga ne primijeniti**
4. **Uvijek provjeri kompatibilnost prije zamjene**

---

## 5. IMPLEMENTACIJSKI PLAN

### FAZA 1: Ažuriraj `database.py`
- Dodaj kolone u `instrument_profiles` tabelu:
  - `velocity_abs_min`, `velocity_abs_max`
  - `velocity_work_min`, `velocity_work_max`
  - `key_abs_min`, `key_abs_max`
  - `key_work_min`, `key_work_max`
  - `instrument_type`

### FAZA 2: Ažuriraj `features.py`
- Modifikuj `GoldDNAModel.fit()` da računa ove vrijednosti iz podataka
- Implementiraj `transform_velocity()` sa zaštitom granica
- Implementiraj `transform_note_range()` sa transpozicijom

### FAZA 3: Ažuriraj `optimizer.py`
- Zamijeni pozive `_factory_instrument_velocity()` sa novom funkcijom
- Dodaj validaciju prije primjene mappinga
- Implementiraj strogu provjeru kompatibilnosti

### FAZA 4: Testiranje
- Napravi testove za granične slučajeve (velocity 1, 127, note 0, 127)
- Testiraj fallback logiku (šta se dešava kad nema mappinga)
- Validiraj da bass nikad ne prelazi 95 velocity

---

## 6. PRIORITETI

1. **VISOK**: Sigurnosne granice za velocity (bass ne smije ići preko 95)
2. **VISOK**: Kompatibilnost mappinga (ne primjenjuj piano profil na bass)
3. **SREDNJI**: Key range transpozicija (umjesto brisanja)
4. **NIZAK**: Statistička poboljšanja (bolji Z-score proračuni)

---

## 7. PROVJERA ISPRAVNOSTI

Nakon implementacije, pokreni ove testove:

```bash
# Test 1: Bass velocity nikad ne prelazi 95
python -c "from rxoptimizer.optimizer import optimize; ..."

# Test 2: Note van opsega su transponovane, ne obrisane
python -c "..."

# Test 3: Pogrešan mapping je odbačen
python -c "..."
```

---

**NAPOMENA**: Ovaj dokument je **jedini izvor istine** za buduću implementaciju. Svaki kod koji odudara od ovih pravila mora biti označen kao `NOT PROVEN`.
