import json
from typing import Dict

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