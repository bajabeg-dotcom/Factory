"""
Korg MIDI Optimizer - Main CLI Application
Komandna linija za analizu i optimizaciju MIDI fajlova
"""

import os
import sys
import json
import argparse
from datetime import datetime

from rxoptimizer.dna_analyzer import analyze_dna, DNAAnalyzer
from rxoptimizer.optimizer import optimize, KorgOptimizer


def cmd_analyze(args):
    """Komanda za DNA analizu"""
    print(f"🔍 Analiziram DNA iz: {args.directory}")
    
    if not os.path.exists(args.directory):
        print(f"❌ Greška: Direktorijum ne postoji: {args.directory}")
        return 1
    
    recursive = not args.no_recursive
    results = analyze_dna(args.directory, args.output, recursive=recursive)
    
    if results['files_analyzed'] == 0:
        print("⚠️  Nije pronađen nijedan MIDI fajl!")
        return 1
    
    summary = results['summary']
    
    print(f"\n{'='*60}")
    print("📊 REZULTATI ANALIZE")
    print(f"{'='*60}")
    print(f"✅ Fajlova analizirano: {results['files_analyzed']}")
    print(f"📝 Ukupno track-ova: {summary.get('total_tracks', 'N/A')}")
    print(f"🎵 Najčešći TPQ: {summary.get('most_common_tpq', 'N/A')}")
    print(f"🎹 Korišćeni kanali: {summary.get('channels_used', [])}")
    
    if summary.get('velocity_stats'):
        print(f"\n📈 Velocity Distribucija:")
        for range_name, percentage in summary['velocity_stats'].items():
            print(f"   {range_name}: {percentage}%")
    
    if summary.get('top_ccs'):
        print(f"\n🎛️  Top 5 CC Kontrolera:")
        for cc_info in summary['top_ccs'][:5]:
            print(f"   CC{cc_info['cc']}: {cc_info['count']} puta")
    
    if summary.get('marker_distribution'):
        print(f"\n🏷️  Style Markeri:")
        for marker_type, count in summary['marker_distribution'].items():
            print(f"   {marker_type}: {count}")
    
    if args.output:
        print(f"\n💾 Pravila eksportovana u: {args.output}")
    
    print(f"\n📋 Preporučena pravila:")
    for rule in summary.get('recommended_rules', []):
        print(f"   ✓ {rule['description']}")
    
    return 0


def cmd_optimize(args):
    """Komanda za optimizaciju pojedinačnog fajla"""
    print(f"⚙️  Optimizujem: {args.input}")
    
    if not os.path.exists(args.input):
        print(f"❌ Greška: Fajl ne postoji: {args.input}")
        return 1
    
    # Učitaj pravila ako su navedena
    rules = None
    if args.rules and os.path.exists(args.rules):
        with open(args.rules, 'r') as f:
            rules_config = json.load(f)
            rules = rules_config.get('optimization_rules')
        print(f"📋 Učitana pravila iz: {args.rules}")
    
    # Odredi izlazni fajl
    output_file = args.output
    if not output_file:
        base, ext = os.path.splitext(args.input)
        output_file = f"{base}_optimized{ext}"
    
    result = optimize(args.input, output_file, rules=rules, detailed=args.detailed)
    
    if 'error' in result:
        print(f"❌ GREŠKA: {result['error']}")
        return 1
    
    print(f"\n{'='*60}")
    print("✅ OPTIMIZACIJA USPEŠNA")
    print(f"{'='*60}")
    print(f"📁 Izlazni fajl: {result['output_file']}")
    print(f"📉 Smanjenje veličine: {result['size_reduction_percent']}%")
    print(f"⏱️  Smanjenje tick-ova: {result['tick_reduction_percent']}%")
    
    print(f"\n📊 Statistika:")
    for key, value in result['statistics'].items():
        readable_key = key.replace('_', ' ').title()
        print(f"   {readable_key}: {value}")
    
    if args.detailed:
        print(f"\n🛡️  Zaštićeni elementi:")
        print(f"   Esencijalni CC-evi: {result.get('essential_ccs_preserved', [])}")
        print(f"   Style markeri: {len(result.get('style_markers_protected', []))} tipova")
    
    return 0


