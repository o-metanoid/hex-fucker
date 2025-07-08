#!/usr/bin/env python3
"""
Hex Fucker - Corrupt video files by manipulating hex data directly
Targets AVI frame data chunks while preserving file structure integrity
"""

import os
import sys
import struct
import random
import argparse
import json
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass
from pathlib import Path
import subprocess

# --- SMEAR MODE CONFIG ---
smear_mode = False  # If true, applies smear-oriented corruption logic

@dataclass
class GlitchConfig:
    """Configuration for glitch parameters"""
    patterns: List[bytes]  # Glitch patterns to apply
    target_strategy: str   # 'every_nth', 'random', 'time_offset'
    target_value: int      # N for every_nth, percentage for random, offset for time_offset
    max_glitches: int      # Maximum number of glitches to apply
    skip_header_bytes: int # Bytes to skip after chunk header (default 12)
    glitch_size: int       # Size of glitch to apply (default 16)
    intensity: str = 'medium'  # Intensity level: low, medium, high, extreme, fucked

class HexFucker:
    """Main class for video hex fucking operations"""
    
    def __init__(self, config: GlitchConfig, smear_mode: bool = False):
        self.config = config
        self.glitch_log = []  # Track applied glitches for debugging
        self.intensity_params = get_intensity_params(config.intensity)
        self.smear_mode = smear_mode
        self.smear_patterns = None  # Will be set per run

    def find_frame_chunks(self, data: bytes) -> List[Tuple[int, int]]:
        """
        Find all '00dc' frame data chunks in AVI file
        Returns list of (offset, size) tuples
        """
        chunks = []
        # Search for '00dc' ASCII pattern (30 30 64 63 in hex)
        pattern = b'00dc'
        offset = 0
        
        while True:
            pos = data.find(pattern, offset)
            if pos == -1:
                break
                
            # Read chunk size (4 bytes after '00dc')
            if pos + 8 <= len(data):
                try:
                    # AVI uses little-endian format
                    chunk_size = struct.unpack('<I', data[pos + 4:pos + 8])[0]
                    chunks.append((pos, chunk_size))
                except struct.error:
                    pass  # Skip malformed chunks
                    
            offset = pos + 1
            
        return chunks

    def apply_intensity_glitches(self, data: bytearray, chunk_offset: int, chunk_size: int) -> int:
        """
        Apply multiple stacked pattern overwrites to a chunk, based on intensity settings.
        Returns the number of glitches applied.
        """
        p = self.intensity_params
        data_start = chunk_offset + 8 + p['skip_header_bytes']
        data_end = chunk_offset + 8 + chunk_size
        if data_start >= data_end or data_start >= len(data):
            return 0
        available_space = min(data_end - data_start, len(data) - data_start)
        if available_space <= 0:
            return 0
        glitches_applied = 0
        pos = 0
        used_offsets = set()
        while pos < available_space:
            # Randomize spacing and offset
            spacing = random.randint(p['overwrite_spacing_min'], p['overwrite_spacing_max'])
            chaos = random.randint(0, p['chaos_offset']) if p['chaos_offset'] > 0 else 0
            offset = data_start + pos + chaos
            if offset >= data_end:
                break
            # Randomize overwrite size
            overwrite_size = random.randint(p['overwrite_size_min'], p['overwrite_size_max'])
            if offset + overwrite_size > data_end:
                overwrite_size = data_end - offset
            if overwrite_size <= 0:
                break
            # Pattern stacking
            stack_count = random.randint(p['pattern_stack_min'], p['pattern_stack_max'])
            patterns = [random.choice(self.config.patterns) for _ in range(stack_count)]
            pattern_bytes = b''.join(patterns)
            # Truncate or repeat pattern_bytes to fit overwrite_size
            if len(pattern_bytes) < overwrite_size:
                # Repeat pattern if too short
                repeats = (overwrite_size + len(pattern_bytes) - 1) // len(pattern_bytes)
                pattern_bytes = (pattern_bytes * repeats)[:overwrite_size]
            else:
                pattern_bytes = pattern_bytes[:overwrite_size]
            # Overlap control
            if not p['overlap']:
                if any(o in used_offsets for o in range(offset, offset+overwrite_size)):
                    pos += spacing
                    continue
                used_offsets.update(range(offset, offset+overwrite_size))
            # Apply the glitch
            try:
                data[offset:offset+overwrite_size] = pattern_bytes
                self.glitch_log.append({
                    'offset': offset,
                    'size': overwrite_size,
                    'pattern': pattern_bytes[:16].hex() + ("..." if len(pattern_bytes) > 16 else ""),
                    'chunk_offset': chunk_offset
                })
                glitches_applied += 1
            except (IndexError, ValueError):
                break
            pos += spacing
        return glitches_applied

    def apply_smear_glitch(self, data: bytearray, chunk_offset: int, chunk_size: int, smear_offset: int, pattern: bytes) -> int:
        """
        Apply a single large, stable-pattern corruption at a sliding offset within the chunk.
        Returns 1 if applied, 0 if not.
        """
        # Avoid corrupting header regions (file offset < 100KB)
        file_offset = chunk_offset + 8 + smear_offset
        if file_offset < 102400:
            return 0
        # Boundaries
        data_start = chunk_offset + 8
        data_end = chunk_offset + 8 + chunk_size
        if file_offset + 1024 > data_end:
            # If not enough space, skip
            return 0
        if file_offset + 1024 > len(data):
            return 0
        # Apply the glitch
        try:
            data[file_offset:file_offset+1024] = pattern[:1024]
            self.glitch_log.append({
                'offset': file_offset,
                'size': 1024,
                'pattern': pattern[:16].hex() + ("..." if len(pattern) > 16 else ""),
                'chunk_offset': chunk_offset
            })
            return 1
        except (IndexError, ValueError):
            return 0

    def select_frames_to_glitch(self, total_frames: int) -> List[int]:
        """
        Select which frames to glitch based on targeting strategy
        """
        selected = []
        
        if self.config.target_strategy == 'every_nth':
            n = max(1, self.config.target_value)
            selected = list(range(0, total_frames, n))
            
        elif self.config.target_strategy == 'random':
            percentage = max(0, min(100, self.config.target_value))
            count = int(total_frames * percentage / 100)
            selected = random.sample(range(total_frames), min(count, total_frames))
            
        elif self.config.target_strategy == 'time_offset':
            # Assume frames after offset position
            start_frame = max(0, min(total_frames - 1, self.config.target_value))
            selected = list(range(start_frame, total_frames))
            
        # Limit to max_glitches
        if self.config.max_glitches > 0:
            selected = selected[:self.config.max_glitches]
            
        return sorted(selected)

    def fuck_video(self, input_path: str, output_path: str) -> bool:
        """
        Main hex fucking function - process video file and apply glitches
        """
        try:
            # Read input file as binary
            with open(input_path, 'rb') as f:
                data = bytearray(f.read())
            print(f"Loaded video file: {len(data):,} bytes")
            # Find all frame chunks
            chunks = self.find_frame_chunks(data)
            print(f"Found {len(chunks)} frame chunks")
            if not chunks:
                print("No frame chunks found. Is this a valid AVI file?")
                return False
            # Select frames to glitch
            frames_to_glitch = self.select_frames_to_glitch(len(chunks))
            print(f"Targeting {len(frames_to_glitch)} frames for hex fucking")
            # --- SMEAR MODE LOGIC ---
            if self.smear_mode:
                # Select 2-3 stable patterns for this run
                if len(self.config.patterns) <= 3:
                    self.smear_patterns = self.config.patterns
                else:
                    self.smear_patterns = random.sample(self.config.patterns, k=random.randint(2, 3))
                print(f"[Smear Mode] Using {len(self.smear_patterns)} stable patterns for this run.")
                smear_offset = 0
                smear_step_min = 4000
                smear_step_max = 8000
                smear_applied = 0
                skip_first_n = 2  # Avoid first 2 frames (likely I-frames)
                for i, frame_idx in enumerate(frames_to_glitch):
                    if i < skip_first_n:
                        continue
                    if frame_idx < len(chunks):
                        chunk_offset, chunk_size = chunks[frame_idx]
                        # Sliding window: offset increases per frame
                        smear_offset += random.randint(smear_step_min, smear_step_max)
                        # Cycle through stable patterns
                        pattern = self.smear_patterns[i % len(self.smear_patterns)]
                        smear_applied += self.apply_smear_glitch(data, chunk_offset, chunk_size, smear_offset, pattern)
                print(f"[Smear Mode] Applied {smear_applied} smear hex fucks")
            else:
                # Original logic
                glitches_applied = 0
                for frame_idx in frames_to_glitch:
                    if frame_idx < len(chunks):
                        chunk_offset, chunk_size = chunks[frame_idx]
                        glitches_applied += self.apply_intensity_glitches(data, chunk_offset, chunk_size)
                print(f"Applied {glitches_applied} hex fucks")
            # Write output file
            with open(output_path, 'wb') as f:
                f.write(data)
            print(f"Saved hex fucked video: {output_path}")
            return True
        except FileNotFoundError:
            print(f"Input file not found: {input_path}")
            return False
        except PermissionError:
            print(f"Permission denied accessing files")
            return False
        except Exception as e:
            print(f"Error during hex fucking: {e}")
            return False
    
    def print_glitch_log(self):
        """Print detailed log of applied glitches"""
        if not self.glitch_log:
            print("No hex fucks were applied.")
            return
            
        print(f"\nHex Fuck Log ({len(self.glitch_log)} entries):")
        print("-" * 60)
        for i, entry in enumerate(self.glitch_log, 1):
            print(f"{i:3d}. Offset: 0x{entry['offset']:08x} | "
                  f"Size: {entry['size']:2d} bytes | "
                  f"Pattern: {entry['pattern'][:16]}...")

