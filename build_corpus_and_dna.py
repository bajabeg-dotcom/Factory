#!/usr/bin/env python3
"""
BUILD CORPUS & DNA - Automatski proces za:
1. Kreiranje Factory/Gold Corpus baza
2. Import svih MIDI fajlova
3. Build DNA baza (Rhythm, RX, DNC, Instrument)
"""

import sys
from pathlib import Path
from datetime import datetime

# Dodaj workspace u path
sys.path.insert(0, str(Path(__file__).parent))

from rxoptimizer import database, dna_databases
from rxoptimizer.midi import parse_midi
import json

def print_header(text: str):
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)

def print_status(step: str, status: str, details: str = ""):
    symbol = "✓" if status == "OK" else "✗" if status == "FAIL" else "…"
    print(f"[{symbol}] {step}: {status}")
    if details:
        print(f"    → {details}")

def main():
    start_time = datetime.now()
    print_header("BUILD CORPUS & DNA SYSTEM")
    print(f"Start: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    base_dir = Path(__file__).parent
    data_dir = base_dir / "data"
    corpus_dir = data_dir / "corpus"
    dna_dir = data_dir / "dna"
    gold_dir = base_dir / "gold_styles"
    factory_dir = base_dir / "factory_styles"
    uploads_dir = base_dir / "prism-uploads"
    
    # Kreiraj direktorije
    for d in [corpus_dir, dna_dir, gold_dir, factory_dir]:
        d.mkdir(parents=True, exist_ok=True)
    
    print_status("Directory structure", "OK", f"data/{corpus_dir.name}, data/{dna_dir.name}")
    
    # ============================================================
    # KORAK 1: KREIRAJ CORPUS BAZE
    # ============================================================
    print_header("KORAK 1: KREIRANJE CORPUS BAZA")
    
    try:
        db_path = corpus_dir / "corpus.sqlite3"
        db = database.connect(db_path)
        database.seed_rx_zones(db)
        database.seed_pa800_catalog(db)
        database.seed_default_gm_rx_mappings(db)
        print_status("Corpus database init", "OK", str(db_path))
        
        # Provjeri postojeće stanje
        stats_rows = database.rows(db, "SELECT COUNT(*) as cnt FROM midi_files WHERE style_name LIKE '%gold%'")
        gold_count = stats_rows[0]['cnt'] if stats_rows else 0
        
        stats_rows = database.rows(db, "SELECT COUNT(*) as cnt FROM midi_files WHERE style_name LIKE '%factory%'")
        factory_count = stats_rows[0]['cnt'] if stats_rows else 0
        
        print_status("Existing gold files", "INFO", str(gold_count))
        print_status("Existing factory files", "INFO", str(factory_count))
        
    except Exception as e:
        print_status("Corpus database init", "FAIL", str(e))
        import traceback
        traceback.print_exc()
        return 1
    
    # ============================================================
    # KORAK 2: IMPORT GOLD STILOVA
    # ============================================================
    print_header("KORAK 2: IMPORT GOLD STILOVA")
    
    gold_midi_files = list(gold_dir.glob("**/*.mid")) + list(gold_dir.glob("**/*.midi"))
    print_status("Gold MIDI files found", "INFO", str(len(gold_midi_files)))
    
    if gold_midi_files:
        success_count = 0
        fail_count = 0
        
        for midi_file in gold_midi_files:
            try:
                with open(midi_file, 'rb') as f:
                    midi = parse_midi(f.read())
                # Analiziraj i sačuvaj
                database.analyze_and_store(db, None, midi, "gold")
                success_count += 1
                if success_count <= 5:
                    print_status(f"  {midi_file.name}", "OK")
            except Exception as e:
                fail_count += 1
                if fail_count <= 5:
                    print_status(f"  {midi_file.name}", "FAIL", str(e)[:50])
        
        print_status("Gold import complete", "OK" if success_count > 0 else "FAIL", f"{success_count} uspešno, {fail_count} neuspešno")
    else:
        print_status("Gold import", "SKIP", "Nema .mid fajlova u gold_styles/")
        print(f"    → Kreiraj folder {gold_dir} i dodaj MIDI fajlove")
    
    # ============================================================
    # KORAK 3: IMPORT FACTORY STILOVA
    # ============================================================
    print_header("KORAK 3: IMPORT FACTORY STILOVA")
    
    factory_midi_files = list(factory_dir.glob("**/*.mid")) + list(factory_dir.glob("**/*.midi"))
    print_status("Factory MIDI files found", "INFO", str(len(factory_midi_files)))
    
    if factory_midi_files:
        success_count = 0
        fail_count = 0
        
        for midi_file in factory_midi_files:
            try:
                with open(midi_file, 'rb') as f:
                    midi = parse_midi(f.read())
                database.analyze_and_store(db, None, midi, "factory")
                success_count += 1
                if success_count <= 5:
                    print_status(f"  {midi_file.name}", "OK")
            except Exception as e:
                fail_count += 1
                if fail_count <= 5:
                    print_status(f"  {midi_file.name}", "FAIL", str(e)[:50])
        
        print_status("Factory import complete", "OK" if success_count > 0 else "FAIL", f"{success_count} uspešno, {fail_count} neuspešno")
    else:
        print_status("Factory import", "SKIP", "Nema .mid fajlova u factory_styles/")
        print(f"    → Kreiraj folder {factory_dir} i dodaj MIDI fajlove")
    
    # ============================================================
    # KORAK 4: PRIKAŽI STATISTIKU
    # ============================================================
    print_header("KORAK 4: CORPUS STATISTIKA")
    
    gold_rows = database.rows(db, "SELECT COUNT(*) as cnt FROM midi_files WHERE style_name LIKE '%gold%'")
    factory_rows = database.rows(db, "SELECT COUNT(*) as cnt FROM midi_files WHERE style_name LIKE '%factory%'")
    track_rows = database.rows(db, "SELECT COUNT(*) as cnt FROM track_stats")
    
    gold_count = gold_rows[0]['cnt'] if gold_rows else 0
    factory_count = factory_rows[0]['cnt'] if factory_rows else 0
    track_count = track_rows[0]['cnt'] if track_rows else 0
    
    print(f"  Gold files:      {gold_count}")
    print(f"  Factory files:   {factory_count}")
    print(f"  Total tracks:    {track_count}")
    
    # ============================================================
    # KORAK 5: BUILD DNA BAZA
    # ============================================================
    print_header("KORAK 5: BUILD DNA BAZA")
    
    try:
        builder_result = dna_databases.build_all(
            factory_path=factory_dir,
            gold_path=gold_dir,
            data_directory=dna_dir
        )
        print_status("DNA Builder init", "OK", str(dna_dir))
        
        # Pokreni build svih DNA baza
        results = builder_result
        
        print_status("Rhythm DNA", "OK" if results.get('rhythm') else "FAIL")
        print_status("RX DNA", "OK" if results.get('rx') else "FAIL")
        print_status("DNC DNA", "OK" if results.get('dnc') else "FAIL")
        print_status("Instrument DNA", "OK" if results.get('instrument') else "FAIL")
        print_status("Song DNA", "OK" if results.get('song') else "FAIL")
        print_status("Trill DNA", "OK" if results.get('trill') else "FAIL")
        
        # Prikaži detaljan status
        print("\nDetaljan DNA status:")
        status = dna_databases.dna_status(dna_dir)
        for key, value in status.items():
            exists = "✓" if value.get('exists', False) else "✗"
            size = value.get('size_mb', 0)
            print(f"  [{exists}] {key}: {size:.2f} MB")
        
    except Exception as e:
        print_status("DNA Build", "FAIL", str(e))
        import traceback
        traceback.print_exc()
    
    # ============================================================
    # ZAVRŠETAK
    # ============================================================
    end_time = datetime.now()
    duration = end_time - start_time
    
    print_header("ZAVRŠETAK")
    print(f"Start: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"End:   {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Duration: {duration}")
    
    print("\n✅ BUILD PROCES KOMPLETAN!")
    print("\nSledeći koraci:")
    print("  1. Pokreni: streamlit run app.py")
    print("  2. Idi na 'Optimize' tab")
    print("  3. Upload-uj MIDI fajlove")
    print("  4. Klikni 'Optimize'")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
