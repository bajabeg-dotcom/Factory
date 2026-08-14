#!/usr/bin/env python3
"""
Korg MIDI Optimizer - Main Application

Optimizes MIDI files based on Factory Styles and Gold DNA patterns.
"""

import argparse
import os
import sys
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from dna_analyzer import MIDIDNAAnalyzer
from optimizer import KorgMIDIOptimizer, create_dna_profile_from_samples


def main():
    parser = argparse.ArgumentParser(
        description='Korg MIDI Optimizer - Optimize MIDI files using DNA-based rules'
    )
    
    parser.add_argument(
        'input',
        help='Input MIDI file or directory'
    )
    
    parser.add_argument(
        '-o', '--output',
        required=True,
        help='Output directory for optimized files'
    )
    
    parser.add_argument(
        '--gold-dna',
        help='Directory containing Gold DNA MIDI files for analysis'
    )
    
    parser.add_argument(
        '--factory-styles',
        help='Directory containing Factory Style MIDI files for analysis'
    )
    
    parser.add_argument(
        '--analyze-only',
        action='store_true',
        help='Only analyze files, do not optimize'
    )
    
    parser.add_argument(
        '--report',
        action='store_true',
        help='Generate detailed optimization report'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )
    
    args = parser.parse_args()
    
    # Create DNA profile if source directories provided
    dna_profile = {}
    if args.gold_dna and args.factory_styles:
        print("Creating DNA profile from Gold DNA and Factory Styles...")
        dna_profile = create_dna_profile_from_samples(args.gold_dna, args.factory_styles)
        
        if args.verbose:
            print(f"\nDNA Profile Summary:")
            print(f"  Gold DNA samples: {dna_profile['gold_dna_profile'].get('sample_count', 0)}")
            print(f"  Factory Style samples: {dna_profile['factory_style_profile'].get('sample_count', 0)}")
            
            if dna_profile['gold_dna_profile'].get('tempo_distribution'):
                tempo = dna_profile['gold_dna_profile']['tempo_distribution']
                print(f"  Average tempo: {tempo.get('avg', 120):.1f} BPM")
    
    # Initialize components
    analyzer = MIDIDNAAnalyzer()
    optimizer = KorgMIDIOptimizer(dna_profile=dna_profile)
    
    # Check if input is file or directory
    if os.path.isfile(args.input):
        # Single file mode
        if args.analyze_only:
            print(f"Analyzing: {args.input}")
            result = analyzer.analyze_file(args.input)
            
            if args.report:
                print(json.dumps(result, indent=2, default=str))
            else:
                print(f"  Type: {result.get('type')}")
                print(f"  Tracks: {result.get('num_tracks')}")
                print(f"  Tempo: {result.get('global_features', {}).get('tempo_bpm', 'N/A')} BPM")
        else:
            # Optimize single file
            output_file = os.path.join(args.output, os.path.basename(args.input))
            os.makedirs(args.output, exist_ok=True)
            
            print(f"Optimizing: {args.input}")
            result = optimizer.optimize_file(args.input, output_file)
            
            if result['success']:
                print(f"  Output: {output_file}")
                
                if result.get('improvements'):
                    print(f"  Improvements:")
                    for key, value in result['improvements'].items():
                        print(f"    - {key}: {value}")
            else:
                print(f"  Error: {result.get('error')}")
                sys.exit(1)
    
    elif os.path.isdir(args.input):
        # Directory mode
        if args.analyze_only:
            print(f"Analyzing directory: {args.input}")
            results = analyzer.analyze_directory(args.input)
            
            print(f"\nAnalysis Results:")
            print(f"  Files analyzed: {results['files_analyzed']}")
            print(f"  Errors: {len(results['errors'])}")
            
            if results['dna_samples']:
                profile = analyzer.create_style_profile(results['dna_samples'])
                print(f"\nStyle Profile:")
                print(f"  Sample count: {profile.get('sample_count', 0)}")
                if profile.get('tempo_distribution'):
                    tempo = profile['tempo_distribution']
                    print(f"  Tempo range: {tempo.get('min', 0):.1f} - {tempo.get('max', 0):.1f} BPM")
                    print(f"  Average tempo: {tempo.get('avg', 120):.1f} BPM")
            
            if args.report:
                report_file = os.path.join(args.output, 'analysis_report.json')
                os.makedirs(args.output, exist_ok=True)
                with open(report_file, 'w') as f:
                    json.dump(results, f, indent=2, default=str)
                print(f"\nReport saved to: {report_file}")
        else:
            # Optimize directory
            print(f"Optimizing directory: {args.input}")
            print(f"Output directory: {args.output}")
            
            results = optimizer.optimize_directory(args.input, args.output)
            
            print(f"\nOptimization Results:")
            print(f"  Files processed: {results['files_processed']}")
            print(f"  Successful: {results['successful']}")
            print(f"  Failed: {results['failed']}")
            
            if args.report:
                report_file = os.path.join(args.output, 'optimization_report.json')
                with open(report_file, 'w') as f:
                    json.dump(results, f, indent=2, default=str)
                print(f"\nReport saved to: {report_file}")
    
    else:
        print(f"Error: Input path does not exist: {args.input}")
        sys.exit(1)
    
    print("\nDone!")


if __name__ == '__main__':
    main()
