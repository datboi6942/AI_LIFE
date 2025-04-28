"""Tests the procedural sound generation and caching."""
from __future__ import annotations

import pytest
import hashlib
import arcade
from unittest.mock import patch, MagicMock

# Ensure pyglet is available as it's used indirectly by arcade sound
try:
    import pyglet
except ImportError:
    pyglet = None

from hive_game.hive import sound
from hive_game.hive.game_window import GameWindow # For type hint in play_chirp mock

# --- Fixtures ---
@pytest.fixture(autouse=True)
def clear_sound_cache():
    """Ensures the sound cache is empty before each test."""
    sound.sound_cache.clear()

@pytest.fixture
def mock_arcade_load_sound():
    """Mocks arcade.load_sound to return a dummy object and capture input."""
    mock_sound_obj = MagicMock(spec=arcade.Sound)
    with patch('arcade.load_sound', return_value=mock_sound_obj) as mock_load:
        yield mock_load, mock_sound_obj

@pytest.fixture
def mock_arcade_play_sound():
    """Mocks arcade.play_sound."""
    with patch('arcade.play_sound') as mock_play:
        yield mock_play

# --- Test Cases ---
@pytest.mark.skipif(pyglet is None, reason="pyglet not installed, cannot test sound loading")
def test_get_sound_generates_and_caches(mock_arcade_load_sound):
    """Verify get_or_generate_sound generates, caches, and returns sound."""
    mock_load, mock_sound_obj = mock_arcade_load_sound
    chirp_id = 42

    # First call: should generate
    result1 = sound.get_or_generate_sound(chirp_id)
    assert result1 is mock_sound_obj, "Did not return the mocked sound object on first call"
    mock_load.assert_called_once() # Check that arcade.load_sound was called
    assert chirp_id in sound.sound_cache, "Sound not added to cache"
    assert sound.sound_cache[chirp_id] is mock_sound_obj, "Incorrect object in cache"

    # Second call: should return from cache
    result2 = sound.get_or_generate_sound(chirp_id)
    assert result2 is mock_sound_obj, "Did not return the mocked sound object on second call"
    # Assert that load_sound was NOT called again
    mock_load.assert_called_once() # Still only called once

@pytest.mark.skipif(pyglet is None, reason="pyglet not installed, cannot test sound loading")
def test_sound_generation_is_deterministic(mock_arcade_load_sound):
    """Verify generating sound for the same ID yields identical WAV bytes."""
    mock_load, _ = mock_arcade_load_sound
    chirp_id = 88 # Use a different ID

    # Generate first time
    sound.get_or_generate_sound(chirp_id)
    assert mock_load.call_count == 1
    # Extract the BytesIO object passed to load_sound
    args1, kwargs1 = mock_load.call_args
    wav_stream1 = args1[0]
    wav_bytes1 = wav_stream1.getvalue()
    hash1 = hashlib.sha256(wav_bytes1).hexdigest()

    # Clear cache and generate second time
    sound.sound_cache.clear()
    mock_load.reset_mock()
    sound.get_or_generate_sound(chirp_id)
    assert mock_load.call_count == 1
    args2, kwargs2 = mock_load.call_args
    wav_stream2 = args2[0]
    wav_bytes2 = wav_stream2.getvalue()
    hash2 = hashlib.sha256(wav_bytes2).hexdigest()

    # Assert WAV bytes are identical
    assert len(wav_bytes1) > 44, "Generated WAV bytes seem too short (missing data?)"
    assert wav_bytes1 == wav_bytes2, "Generated WAV bytes differ between calls for the same ID"
    assert hash1 == hash2, "Hashes of generated WAV bytes differ"

@pytest.mark.skipif(pyglet is None, reason="pyglet not installed, cannot test sound loading")
def test_waveform_type_alternates(mock_arcade_load_sound):
    """Verify square wave for even IDs, sine for odd IDs."""
    mock_load, _ = mock_arcade_load_sound

    # Even ID (expect square wave characteristics)
    chirp_id_even = 100
    sound.get_or_generate_sound(chirp_id_even)
    args_even, _ = mock_load.call_args
    wav_bytes_even = args_even[0].getvalue()
    # Simple check: square wave likely has long runs of 0x00 and 0xFF
    data_bytes_even = wav_bytes_even[44:] # Skip header
    assert b'\xff\xff\xff' in data_bytes_even or b'\x00\x00\x00' in data_bytes_even, \
        f"Even ID {chirp_id_even} did not seem to produce square wave bytes"

    sound.sound_cache.clear()
    mock_load.reset_mock()

    # Odd ID (expect sine wave characteristics)
    chirp_id_odd = 101
    sound.get_or_generate_sound(chirp_id_odd)
    args_odd, _ = mock_load.call_args
    wav_bytes_odd = args_odd[0].getvalue()
    data_bytes_odd = wav_bytes_odd[44:]
    # Sine wave should vary more smoothly, less likely to have long runs of max/min
    # Check if it contains values other than 0 and 255 frequently
    non_boundary_values = [b for b in data_bytes_odd if b != 0 and b != 255]
    assert len(non_boundary_values) / len(data_bytes_odd) > 0.5, \
        f"Odd ID {chirp_id_odd} did not seem to produce sine wave bytes"

@pytest.mark.skipif(pyglet is None, reason="pyglet not installed, cannot test sound loading")
def test_play_chirp_calls_get_and_play(mock_arcade_load_sound, mock_arcade_play_sound):
    """Verify play_chirp gets the sound and calls arcade.play_sound."""
    _, mock_sound_obj = mock_arcade_load_sound
    chirp_id = 123
    mock_gw = MagicMock(spec=GameWindow) # Mock game window ref

    sound.play_chirp(chirp_id, mock_gw)

    # Assert get_or_generate_sound was implicitly called by play_chirp (checked via load mock)
    mock_arcade_load_sound[0].assert_called_once()
    # Assert play_sound was called with the generated object
    mock_arcade_play_sound.assert_called_once_with(mock_sound_obj) 