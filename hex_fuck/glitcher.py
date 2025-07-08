import struct
import random
from typing import List, Tuple, Dict
from dataclasses import dataclass

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
        from intensity import get_intensity_params
        self.intensity_params = get_intensity_params(config.intensity)
        self.smear_mode = smear_mode
        self.smear_patterns = None  # Will be set per run

    def find_frame_chunks(self, data: bytes) -> List[Tuple[int, int]]:
        """
        Find all '00dc' frame data chunks in AVI file
        Returns list of (offset, size) tuples
        """
        chunks = []
        pattern = b'00dc'
        offset = 0
        while True:
            pos = data.find(pattern, offset)
            if pos == -1:
                break
            if pos + 8 <= len(data):
                try:
                    chunk_size = struct.unpack('<I', data[pos + 4:pos + 8])[0]
                    chunks.append((pos, chunk_size))
                except struct.error:
                    pass
            offset = pos + 1
        return chunks

    def apply_intensity_glitches(self, data: bytearray, chunk_offset: int, chunk_size: int) -> int:
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
            spacing = random.randint(p['overwrite_spacing_min'], p['overwrite_spacing_max'])
            chaos = random.randint(0, p['chaos_offset']) if p['chaos_offset'] > 0 else 0
            offset = data_start + pos + chaos
            if offset >= data_end:
                break
            overwrite_size = random.randint(p['overwrite_size_min'], p['overwrite_size_max'])
            if offset + overwrite_size > data_end:
                overwrite_size = data_end - offset
            if overwrite_size <= 0:
                break
            stack_count = random.randint(p['pattern_stack_min'], p['pattern_stack_max'])
            patterns = [random.choice(self.config.patterns) for _ in range(stack_count)]
            pattern_bytes = b''.join(patterns)
            if len(pattern_bytes) < overwrite_size:
                repeats = (overwrite_size + len(pattern_bytes) - 1) // len(pattern_bytes)
                pattern_bytes = (pattern_bytes * repeats)[:overwrite_size]
            else:
                pattern_bytes = pattern_bytes[:overwrite_size]
            if not p['overlap']:
                if any(o in used_offsets for o in range(offset, offset+overwrite_size)):
                    pos += spacing
                    continue
                used_offsets.update(range(offset, offset+overwrite_size))
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
        file_offset = chunk_offset + 8 + smear_offset
        if file_offset < 102400:
            return 0
        data_start = chunk_offset + 8
        data_end = chunk_offset + 8 + chunk_size
        if file_offset + 1024 > data_end:
            return 0
        if file_offset + 1024 > len(data):
            return 0
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
        selected = []
        if self.config.target_strategy == 'every_nth':
            n = max(1, self.config.target_value)
            selected = list(range(0, total_frames, n))
        elif self.config.target_strategy == 'random':
            percentage = max(0, min(100, self.config.target_value))
            count = int(total_frames * percentage / 100)
            selected = random.sample(range(total_frames), min(count, total_frames))
        elif self.config.target_strategy == 'time_offset':
            start_frame = max(0, min(total_frames - 1, self.config.target_value))
            selected = list(range(start_frame, total_frames))
        if self.config.max_glitches > 0:
            selected = selected[:self.config.max_glitches]
        return sorted(selected)

    def fuck_video(self, input_path: str, output_path: str) -> bool:
        try:
            with open(input_path, 'rb') as f:
                data = bytearray(f.read())
            print(f"Loaded video file: {len(data):,} bytes")
            chunks = self.find_frame_chunks(data)
            print(f"Found {len(chunks)} frame chunks")
            if not chunks:
                print("No frame chunks found. Is this a valid AVI file?")
                return False
            frames_to_glitch = self.select_frames_to_glitch(len(chunks))
            print(f"Targeting {len(frames_to_glitch)} frames for hex fucking")
            if self.smear_mode:
                if len(self.config.patterns) <= 3:
                    self.smear_patterns = self.config.patterns
                else:
                    self.smear_patterns = random.sample(self.config.patterns, k=random.randint(2, 3))
                print(f"[Smear Mode] Using {len(self.smear_patterns)} stable patterns for this run.")
                smear_offset = 0
                smear_step_min = 4000
                smear_step_max = 8000
                smear_applied = 0
                skip_first_n = 2
                for i, frame_idx in enumerate(frames_to_glitch):
                    if i < skip_first_n:
                        continue
                    if frame_idx < len(chunks):
                        chunk_offset, chunk_size = chunks[frame_idx]
                        smear_offset += random.randint(smear_step_min, smear_step_max)
                        pattern = self.smear_patterns[i % len(self.smear_patterns)]
                        smear_applied += self.apply_smear_glitch(data, chunk_offset, chunk_size, smear_offset, pattern)
                print(f"[Smear Mode] Applied {smear_applied} smear hex fucks")
            else:
                glitches_applied = 0
                for frame_idx in frames_to_glitch:
                    if frame_idx < len(chunks):
                        chunk_offset, chunk_size = chunks[frame_idx]
                        glitches_applied += self.apply_intensity_glitches(data, chunk_offset, chunk_size)
                print(f"Applied {glitches_applied} hex fucks")
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
        if not self.glitch_log:
            print("No hex fucks were applied.")
            return
        print(f"\nHex Fuck Log ({len(self.glitch_log)} entries):")
        print("-" * 60)
        for i, entry in enumerate(self.glitch_log, 1):
            print(f"{i:3d}. Offset: 0x{entry['offset']:08x} | "
                  f"Size: {entry['size']:2d} bytes | "
                  f"Pattern: {entry['pattern'][:16]}...") 