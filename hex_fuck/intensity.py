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