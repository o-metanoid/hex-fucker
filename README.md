# Hex Fucker - Video Hex Corruption Tool

A Python tool for creating glitch art by corrupting video files at the hex level. Targets AVI frame data chunks while preserving file structure integrity for playable corrupted videos.

## Features

- **Hex-Level Corruption**: Directly manipulates video frame data in binary
- **Smart Targeting**: Finds and corrupts `00dc` frame chunks in AVI files
- **Multiple Glitch Patterns**: Static, digital, rainbow, and chaos corruption styles
- **Intensity Control**: Five levels (low, medium, high, extreme, fucked) control overwrite size, frequency, stacking, chaos, and overlap
- **Pattern Stacking & Chaotic Offsets**: Multiple patterns can be stacked and applied at random, chaotic offsets for maximum glitch variety
- **Flexible Targeting**: Corrupt every Nth frame, random frames, or time-based offsets
- **Safe Corruption**: Preserves file structure to maintain video playability
- **Detailed Logging**: Track exactly what was corrupted and where
- **Smear Mode (Temporal Drag/Smear) [EXPERIMENTAL]**: Applies large, stable-pattern corruptions in a sliding window for temporal smear effects, with header safety and reduced jitter. May cause playback issues or unexpected results.
- **FFmpeg Auto-Encode**: Optionally re-encodes your input video with refined settings (sparse I-frames, B-frames) for optimal glitching and smear effects

## Quick Start

### Basic Usage

```bash
# Hex fuck every 10th frame with all patterns
python hex_fucker.py input.avi output_glitched.avi

# High intensity rainbow smear corruption (more frequent, larger, stacked patterns)
python hex_fucker.py input.avi output.avi --pattern rainbow_smear --intensity high

# Extreme intensity with pattern stacking and chaotic offsets
python hex_fucker.py input.avi output.avi --pattern static_grit,bitflip_noise,ghost_echo --intensity extreme

# Fucked intensity: maximum chaos, overlap, and overwrite size
python hex_fucker.py input.avi output.avi --pattern all --intensity fucked

# Smear mode (EXPERIMENTAL): temporal drag/smear effect with stable patterns and sliding window
# WARNING: This mode is experimental and may break video playback or cause unexpected results.
python hex_fucker.py input.avi output.avi --smear-mode

# Auto-encode for best smear results (recommended for most videos)
python hex_fucker.py input.avi output.avi --auto-encode --smear-mode

# List all available patterns
python hex_fucker.py --list-patterns
```

### Run the Demo

```bash
# Run demo with your own AVI file
python demo.py your_video.avi

# Run demo with generated sample file
python demo.py
```

## Command Line Options

| Option | Default | Description |
|--------|---------|-------------|
| `input` | Required | Input AVI file path |
| `output` | Required | Output file path |
| `--strategy` | `every_nth` | Frame targeting: `every_nth`, `random`, `time_offset` |
| `--value` | `10` | Strategy value (N for every_nth, % for random, offset for time_offset) |
| `--max-glitches` | `50` | Maximum number of glitches to apply |
| `--pattern` | `all` | Pattern(s): single `whiteout`, multiple `whiteout,blackout,rainbow_smear`, or `all` |
| `--glitch-size` | `256` | Size of each glitch in bytes |
| `--list-patterns` | False | List all available patterns and exit |
| `--skip-bytes` | `12` | Bytes to skip after chunk header |
| `--log` | False | Print detailed glitch log |
| `--seed` | Random | Random seed for reproducible results |
| `--intensity` | `medium` | Glitch intensity: low, medium, high, extreme, fucked (controls overwrite size, frequency, stacking, chaos) |
| `--smear-mode` | False | Enable temporal smear mode: large, stable-pattern corruptions with sliding window and header safety |
| `--auto-encode` | False | Re-encode input with FFmpeg for smear-friendly structure (sparse I-frames, B-frames) before hex editing |

## Glitch Patterns

All patterns are 256 bytes long and loaded from `glitch_patterns_256.json`. **23 unique patterns** are now available. Use `--list-patterns` to see all available options.

### Available Patterns
- **whiteout**: White-out / blown pixels
- **blackout**: Blackout / null blocks
- **rainbow_smear**: Rainbow smear / color bleed
- **strobe_flicker**: Strobe flicker / pulsing
- **chroma_shift**: Chroma shift / RGB distortion
- **block_drift**: Block drift / shifting pixels
- **banding_stripes**: Banding stripes / wave textures
- **inversion_break**: Inversion break / partial decode
- **color_burn**: Color burn / blown-out zones
- **checkerboard_flicker**: Checkerboard flicker
- **negative_burst**: Negative burst / ghost smear
- **vertical_skew**: Vertical skew / gradient drift
- **static_grit**: Static / digital grit
- **flat_gray**: Flat gray melt / texture loss
- **color_pulse**: Color pulse / mild echo
- **rhythmic_flicker**: Rhythmic flicker
- **warp_twist**: Distorted warp / block twist
- **ghost_echo**: Ghost echo / double image
- **scanline_jitter**: Scanline jitter / interlace confusion
- **step_skew**: Step skew / decode collapse
- **motion_vector_jam**: Disrupts predicted motion vectors, causing smear or visual tearing
- **quant_table_spike**: Triggers quantization overflow, exaggerating blockiness
- **bitflip_noise**: Causes unpredictable decoder behavior via pseudo-random XOR-like flicker

