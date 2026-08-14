"""
Korg MIDI Optimizer - CLI Aplikacija
Optimizacija MIDI fajlova na osnovu Factory Styles i Gold DNA pattern-a
"""

import argparse
import sys
import os
import json
from typing import Optional

# Dodaj root directory za import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rxoptimizer.dna_analyzer import analyze_dna, DNAAnalyzer
from rxoptimizer.optimizer import optimize, optimize_batch


def cmd_analyze(args):
    """Analiziraj DNA direktorijum"""
    print(f"\n🔍 Analiza DNA: {args.directory}")
    print("=" * 50)
    
    if not os.path.exists(args.directory):
        print(f"❌ Greška: Direktorijum ne postoji: {args.directory}")
        return 1
    
    rules = analyze_dna(args.directory)
    
    if 'error' in rules:
        print(f"❌ Greška: {rules['error']}")
        return 1
    
    print(f"\n📊 Statistika:")
    print(f"   Esencijalni CC: {rules.get('essential_cc', [])}")
    print(f"   Style markeri: {rules.get('style_markers', [])}")
    print(f"   Preporučeni kanali: {rules.get('recommended_channels', [])}")
    
    velocity = rules.get('velocity_threshold', {})
    if velocity:
        print(f"\n🎹 Velocity pragovi:")
        print(f"   Min: {velocity.get('min_recommended', 0)}")
        print(f"   Max: {velocity.get('max_recommended', 127)}")
        print(f"   Avg: {velocity.get('average', 0)}")
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(rules, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Pravila sačuvana u: {args.output}")
    
    return 0


def cmd_optimize(args):
    """Optimizuj pojedinačni MIDI fajl"""
    print(f"\n⚙️ Optimizacija: {args.input}")
    print("=" * 50)
    
    # Učitaj pravila ako su specificirana
    rules = None
    if args.rules:
        if os.path.exists(args.rules):
            with open(args.rules, 'r', encoding='utf-8') as f:
                rules = json.load(f)
            print(f"📋 Učitana pravila iz: {args.rules}")
        else:
            print(f"⚠️ Fajl sa pravilima ne postoji: {args.rules}")
    
    result = optimize(args.input, args.output, rules, args.detailed)
    
    if result.get('error'):
        print(f"❌ Greška: {result['error']}")
        return 1
    
    print(f"\n✅ Optimizacija uspješna!")
    print(f"   Izlazni fajl: {result['output_file']}")
    print(f"   Redukcija: {result['reduction_percentage']}%")
    
    if args.detailed:
        print(f"\n📊 Detaljna statistika:")
        orig = result.get('original_stats', {})
        final = result.get('final_stats', {})
        
        print(f"   Originalno:")
        print(f"      - Nota: {orig.get('notes', 0)}")
        print(f"      - CC eventa: {orig.get('cc_events', 0)}")
        print(f"      - Trackova: {orig.get('tracks', 0)}")
        
        print(f"   Nakon optimizacije:")
        print(f"      - Nota: {final.get('notes', 0)}")
        print(f"      - CC eventa: {final.get('cc_events', 0)}")
        print(f"      - Trackova: {final.get('tracks', 0)}")
    
    return 0


def cmd_batch(args):
    """Batch optimizacija direktorijuma"""
    print(f"\n🔄 Batch optimizacija")
    print("=" * 50)
    print(f"   Ulaz: {args.input_dir}")
    print(f"   Izlaz: {args.output_dir}")
    
    # Učitaj pravila ako su specificirana
    rules = None
    if args.rules:
        if os.path.exists(args.rules):
            with open(args.rules, 'r', encoding='utf-8') as f:
                rules = json.load(f)
            print(f"📋 Učitana pravila iz: {args.rules}")
    
    result = optimize_batch(args.input_dir, args.output_dir, rules, args.detailed)
    
    if result.get('error'):
        print(f"❌ Greška: {result['error']}")
        return 1
    
    print(f"\n✅ Batch optimizacija završena!")
    print(f"   Ukupno fajlova: {result['total_files']}")
    print(f"   Uspješno: {result['successful']}")
    print(f"   Neuspješno: {result['failed']}")
    
    if result['successful'] > 0:
        print(f"   Prosječna redukcija: {result.get('avg_reduction', 0)}%")
    
    if args.detailed and result.get('files'):
        print(f"\n📊 Detalji po fajlovima:")
        for file_info in result['files']:
            filename = file_info.get('filename', 'unknown')
            if 'error' in file_info:
                print(f"   ❌ {filename}: {file_info['error']}")
            else:
                reduction = file_info.get('reduction', 0)
                print(f"   ✅ {filename}: {reduction}%")
    
    return 0


def main():
    parser = argparse.ArgumentParser(
        description='Korg MIDI Optimizer - Optimizacija MIDI fajlova na osnovu Factory Styles i Gold DNA',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Primjeri upotrebe:
  %(prog)s analyze ./data/gold --output rules.json
  %(prog)s optimize input.mid --output output.mid
  %(prog)s batch ./input ./output --detailed
  %(prog)s optimize input.mid --rules rules.json --detailed
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Dostupne komande')
    
    # Analyze komanda
    analyze_parser = subparsers.add_parser('analyze', help='Analiziraj DNA i generiši pravila')
    analyze_parser.add_argument('directory', help='Direktorijum sa DNA MIDI fajlovima')
    analyze_parser.add_argument('--output', '-o', help='Izlazni JSON fajl za pravila')
    analyze_parser.set_defaults(func=cmd_analyze)
    
    # Optimize komanda
    optimize_parser = subparsers.add_parser('optimize', help='Optimizuj pojedinačni MIDI fajl')
    optimize_parser.add_argument('input', help='Ulazni MIDI fajl')
    optimize_parser.add_argument('--output', '-o', help='Izlazni MIDI fajl (default: inplace)')
    optimize_parser.add_argument('--rules', '-r', help='JSON fajl sa pravilima')
    optimize_parser.add_argument('--detailed', '-d', action='store_true', help='Prikaži detaljnu statistiku')
    optimize_parser.set_defaults(func=cmd_optimize)
    
    # Batch komanda
    batch_parser = subparsers.add_parser('batch', help='Batch optimizacija direktorijuma')
    batch_parser.add_argument('input_dir', help='Direktorijum sa ulaznim MIDI fajlovima')
    batch_parser.add_argument('output_dir', help='Direktorijum za izlazne MIDI fajlove')
    batch_parser.add_argument('--rules', '-r', help='JSON fajl sa pravilima')
    batch_parser.add_argument('--detailed', '-d', action='store_true', help='Prikaži detalje po fajlovima')
    batch_parser.set_defaults(func=cmd_batch)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
