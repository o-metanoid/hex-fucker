#!/usr/bin/env python3
"""
Hex Fucker - Corrupt video files by manipulating hex data directly
Targets AVI frame data chunks while preserving file structure integrity
"""

import os
import sys
import argparse
from glitcher import HexFucker, GlitchConfig
from patterns import GLITCH_PATTERNS, list_available_patterns
from intensity import get_intensity_params
from ffmpeg_utils import run_ffmpeg_auto_encode, cleanup_temp_file

# --- SMEAR MODE CONFIG ---
smear_mode = False  # If true, applies smear-oriented corruption logic

def main():
    global smear_mode
    parser = argparse.ArgumentParser(description='Hex Fucker - Corrupt AVI videos by fucking with hex data. Interactive mode is enabled by default when max-glitches is not specified.')
    parser.add_argument('input', nargs='?', help='Input AVI file path')
    parser.add_argument('output', nargs='?', help='Output file path')
    parser.add_argument('--strategy', choices=['every_nth', 'random', 'time_offset'], 
                       default='every_nth', help='Frame targeting strategy')
    parser.add_argument('--value', type=int, default=10, 
                       help='Strategy value (N for every_nth, %% for random, offset for time_offset)')
    parser.add_argument('--max-glitches', type=int, default=50, 
                       help='Maximum number of glitches to apply')
    parser.add_argument('--pattern', default='all', 
                       help='Glitch pattern(s) to use. Single pattern, comma-separated list, or "all". Available: ' + ', '.join(list(GLITCH_PATTERNS.keys())))
    parser.add_argument('--glitch-size', type=int, default=256, 
                       help='Size of each glitch in bytes')
    parser.add_argument('--skip-bytes', type=int, default=12, 
                       help='Bytes to skip after chunk header')
    parser.add_argument('--log', action='store_true', 
                       help='Print detailed glitch log')
    parser.add_argument('--seed', type=int, help='Random seed for reproducible results')
    parser.add_argument('--list-patterns', action='store_true', 
                       help='List all available glitch patterns and exit')
    parser.add_argument('--interactive', action='store_true',
                       help='Force interactive mode: shows frame count and prompts for corruption amount')
    parser.add_argument('--no-interactive', action='store_true',
                       help='Disable interactive mode (use when max-glitches=50 but want non-interactive)')
    parser.add_argument('--intensity', choices=['low', 'medium', 'high', 'extreme', 'fucked'], default='medium',
                       help='Glitch intensity: low, medium, high, extreme, fucked (controls overwrite size, frequency, stacking, chaos)')
    parser.add_argument('--smear-mode', action='store_true', help='Enable smear mode for temporal drag/smear effects')
    parser.add_argument('--auto-encode', action='store_true', help='Automatically re-encode input with FFmpeg for smear-friendly structure before hex editing')
    
    args = parser.parse_args()
    if args.list_patterns:
        list_available_patterns()
        sys.exit(0)
    if not args.input or not args.output:
        parser.error("Input and output file paths are required when not using --list-patterns")
    if args.seed:
        import random
        random.seed(args.seed)
        print(f"Using random seed: {args.seed}")
    if args.smear_mode:
        smear_mode = True
    # FFmpeg Preprocessing Step (if --auto-encode)
    input_file_for_hex = args.input
    temp_encoded = "temp_encoded.avi"
    if args.auto_encode:
        print("[Auto-Encode] Re-encoding input with FFmpeg for smear-friendly structure...")
        try:
            run_ffmpeg_auto_encode(args.input, temp_encoded)
            input_file_for_hex = temp_encoded
        except Exception as e:
            print(f"[Auto-Encode] FFmpeg failed: {e}")
            sys.exit(1)
    # Select patterns
    if args.pattern == 'all':
        patterns = [pattern_info['pattern'] for pattern_info in GLITCH_PATTERNS.values()]
        print(f"Using all {len(patterns)} available patterns")
    else:
        pattern_names = [name.strip() for name in args.pattern.split(',')]
        patterns = []
        for pattern_name in pattern_names:
            if pattern_name not in GLITCH_PATTERNS:
                print(f"Error: Pattern '{pattern_name}' not found.")
                print(f"Available patterns: {', '.join(GLITCH_PATTERNS.keys())}")
                sys.exit(1)
            patterns.append(GLITCH_PATTERNS[pattern_name]['pattern'])
        if len(pattern_names) == 1:
            print(f"Using pattern: {pattern_names[0]}")
        else:
            print(f"Using {len(pattern_names)} patterns: {', '.join(pattern_names)}")
    intensity_params = get_intensity_params(args.intensity)
    config = GlitchConfig(
        patterns=patterns,
        target_strategy=args.strategy,
        target_value=args.value,
        max_glitches=args.max_glitches,
        skip_header_bytes=intensity_params['skip_header_bytes'],
        glitch_size=intensity_params['overwrite_size_max'],
        intensity=args.intensity
    )
    interactive_mode = (args.interactive or 
                       (args.max_glitches == 50 and '--max-glitches' not in sys.argv)) and not args.no_interactive
    if interactive_mode:
        print("Hex Fucker - Video Hex Corruption Tool")
        print("=" * 40)
        print("Analyzing video file...")
        try:
            with open(args.input, 'rb') as f:
                data = f.read()
            temp_hex_fucker = HexFucker(config)
            chunks = temp_hex_fucker.find_frame_chunks(data)
            total_frames = len(chunks)
            if total_frames == 0:
                print("No frame chunks found. Is this a valid AVI file?")
                sys.exit(1)
            print(f"Found {total_frames:,} frames in the video")
            print()
            temp_frames = temp_hex_fucker.select_frames_to_glitch(total_frames)
            if args.strategy == 'every_nth':
                strategy_desc = f"Every {args.value}th frame would target ~{len(temp_frames):,} frames"
            elif args.strategy == 'random':
                strategy_desc = f"Random {args.value}% would target ~{len(temp_frames):,} frames"
            elif args.strategy == 'time_offset':
                strategy_desc = f"Time offset from frame {args.value} would target ~{len(temp_frames):,} frames"
            print(f"Current strategy ({args.strategy}): {strategy_desc}")
            print(f"Current max-glitches limit: {args.max_glitches:,}")
            print()
            while True:
                try:
                    user_input = input(f"How many frames would you like to corrupt? (1-{total_frames:,}): ").strip()
                    if user_input == "":
                        print("Please enter a number.")
                        continue
                    desired_frames = int(user_input)
                    if desired_frames < 1:
                        print("Please enter a number greater than 0.")
                        continue
                    elif desired_frames > total_frames:
                        print(f"Cannot corrupt more than {total_frames:,} frames.")
                        continue
                    config.max_glitches = desired_frames
                    print()
                    print(f"Set to corrupt {desired_frames:,} frames")
                    break
                except ValueError:
                    print("Please enter a valid number.")
                    continue
                except KeyboardInterrupt:
                    print("\nOperation cancelled.")
                    sys.exit(0)
        except FileNotFoundError:
            print(f"Input file not found: {args.input}")
            sys.exit(1)
        except Exception as e:
            print(f"Error analyzing video: {e}")
            sys.exit(1)
    hex_fucker = HexFucker(config, smear_mode=smear_mode)
    if not interactive_mode:
        print("Hex Fucker - Video Hex Corruption Tool")
        print("=" * 40)
    success = hex_fucker.fuck_video(input_file_for_hex, args.output)
    if args.log and success:
        hex_fucker.print_glitch_log()
    if success:
        print("\nHex fucking completed successfully!")
    else:
        print("\nHex fucking failed!")
        if args.auto_encode:
            cleanup_temp_file(temp_encoded)
        sys.exit(1)
    if args.auto_encode:
        if cleanup_temp_file(temp_encoded):
            print("[Auto-Encode] Cleaned up temp_encoded.avi")
        else:
            print("[Auto-Encode] Warning: Could not delete temp_encoded.avi")

if __name__ == '__main__':
    main() 