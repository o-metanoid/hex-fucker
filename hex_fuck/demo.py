#!/usr/bin/env python3
"""
Demo script showing different ways to use the Hex Fucker
Creates various hex fucked versions of an input video with different effects
"""

import os
import sys
from hex_fucker import HexFucker, GlitchConfig, GLITCH_PATTERNS

def demo_glitch_variations(input_video: str):
    """
    Create multiple glitched versions with different effects
    """
    if not os.path.exists(input_video):
        print(f"Input video not found: {input_video}")
        print("Please provide a valid AVI file to glitch!")
        return
    
    base_name = os.path.splitext(input_video)[0]
    
    # Demo 1: Whiteout every 5th frame
    print("Demo 1: Whiteout Flash")
    config1 = GlitchConfig(
        patterns=[GLITCH_PATTERNS['whiteout']['pattern']],
        target_strategy='every_nth',
        target_value=5,
        max_glitches=30,
        skip_header_bytes=12,
        glitch_size=256
    )
    glitcher1 = HexFucker(config1)
    glitcher1.fuck_video(input_video, f"{base_name}_whiteout.avi")
    
    # Demo 2: Checkerboard pulse on random frames
    print("\nDemo 2: Checkerboard Pulse")
    config2 = GlitchConfig(
        patterns=[GLITCH_PATTERNS['checkerboard_pulse']['pattern']],
        target_strategy='random',
        target_value=25,  # 25% of frames
        max_glitches=40,
        skip_header_bytes=8,
        glitch_size=256
    )
    glitcher2 = HexFucker(config2)
    glitcher2.fuck_video(input_video, f"{base_name}_checkerboard.avi")
    
    # Demo 3: Rainbow drift after halfway point
    print("\nDemo 3: Rainbow Drift")
    config3 = GlitchConfig(
        patterns=[GLITCH_PATTERNS['rainbow_drift']['pattern']],
        target_strategy='time_offset',
        target_value=50,  # Start after frame 50
        max_glitches=25,
        skip_header_bytes=16,
        glitch_size=256
    )
    glitcher3 = HexFucker(config3)
    glitcher3.fuck_video(input_video, f"{base_name}_rainbow.avi")
    
    # Demo 4: Garbage binary - heavy corruption
    print("\nDemo 4: Garbage Binary")
    config4 = GlitchConfig(
        patterns=[GLITCH_PATTERNS['garbage_binary']['pattern']],
        target_strategy='every_nth',
        target_value=3,  # Every 3rd frame
        max_glitches=100,
        skip_header_bytes=10,
        glitch_size=256
    )
    glitcher4 = HexFucker(config4)
    glitcher4.fuck_video(input_video, f"{base_name}_garbage.avi")
    
    # Demo 5: Mixed patterns - artistic effect
    print("\nDemo 5: Mixed Patterns")
    mixed_patterns = [pattern_info['pattern'] for pattern_info in GLITCH_PATTERNS.values()]
    
    config5 = GlitchConfig(
        patterns=mixed_patterns,
        target_strategy='random',
        target_value=15,  # 15% of frames
        max_glitches=50,
        skip_header_bytes=14,
        glitch_size=256
    )
    glitcher5 = HexFucker(config5)
    glitcher5.fuck_video(input_video, f"{base_name}_mixed.avi")
    glitcher5.print_glitch_log()
    
    print("\nAll demo hex fucks completed!")
    print("Generated files:")
    for suffix in ['whiteout', 'checkerboard', 'rainbow', 'garbage', 'mixed']:
        filename = f"{base_name}_{suffix}.avi"
        if os.path.exists(filename):
            size = os.path.getsize(filename)
            print(f"  • {filename} ({size:,} bytes)")

def create_sample_avi():
    """
    Create a minimal sample AVI file for testing (simplified structure)
    This creates a very basic AVI file structure for demonstration
    """
    print("Creating sample AVI file for testing...")
    
    # Basic AVI file structure (simplified)
    # This is just for demonstration - in real use, provide actual AVI files
    avi_header = (
        b'RIFF'               # RIFF header
        b'\x00\x10\x00\x00'   # File size placeholder
        b'AVI '               # AVI format
        b'LIST'               # LIST chunk
        b'\x00\x08\x00\x00'   # List size
        b'hdrl'               # Header list
        b'avih'               # AVI header
        b'\x38\x00\x00\x00'   # Header size
        b'\x00' * 56          # AVI header data (simplified)
    )
    
    # Sample frame data chunks
    frame_data = b''
    for i in range(10):  # 10 sample frames
        frame_chunk = (
            b'00dc'               # Frame chunk ID
            b'\x00\x04\x00\x00'   # Chunk size (1024 bytes)
            b'\xFF\x00\x80\x40' * 256  # Sample frame data (1024 bytes)
        )
        frame_data += frame_chunk
    
    # Combine all parts
    sample_avi = avi_header + frame_data
    
    with open('sample.avi', 'wb') as f:
        f.write(sample_avi)
    
    print("Created sample.avi for testing")
    return 'sample.avi'

def main():
    if len(sys.argv) > 1:
        input_video = sys.argv[1]
    else:
        print("No input video provided. Creating sample AVI file...")
        input_video = create_sample_avi()
        print("You can also provide your own AVI file:")
        print("   python demo.py your_video.avi")
        print()
    
    print("Hex Fucker Demo")
    print("=" * 40)
    print(f"Input: {input_video}")
    print()
    
    demo_glitch_variations(input_video)

if __name__ == '__main__':
    main() 