def load_glitch_patterns(json_file: str = 'glitch_patterns_256.json') -> Dict[str, Dict]:
    """
    Load glitch patterns from JSON file
    Returns dictionary with pattern name as key and pattern info as value
    """
    try:
        with open(json_file, 'r') as f:
            patterns_list = json.load(f)
        
        patterns_dict = {}
        for pattern_data in patterns_list:
            name = pattern_data['name']
            description = pattern_data['description']
            hex_pattern = pattern_data['pattern']
            
            # Convert hex strings to bytes
            byte_pattern = bytes([int(hex_byte, 16) for hex_byte in hex_pattern])
            
            patterns_dict[name] = {
                'description': description,
                'pattern': byte_pattern
            }
        
        return patterns_dict
    
    except FileNotFoundError:
        print(f"Pattern file '{json_file}' not found. Using fallback patterns.")
        return get_fallback_patterns()
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        print(f"Error loading patterns from '{json_file}': {e}")
        print("Using fallback patterns.")
        return get_fallback_patterns()

def get_fallback_patterns() -> Dict[str, Dict]:
    """
    Fallback patterns if JSON file can't be loaded
    """
    return {
        'whiteout': {
            'description': 'All FF bytes - creates white flash effect',
            'pattern': b'\xFF' * 256
        },
        'blackout': {
            'description': 'All 00 bytes - creates black frames or freezing',
            'pattern': b'\x00' * 256
        },
        'checkerboard': {
            'description': 'Alternating pattern for digital noise',
            'pattern': (b'\xAA\x55' * 128)
        },
        'rainbow_simple': {
            'description': 'Simple rainbow gradient',
            'pattern': bytes([i % 256 for i in range(256)])
        }
    }