def cmd_batch(args):
    """Komanda za batch optimizaciju"""
    print(f"🔄 Batch optimizacija...")
    print(f"📂 Ulaz: {args.input_dir}")
    print(f"📂 Izlaz: {args.output_dir}")
    
    if not os.path.exists(args.input_dir):
        print(f"❌ Greška: Direktorijum ne postoji: {args.input_dir}")
        return 1
    
    # Kreiraj izlazni direktorijum ako ne postoji
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)
        print(f"📁 Kreiran izlazni direktorijum: {args.output_dir}")
    
    # Učitaj pravila ako su navedena
    rules = None
    if args.rules and os.path.exists(args.rules):
        with open(args.rules, 'r') as f:
            rules_config = json.load(f)
            rules = rules_config.get('optimization_rules')
        print(f"📋 Učitana pravila iz: {args.rules}")
    
    # Pronađi sve MIDI fajlove
    midi_files = []
    for root, dirs, files in os.walk(args.input_dir):
        for file in files:
            if file.lower().endswith(('.mid', '.midi')):
                midi_files.append(os.path.join(root, file))
    
    if not midi_files:
        print("⚠️  Nije pronađen nijedan MIDI fajl!")
        return 1
    
    print(f"🎯 Pronađeno {len(midi_files)} fajlova za optimizaciju\n")
    
    # Optimizuj svaki fajl
    successful = 0
    failed = 0
    total_size_saved = 0
    
    for i, input_file in enumerate(midi_files, 1):
        filename = os.path.basename(input_file)
        print(f"[{i}/{len(midi_files)}] Optimizujem: {filename}", end=" ")
        
        # Odredi izlaznu putanju (očuvaj strukturu foldera)
        rel_path = os.path.relpath(input_file, args.input_dir)
        output_file = os.path.join(args.output_dir, rel_path)
        
        # Kreiraj podfoldere ako je potrebno
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        try:
            result = optimize(input_file, output_file, rules=rules, detailed=False)
            
            if 'error' in result:
                print(f"❌ GREŠKA: {result['error']}")
                failed += 1
            else:
                print(f"✅ ({result['size_reduction_percent']}%)")
                successful += 1
                original_size = result['original_size_bytes']
                new_size = result['optimized_size_bytes']
                total_size_saved += (original_size - new_size)
                
        except Exception as e:
            print(f"❌ EXCEPTION: {str(e)}")
            failed += 1
    
    # Finalni izveštaj
    print(f"\n{'='*60}")
    print("📊 BATCH IZVEŠTAJ")
    print(f"{'='*60}")
    print(f"✅ Uspešno: {successful}")
    print(f"❌ Neuspešno: {failed}")
    print(f"💾 Ukupno ušteđeno: {total_size_saved:,} bajtova ({total_size_saved/1024:.2f} KB)")
    
    return 0 if failed == 0 else 1


def main():
    parser = argparse.ArgumentParser(
        description='Korg MIDI Optimizer - Optimizacija MIDI fajlova za Korg tastature',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Primeri upotrebe:
  %(prog)s analyze ./data/gold --output rules.json
  %(prog)s optimize song.mid -o song_optimized.mid --detailed
  %(prog)s batch ./input ./output --rules rules.json
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Dostupne komande')
    
    # Analyze komanda
    analyze_parser = subparsers.add_parser('analyze', help='Analiziraj DNA iz Factory/Gold stilova')
    analyze_parser.add_argument('directory', help='Direktorijum sa MIDI fajlovima za analizu')
    analyze_parser.add_argument('-o', '--output', help='Izlazni JSON fajl za pravila')
    analyze_parser.add_argument('--no-recursive', action='store_true', 
                               help='Ne traži fajlove rekurzivno')
    analyze_parser.set_defaults(func=cmd_analyze)
    
    # Optimize komanda
    optimize_parser = subparsers.add_parser('optimize', help='Optimizuj pojedinačni MIDI fajl')
    optimize_parser.add_argument('input', help='Ulazni MIDI fajl')
    optimize_parser.add_argument('-o', '--output', help='Izlazni MIDI fajl')
    optimize_parser.add_argument('-r', '--rules', help='JSON fajl sa pravilima')
    optimize_parser.add_argument('--detailed', action='store_true', 
                                help='Prikaži detaljan izveštaj')
    optimize_parser.set_defaults(func=cmd_optimize)
    
    # Batch komanda
    batch_parser = subparsers.add_parser('batch', help='Batch optimizacija više fajlova')
    batch_parser.add_argument('input_dir', help='Ulazni direktorijum')
    batch_parser.add_argument('output_dir', help='Izlazni direktorijum')
    batch_parser.add_argument('-r', '--rules', help='JSON fajl sa pravilima')
    batch_parser.set_defaults(func=cmd_batch)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
