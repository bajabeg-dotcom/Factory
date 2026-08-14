#!/usr/bin/env python3
"""
Korg MIDI Optimizer - Main CLI Application

Optimizes MIDI files for Korg keyboards using DNA patterns from Factory Styles and Gold styles.

Usage:
    python main.py analyze <directory>     # Analyze MIDI files
    python main.py optimize <input_dir> <output_dir>  # Optimize MIDI files
    python main.py batch <input_dir> <output_dir>     # Full batch processing with analysis
"""

import sys
import os
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from dna_analyzer import DNAAnalyzer
from optimizer import MIDIOptimizer


def analyze_directory(directory: str, detailed: bool = False):
    """Analyze all MIDI files in a directory."""
    analyzer = DNAAnalyzer()
    path = Path(directory)
    
    print(f"Analyzing MIDI files in {directory}...")
    print("=" * 60)
    
    midi_files = list(path.rglob("*.mid")) + list(path.rglob("*.MID"))
    print(f"Found {len(midi_files)} MIDI files\n")
    
    if not midi_files:
        print("No MIDI files found!")
        return
    
    results = analyzer.analyze_directory(directory)
    
    # Summary statistics
    total_notes = 0
    total_tracks = 0
    total_files = 0
    style_markers_found = {}
    instruments_used = {}
    
    for result in results:
        if 'error' in result:
            print(f"Error analyzing {result.get('path', 'unknown')}: {result['error']}")
            continue
            
        total_files += 1
        total_notes += result.get('total_notes', 0)
        total_tracks += result.get('total_tracks', 0)
        
        for marker in result.get('style_markers', []):
            marker_type = marker['type']
            style_markers_found[marker_type] = style_markers_found.get(marker_type, 0) + 1
        
        for instrument in result.get('instruments', {}).values():
            instruments_used[instrument] = instruments_used.get(instrument, 0) + 1
    
    print(f"Files analyzed: {total_files}")
    print(f"Total tracks: {total_tracks}")
    print(f"Total notes: {total_notes}")
    
    if style_markers_found:
        print(f"\nStyle Markers Found:")
        for marker_type, count in sorted(style_markers_found.items()):
            print(f"  {marker_type}: {count}")
    
    if detailed and instruments_used:
        print(f"\nInstruments Used (top 10):")
        sorted_instruments = sorted(instruments_used.items(), key=lambda x: x[1], reverse=True)[:10]
        for instrument, count in sorted_instruments:
            print(f"  Program {instrument}: {count} tracks")
    
    print("\n" + "=" * 60)
    return results


def optimize_directory(input_dir: str, output_dir: str, rules: dict = None):
    """Optimize all MIDI files in a directory."""
    analyzer = DNAAnalyzer()
    optimizer = MIDIOptimizer(dna_analyzer=analyzer)
    
    # Apply custom rules if provided
    if rules:
        for rule_name, value in rules.items():
            optimizer.set_rule(rule_name, value)
    
    print(f"Optimizing MIDI files from {input_dir} to {output_dir}...")
    print("=" * 60)
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    results = optimizer.optimize_directory(input_dir, output_dir)
    stats = optimizer.get_stats()
    
    successful = sum(1 for r in results if 'error' not in r)
    errors = sum(1 for r in results if 'error' in r)
    
    print(f"\nResults:")
    print(f"  Files processed: {successful}")
    print(f"  Errors: {errors}")
    print(f"  Events removed: {stats['events_removed']}")
    print(f"  Notes removed: {stats['notes_removed']}")
    
    # Calculate average reduction
    total_original = sum(r.get('original_events', 0) for r in results if 'error' not in r)
    total_optimized = sum(r.get('optimized_events', 0) for r in results if 'error' not in r)
    if total_original > 0:
        reduction = ((total_original - total_optimized) / total_original) * 100
        print(f"  Average reduction: {reduction:.1f}%")
    
    print("\n" + "=" * 60)
    return results


def main():
    parser = argparse.ArgumentParser(
        description='Korg MIDI Optimizer - Optimize MIDI files for Korg keyboards',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py analyze ./my_midi_files
  python main.py optimize ./input ./output
  python main.py batch ./input ./output --detailed
  python main.py optimize ./input ./output --no-duplicates --no-cc-cleanup
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze MIDI files')
    analyze_parser.add_argument('directory', help='Directory containing MIDI files')
    analyze_parser.add_argument('--detailed', '-d', action='store_true', 
                               help='Show detailed instrument information')
    
    # Optimize command
    optimize_parser = subparsers.add_parser('optimize', help='Optimize MIDI files')
    optimize_parser.add_argument('input_dir', help='Input directory with MIDI files')
    optimize_parser.add_argument('output_dir', help='Output directory for optimized files')
    optimize_parser.add_argument('--no-duplicates', action='store_true',
                                help='Disable duplicate note removal')
    optimize_parser.add_argument('--no-cc-cleanup', action='store_true',
                                help='Disable control change cleanup')
    optimize_parser.add_argument('--no-zero-vel', action='store_true',
                                help='Disable zero-velocity note removal')
    
    # Batch command (analyze + optimize)
    batch_parser = subparsers.add_parser('batch', help='Full batch processing')
    batch_parser.add_argument('input_dir', help='Input directory with MIDI files')
    batch_parser.add_argument('output_dir', help='Output directory for optimized files')
    batch_parser.add_argument('--detailed', '-d', action='store_true',
                             help='Show detailed analysis')
    
    args = parser.parse_args()
    
    if args.command == 'analyze':
        analyze_directory(args.directory, args.detailed)
        
    elif args.command == 'optimize':
        rules = {}
        if args.no_duplicates:
            rules['remove_duplicate_notes'] = False
        if args.no_cc_cleanup:
            rules['clean_control_changes'] = False
        if args.no_zero_vel:
            rules['remove_zero_velocity_notes'] = False
        
        optimize_directory(args.input_dir, args.output_dir, rules)
        
    elif args.command == 'batch':
        print("Step 1: Analysis")
        print("=" * 60)
        analyze_directory(args.input_dir, args.detailed)
        
        print("\nStep 2: Optimization")
        print("=" * 60)
        optimize_directory(args.input_dir, args.output_dir)
        
    else:
        parser.print_help()
        print("\nPlease specify a command: analyze, optimize, or batch")
        sys.exit(1)


if __name__ == '__main__':
    main()