# Load patterns from JSON file
GLITCH_PATTERNS = load_glitch_patterns()

def list_available_patterns():
    """Display all available glitch patterns with descriptions"""
    print("Available Hex Fuck Patterns:")
    print("=" * 50)
    
    for name, info in GLITCH_PATTERNS.items():
        pattern_size = len(info['pattern'])
        description = info['description']
        print(f"{name}")
        print(f"   Size: {pattern_size} bytes")
        print(f"   Effect: {description}")
        print()
    
    print(f"Total patterns available: {len(GLITCH_PATTERNS)}")
    print("\nUsage: python hex_fucker.py input.avi output.avi --pattern <pattern_name>")
    print("       python hex_fucker.py input.avi output.avi --pattern <pattern1,pattern2,pattern3>")
    print("       python hex_fucker.py input.avi output.avi --pattern all")

# Intensity parameter mapping
def get_intensity_params(intensity):
    intensity = intensity.lower()
    if intensity == 'low':
        return {
            'overwrite_spacing_min': 512,
            'overwrite_spacing_max': 1024,
            'overwrite_size_min': 128,
            'overwrite_size_max': 256,
            'pattern_stack_min': 1,
            'pattern_stack_max': 1,
            'chaos_offset': 0,
            'overlap': False,
            'skip_header_bytes': 8,
        }
    elif intensity == 'medium':
        return {
            'overwrite_spacing_min': 256,
            'overwrite_spacing_max': 512,
            'overwrite_size_min': 256,
            'overwrite_size_max': 512,
            'pattern_stack_min': 1,
            'pattern_stack_max': 2,
            'chaos_offset': 8,
            'overlap': False,
            'skip_header_bytes': 8,
        }
    elif intensity == 'high':
        return {
            'overwrite_spacing_min': 128,
            'overwrite_spacing_max': 256,
            'overwrite_size_min': 384,
            'overwrite_size_max': 768,
            'pattern_stack_min': 2,
            'pattern_stack_max': 3,
            'chaos_offset': 16,
            'overlap': True,
            'skip_header_bytes': 8,
        }
    elif intensity == 'extreme':
        return {
            'overwrite_spacing_min': 64,
            'overwrite_spacing_max': 128,
            'overwrite_size_min': 512,
            'overwrite_size_max': 1024,
            'pattern_stack_min': 3,
            'pattern_stack_max': 4,
            'chaos_offset': 32,
            'overlap': True,
            'skip_header_bytes': 8,
        }
    elif intensity == 'fucked':
        return {
            'overwrite_spacing_min': 32,
            'overwrite_spacing_max': 64,
            'overwrite_size_min': 768,
            'overwrite_size_max': 2048,
            'pattern_stack_min': 4,
            'pattern_stack_max': 6,
            'chaos_offset': 64,
            'overlap': True,
            'skip_header_bytes': 8,
        }
    else:
        # Default to medium
        return get_intensity_params('medium')