### Pattern Selection Options

**Single Pattern:**
```bash
python hex_fucker.py input.avi output.avi --pattern whiteout
```

**Multiple Specific Patterns:**
```bash
# Light corruption mix
python hex_fucker.py input.avi output.avi --pattern color_pulse,flat_gray,vertical_skew

# Heavy glitch combo
python hex_fucker.py input.avi output.avi --pattern static_grit,warp_twist,negative_burst

# Color effects only
python hex_fucker.py input.avi output.avi --pattern rainbow_smear,chroma_shift,color_burn
```

**All Patterns:**
```bash
python hex_fucker.py input.avi output.avi --pattern all
```

**Note:** When multiple patterns are specified, the tool randomly selects one pattern for each frame corruption, creating varied glitch effects throughout the video.

### Custom Patterns
You can modify `glitch_patterns_256.json` to add your own 256-byte hex patterns.

## Targeting Strategies

### Every Nth Frame (`every_nth`)
```bash
python hex_fucker.py input.avi output.avi --strategy every_nth --value 5
```
Corrupts every 5th frame. Good for rhythmic glitch effects.

### Random Frames (`random`)
```bash
python hex_fucker.py input.avi output.avi --strategy random --value 30 --pattern rainbow_smear,chroma_shift
```
Corrupts 30% of frames randomly. Creates unpredictable glitch timing.

### Time Offset (`time_offset`)
```bash
python hex_fucker.py input.avi output.avi --strategy time_offset --value 100 --pattern blackout
```
Starts corrupting after frame 100. Good for progressive corruption effects.

## Advanced Usage

### Custom Configuration
```python
from hex_fucker import HexFucker, GlitchConfig

# Load specific patterns by name
selected_patterns = [
    GLITCH_PATTERNS['static_grit']['pattern'],
    GLITCH_PATTERNS['warp_twist']['pattern'],
    GLITCH_PATTERNS['color_burn']['pattern']
]

# Or create custom glitch patterns
custom_patterns = [
    b'\xDE\xAD\xBE\xEF' * 64,  # "DEADBEEF" pattern (256 bytes)
    b'\x42' * 256,             # All 0x42 bytes (256 bytes)
]

# Configure hex fucker with multiple patterns
config = GlitchConfig(
    patterns=selected_patterns + custom_patterns,  # Combine patterns
    target_strategy='random',
    target_value=20,
    max_glitches=75,
    skip_header_bytes=8,
    glitch_size=256
)

# Apply hex fucks
hex_fucker = HexFucker(config)
hex_fucker.fuck_video('input.avi', 'output.avi')
hex_fucker.print_glitch_log()
```

### Reproducible Results
```bash
# Use seed for consistent results
python hex_fucker.py input.avi output.avi --seed 42 --log
```

### Smear Mode in Custom Scripts

You can enable smear mode programmatically:

```python
from hex_fucker import HexFucker, GlitchConfig

config = GlitchConfig(
    patterns=[...],
    target_strategy='every_nth',
    target_value=10,
    max_glitches=50,
    skip_header_bytes=12,
    glitch_size=256
)
hex_fucker = HexFucker(config, smear_mode=True)
hex_fucker.fuck_video('input.avi', 'output.avi')
```

Or from the CLI:

```bash
python hex_fucker.py input.avi output.avi --smear-mode
```

## Glitch Intensity Levels

The `--intensity` argument controls how aggressively and chaotically the tool corrupts each video frame. Each level changes:
- How often glitches are applied within a frame (overwrite frequency)
- How many bytes are overwritten at each site (overwrite size)
- How many patterns are stacked together (pattern stacking)
- How random the offset is for each overwrite (chaotic offset)
- Whether overwrites can overlap

| Intensity | Overwrite Spacing (bytes) | Overwrite Size (bytes) | Pattern Stack | Chaotic Offset | Overlap | Skip Header Bytes |
|-----------|--------------------------|-----------------------|---------------|---------------|---------|------------------|
| **low**      | 512–1024                  | 128–256                | 1             | 0             | No      | 8                |
| **medium**   | 256–512                   | 256–512                | 1–2           | 8             | No      | 8                |
| **high**     | 128–256                   | 384–768                | 2–3           | 16            | Yes     | 8                |
| **extreme**  | 64–128                    | 512–1024               | 3–4           | 32            | Yes     | 8                |
| **fucked**   | 32–64                     | 768–2048               | 4–6           | 64            | Yes     | 8                |

