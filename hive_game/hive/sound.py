"""
Handles procedural generation, caching, and playback of chirp sounds.
"""
from __future__ import annotations

import logging
import math
import array
import struct
import io
import os
import tempfile
from typing import Dict, Optional, TYPE_CHECKING, Union

import arcade
import pyglet # For StaticSource

if TYPE_CHECKING:
    from hive_game.hive.game_window import GameWindow

log = logging.getLogger(__name__)

# Cache for generated arcade.Sound objects, keyed by chirp ID (int)
sound_cache: Dict[int, arcade.Sound] = {}

SAMPLE_RATE = 8000 # Hz
BITS_PER_SAMPLE = 8
CHANNELS = 1 # Mono

def _generate_sine_wave(frequency: float, num_samples: int, sample_rate: int) -> array.array:
    """Generates raw PCM data for a sine wave (8-bit unsigned)."""
    raw_data = array.array("B") # Array of unsigned bytes
    for i in range(num_samples):
        time_s = i / sample_rate
        # Value = 127 + 127 * sin(2πf*t)
        # Scale to 0-255 for unsigned 8-bit
        sine_val = math.sin(2.0 * math.pi * frequency * time_s)
        byte_val = int(127.5 + 127.0 * sine_val)
        raw_data.append(max(0, min(255, byte_val))) # Clamp just in case
    return raw_data

def _generate_square_wave(frequency: float, num_samples: int, sample_rate: int) -> array.array:
    """Generates raw PCM data for a square wave (8-bit unsigned)."""
    raw_data = array.array("B") # Array of unsigned bytes
    period_samples = sample_rate / frequency
    half_period_samples = period_samples / 2.0
    for i in range(num_samples):
        # Position within the current period
        pos_in_period = i % period_samples
        # Value is 255 for first half, 0 for second half
        byte_val = 255 if pos_in_period < half_period_samples else 0
        raw_data.append(byte_val)
    return raw_data

def _build_wav_bytes(pcm_data: array.array, sample_rate: int) -> bytes:
    """Prepends a minimal WAV header to 8-bit mono PCM data."""
    num_samples = len(pcm_data)
    data_size = num_samples # Since BITS_PER_SAMPLE is 8
    bytes_per_sample = BITS_PER_SAMPLE // 8
    block_align = CHANNELS * bytes_per_sample
    byte_rate = sample_rate * block_align

    # Full size = 36 + data_size (minimum header size)
    riff_chunk_size = 36 + data_size

    header = struct.pack(
        "<4sI4s"    # RIFF chunk descriptor (RIFF, chunk_size, WAVE)
        "4sIHHIIHH" # fmt chunk descriptor (fmt , 16, 1, channels, sample_rate, byte_rate, block_align, bits_per_sample)
        "4sI",      # data chunk descriptor (data, data_size)
        b"RIFF",
        riff_chunk_size,
        b"WAVE",
        b"fmt ",
        16, # Subchunk1Size for PCM
        1,  # AudioFormat (1 for PCM)
        CHANNELS,
        sample_rate,
        byte_rate,
        block_align,
        BITS_PER_SAMPLE,
        b"data",
        data_size
    )
    return header + pcm_data.tobytes()

def get_or_generate_sound(chirp_id: int, return_bytes: bool = False) -> Union[Optional[arcade.Sound], bytes]:
    """Gets a cached sound or generates it procedurally based on the chirp ID.
    
    Args:
        chirp_id: The ID of the chirp to generate
        return_bytes: If True, returns the raw WAV bytes instead of loading a sound
        
    Returns:
        Either an arcade.Sound object or raw WAV bytes if return_bytes is True
    """
    if not return_bytes and chirp_id in sound_cache:
        return sound_cache[chirp_id]

    log.debug(f"Generating sound for chirp ID {chirp_id}")

    # 1. Determine parameters from ID
    frequency = 400.0 + 2.0 * chirp_id
    duration_ms = 60 + (chirp_id % 3) * 20
    waveform_type = "square" if chirp_id % 2 == 0 else "sine"

    # 2. Synthesize samples
    num_samples = int(SAMPLE_RATE * (duration_ms / 1000.0))
    if waveform_type == "sine":
        pcm_data = _generate_sine_wave(frequency, num_samples, SAMPLE_RATE)
    else: # square
        pcm_data = _generate_square_wave(frequency, num_samples, SAMPLE_RATE)

    # 3. Pack into WAV bytes
    wav_bytes = _build_wav_bytes(pcm_data, SAMPLE_RATE)
    
    if return_bytes:
        return wav_bytes

    # 4. Save to temporary file and load it as a sound
    try:
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_file.write(wav_bytes)
            temp_path = temp_file.name
        
        sound = arcade.load_sound(temp_path)
        sound_cache[chirp_id] = sound
        
        # Clean up the temporary file
        try:
            os.unlink(temp_path)
        except Exception as e:
            log.warning(f"Failed to delete temporary WAV file {temp_path}: {e}")
            
        log.debug(f"Generated and cached sound for chirp ID {chirp_id}")
        return sound
    except Exception as e:
        log.error(f"Error loading generated WAV for chirp ID {chirp_id}: {e}")
        return None

def play_chirp(chirp_id: int, game_window: GameWindow) -> None:
    """Plays the procedurally generated sound for the given chirp ID."""
    sound = get_or_generate_sound(chirp_id)
    if sound:
        try:
            # TODO: Consider volume/pan based on distance if needed later.
            arcade.play_sound(sound)
        except Exception as e:
            # Handle potential issues if audio device is unavailable, etc.
            log.error(f"Error playing generated sound for chirp ID {chirp_id}: {e}") 