def create_default_config() -> GlitchConfig:
    """Create default glitch configuration"""
    all_patterns = []
    for pattern_info in GLITCH_PATTERNS.values():
        all_patterns.append(pattern_info['pattern'])
    
    return GlitchConfig(
        patterns=all_patterns,
        target_strategy='every_nth',
        target_value=10,  # Every 10th frame
        max_glitches=50,
        skip_header_bytes=12,
        glitch_size=256  # Use full 256-byte patterns
    )

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
    
    # Handle list patterns option
    if args.list_patterns:
        list_available_patterns()
        sys.exit(0)
    
    # Validate required arguments when not listing patterns
    if not args.input or not args.output:
        parser.error("Input and output file paths are required when not using --list-patterns")
    
    # Set random seed if provided
    if args.seed:
        random.seed(args.seed)
        print(f"Using random seed: {args.seed}")
    
    # FFmpeg Preprocessing Step (if --auto-encode)
    input_file_for_hex = args.input
    temp_encoded = "temp_encoded.avi"
    if args.auto_encode:
        print("[Auto-Encode] Re-encoding input with FFmpeg for smear-friendly structure...")
        ffmpeg_cmd = [
            "ffmpeg", "-y", "-i", args.input,
            "-c:v", "libxvid",
            "-bf", "2",
            "-g", "150",
            "-keyint_min", "150",
            "-sc_threshold", "0",
            "-an",
            temp_encoded
        ]
        try:
            subprocess.run(ffmpeg_cmd, check=True)
            input_file_for_hex = temp_encoded
        except Exception as e:
            print(f"[Auto-Encode] FFmpeg failed: {e}")
            sys.exit(1)
    
    # Select patterns
    if args.pattern == 'all':
        patterns = [pattern_info['pattern'] for pattern_info in GLITCH_PATTERNS.values()]
        print(f"Using all {len(patterns)} available patterns")
    else:
        # Handle comma-separated pattern names
        pattern_names = [name.strip() for name in args.pattern.split(',')]
        patterns = []
        
        # Validate and collect patterns
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
    
    # Intensity params
    intensity_params = get_intensity_params(args.intensity)
    
    # Create configuration
    config = GlitchConfig(
        patterns=patterns,
        target_strategy=args.strategy,
        target_value=args.value,
        max_glitches=args.max_glitches,
        skip_header_bytes=intensity_params['skip_header_bytes'],
        glitch_size=intensity_params['overwrite_size_max'],  # Use max for now, will randomize in logic
        intensity=args.intensity
    )
    
    # Interactive mode: show frame count and get user input
    # Enable interactive mode if --interactive flag is used OR if max_glitches is default (50)
    # Disable if --no-interactive flag is used
    interactive_mode = (args.interactive or 
                       (args.max_glitches == 50 and '--max-glitches' not in sys.argv)) and not args.no_interactive
    
    if interactive_mode:
        print("Hex Fucker - Video Hex Corruption Tool")
        print("=" * 40)
        print("Analyzing video file...")
        
        # Load video file to count frames
        try:
            with open(args.input, 'rb') as f:
                data = f.read()
            
            # Create temporary hex fucker to count frames
            temp_hex_fucker = HexFucker(config)
            chunks = temp_hex_fucker.find_frame_chunks(data)
            total_frames = len(chunks)
            
            if total_frames == 0:
                print("No frame chunks found. Is this a valid AVI file?")
                sys.exit(1)
            
            print(f"Found {total_frames:,} frames in the video")
            print()
            
            # Calculate what current strategy would target
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
            
            # Prompt for desired corruption amount
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
                    
                    # Update max_glitches to user's desired amount
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
    
    # Create hex fucker and process video
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
        # Clean up temp file if it exists
        if args.auto_encode and os.path.exists(temp_encoded):
            try:
                os.remove(temp_encoded)
            except Exception:
                pass
        sys.exit(1)
    # Cleanup temp_encoded.avi if auto-encode was used
    if args.auto_encode and os.path.exists(temp_encoded):
        try:
            os.remove(temp_encoded)
            print("[Auto-Encode] Cleaned up temp_encoded.avi")
        except Exception:
            print("[Auto-Encode] Warning: Could not delete temp_encoded.avi")

if __name__ == '__main__':
    main() 