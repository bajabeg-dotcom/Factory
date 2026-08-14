"""
Korg MIDI Optimizer - CLI Application
"""

import argparse
import json
import sys
import os

from rxoptimizer.dna_analyzer import analyze_dna
from rxoptimizer.optimizer import optimize, optimize_batch


def cmd_analyze(args):
    """Analiziraj DNA iz Factory Styles ili Gold foldera"""
    print(f"Analiziram DNA iz: {args.directory}")
    
    results = analyze_dna(args.directory, args.output)
    
    if 'error' in results:
        print(f"GREŠKA: {results['error']}")
        return 1
    
    print(f"\n=== DNA Analiza ===")
    print(f"Ukupno fajlova: {results['total_files']}")
    print(f"Analizirano: {results['analyzed_files']}")
    print(f"Neuspjelo: {results['failed_files']}")
    
    rules = results.get('dna_rules', {})
    
    if rules.get('velocity_profile'):
        vp = rules['velocity_profile']
        print(f"\nVelocity Profil:")
        print(f"  Min: {vp['min']}, Max: {vp['max']}, Avg: {vp['avg']}")
    
    if rules.get('note_density'):
        nd = rules['note_density']
        print(f"\nGustina Nota:")
        print(f"  Min: {nd['min']}, Max: {nd['max']}, Avg: {nd['avg']}")
    
    if rules.get('common_cc'):
        print(f"\nNajčešći CC: {rules['common_cc'][:10]}")
    
    if args.output:
        print(f"\nPravila sačuvana u: {args.output}")
    
    return 0


def cmd_optimize(args):
    """Optimizuj pojedinačni MIDI fajl"""
    print(f"Optimizujem: {args.input}")
    
    # Učitaj pravila ako su navedena
    rules = None
    if args.rules and os.path.exists(args.rules):
        with open(args.rules, 'r', encoding='utf-8') as f:
            rules = json.load(f)
        print(f"Koristim pravila iz: {args.rules}")
    
    result = optimize(args.input, args.output, rules, args.detailed)
    
    if 'error' in result:
        print(f"GREŠKA: {result['error']}")
        return 1
    
    print(f"\n=== Rezultati Optimizacije ===")
    print(f"Ulaz: {result['input_file']}")
    print(f"Izlaz: {result['output_file']}")
    
    orig = result.get('original_stats', {})
    final = result.get('final_stats', {})
    
    print(f"\nStatistika:")
    print(f"  Note: {orig.get('notes', 0)} -> {final.get('notes', 0)}")
    print(f"  CC Eventi: {orig.get('cc_events', 0)} -> {final.get('cc_events', 0)}")
    print(f"  Trackovi: {orig.get('tracks', 0)} -> {final.get('tracks', 0)}")
    print(f"  Markeri: {orig.get('markers', 0)} -> {final.get('markers', 0)}")
    
    reduction = result.get('reduction_percentage', 0)
    print(f"\nRedukcija: {reduction}%")
    
    if args.detailed:
        opt_stats = result.get('optimization_stats', {})
        print(f"\nDetalji:")
        print(f"  Uklonjeno nota: {opt_stats.get('notes_removed', 0)}")
        print(f"  Uklonjeno CC: {opt_stats.get('cc_removed', 0)}")
        print(f"  Sačuvano markera: {opt_stats.get('markers_preserved', 0)}")
    
    return 0


def cmd_batch(args):
    """Optimizuj batch MIDI fajlova"""
    print(f"Batch optimizacija: {args.input_dir} -> {args.output_dir}")
    
    # Učitaj pravila ako su navedena
    rules = None
    if args.rules and os.path.exists(args.rules):
        with open(args.rules, 'r', encoding='utf-8') as f:
            rules = json.load(f)
        print(f"Koristim pravila iz: {args.rules}")
    
    results = optimize_batch(args.input_dir, args.output_dir, rules, args.detailed)
    
    if 'error' in results:
        print(f"GREŠKA: {results['error']}")
        return 1
    
    print(f"\n=== Batch Rezultati ===")
    print(f"Ukupno fajlova: {results['total_files']}")
    print(f"Uspješno: {results['successful']}")
    print(f"Neuspješno: {results['failed']}")
    
    if results.get('avg_reduction'):
        print(f"Prosječna redukcija: {results['avg_reduction']}%")
    
    if args.detailed:
        print(f"\n=== Detalji po Fajlu ===")
        for file_result in results.get('files', []):
            status = "OK" if 'reduction' in file_result else "FAIL"
            value = file_result.get('reduction', file_result.get('error', 'N/A'))
            print(f"  [{status}] {file_result['filename']}: {value}")
    
    return 0


def main():
    parser = argparse.ArgumentParser(
        description='Korg MIDI Optimizer - Optimizacija MIDI fajlova koristeći Factory Styles i Gold DNA'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Komande')
    
    # Analyze komanda
    analyze_parser = subparsers.add_parser('analyze', help='Analiziraj DNA iz foldera')
    analyze_parser.add_argument('directory', help='Direktorijum sa MIDI fajlovima')
    analyze_parser.add_argument('-o', '--output', help='Izlazni JSON fajl za pravila')
    analyze_parser.set_defaults(func=cmd_analyze)
    
    # Optimize komanda
    optimize_parser = subparsers.add_parser('optimize', help='Optimizuj MIDI fajl')
    optimize_parser.add_argument('input', help='Ulazni MIDI fajl')
    optimize_parser.add_argument('-o', '--output', help='Izlazni MIDI fajl')
    optimize_parser.add_argument('-r', '--rules', help='JSON fajl sa pravilima')
    optimize_parser.add_argument('-d', '--detailed', action='store_true', help='Detaljan izlaz')
    optimize_parser.set_defaults(func=cmd_optimize)
    
    # Batch komanda
    batch_parser = subparsers.add_parser('batch', help='Batch optimizacija')
    batch_parser.add_argument('input_dir', help='Direktorijum sa ulaznim fajlovima')
    batch_parser.add_argument('output_dir', help='Direktorijum za izlazne fajlove')
    batch_parser.add_argument('-r', '--rules', help='JSON fajl sa pravilima')
    batch_parser.add_argument('-d', '--detailed', action='store_true', help='Detaljan izlaz')
    batch_parser.set_defaults(func=cmd_batch)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