**Descriptions:**
- *Overwrite Spacing*: How often to apply a new glitch within a chunk (smaller = more frequent)
- *Overwrite Size*: How many bytes to overwrite at each mutation site (larger = more destructive)
- *Pattern Stack*: How many patterns to concatenate for each overwrite (higher = more chaotic)
- *Chaotic Offset*: Maximum random offset added to each overwrite position (higher = more unpredictable)
- *Overlap*: Whether overwrites can overlap (yes = more intense, no = more spaced out)
- *Skip Header Bytes*: Always skip the first 8 bytes of each chunk (start corrupting from byte 9)

## Smear Mode (Temporal Drag/Smear) [EXPERIMENTAL]

**WARNING:** Smear mode is experimental and may cause video playback issues or unexpected results. Use with caution and always back up your original files.

**Smear mode** is a special corruption mode designed to create temporal drag and smear effects across video frames, with reduced chaotic jitter and improved visual persistence. When enabled:

- **Corruption is applied at the start of each frame's data** (after the chunk header)
- **Each corruption block is 1024 bytes** (large, visually persistent)
- **2–3 stable patterns** are randomly selected at the start and reused for all corruptions in this run (pattern stability)
- **Header safety:** No corruption is applied to any file offset within the first 10KB, preserving file readability
- **First 2 frames are skipped** (to avoid likely I-frames)
- **Enable with:** `--smear-mode`

**Example:**
```bash
python hex_fucker.py input.avi output.avi --smear-mode
```

This mode is ideal for creating motion drag, echo, and temporal smear effects, especially on videos with visible motion. However, it may break video playback or cause the video to play only a split second. Use at your own risk.

## FFmpeg Auto-Encode (Recommended for Smear Mode)

Some videos (especially those with frequent I-frames or heavy compression) do not smear well with hex corruption alone. The `--auto-encode` flag preprocesses your input using FFmpeg to create a new AVI with:

- **Sparse I-frames** (keyframes only every 150 frames)
- **B-frames enabled** (for temporal blending)
- **libxvid codec** (widely compatible, easy to hex-edit)
- **No audio** (video only)

This makes the file much more responsive to temporal drag, echo, and smear effects.

**How to use:**

```bash
python hex_fucker.py input.avi output.avi --auto-encode --smear-mode
```

This will:
1. Create a temporary file `temp_encoded.avi` using FFmpeg
2. Perform all hex corruption on that file
3. Clean up the temporary file after saving your output

**Highly recommended for best results with smear mode!**

## File Structure

```
hex_fuck/
├── hex_fucker.py       # Main hex fucking tool
├── demo.py             # Demonstration script
├── requirements.txt    # Dependencies (none required)
└── README.md          # This file
```

## Important Notes

### File Format Support
- **Supported**: AVI files with `00dc` frame chunks
- **Planned**: MP4, MOV support in future versions
- **Testing**: Works best with uncompressed or lightly compressed AVI files

### Safety Considerations
- **Always backup original files** - corruption is irreversible
- Start with small `--max-glitches` values to test
- Use `--log` to understand what's being modified
- Some heavily compressed formats may not glitch visibly

### Performance
- Large files (>100MB) may take several seconds to process
- Memory usage scales with file size (loads entire file into RAM)
- Complex patterns may slow down processing

## Example Results

Different hex fuck patterns create distinct visual effects:

- **whiteout/blackout**: Bright flashes, dark blocks, complete frame corruption
- **rainbow_smear**: Color bleeding, chromatic aberration, spectrum effects
- **checkerboard_flicker**: Pixelated noise, electronic distortion patterns  
- **static_grit**: Unpredictable corruption, heavy data moshing effects
- **scanline_jitter**: Horizontal distortion, TV-static-like artifacts
- **vertical_skew**: Gradient-based corruption, field-based glitches

## Troubleshooting

### "No frame chunks found"
- Ensure input is a valid AVI file
- Some AVI variants use different chunk markers
- Try with different AVI files

### "Permission denied"
- Check file permissions for input/output paths
- Ensure output directory exists and is writable

### Glitches not visible
- Increase `--glitch-size` or `--max-glitches`
- Try different `--pattern` options (use `--list-patterns` to see all)
- Some codecs are more resistant to visible corruption
- Try patterns like `whiteout` or `static_grit` for more visible effects
- Use multiple patterns for varied glitch types: `--pattern static_grit,color_burn,warp_twist`

## Future Enhancements

- Support for MP4, MOV, and other video formats
- GUI interface for visual pattern selection
- Real-time preview of glitch effects
- Audio corruption capabilities
- Export glitch maps for recreating effects

## License

This project is provided as-is for educational and artistic purposes. Use responsibly and always backup your original files.

---

**Happy Hex Fucking!** Create unique digital art by corrupting the very fabric of your videos. 
