# Musicgen Integration Fix Session - 2025-11-08

## Problem

Three failure modes were encountered while integrating the MLX MusicGen example into the monorepo:

1.  `AttributeError: 'EncodecModel' object has no attribute 'decode'`
2.  `AttributeError: 'EncodecModel' object has no attribute 'chunk_length'`
3.  Incorrect generated audio length: for a requested 3 seconds at 32 kHz, the file had 238080 samples instead of ~96000, causing the unit test's duration check to fail.

All exceptions originated from `mlx.nn.Module.__getattr__`, indicating that the attributes were genuinely missing from the effective `EncodecModel` instance.

## Root Causes (Confirmed Against Upstream)

### 1. EncodecModel Drift

The local `src/libs/musicgen_core/encodec_model.py` had diverged significantly from the official `mlx-examples` EnCodec implementation. The upstream `EncodecModel` defines `_encode_frame`, `encode`, `_linear_overlap_add`, `_decode_frame`, properties (`channels`, `sampling_rate`, `chunk_length`, `chunk_stride`), `decode(...)`, and `from_pretrained(...)`. The local version had inconsistent method definitions, scope issues with properties, and introduced brittle hacks, leading to attributes not being present on the instantiated class.

### 2. Wrong Time → Token Mapping in the Adapter

The MLX MusicGen example controls audio length via `max_steps`, not a direct `duration` argument. MusicGen uses an EnCodec tokenizer at 32 kHz with 4 codebooks, sampled at 50 Hz, meaning approximately 50 steps per second of audio. The `MusicgenAdapter` was using an incorrect `max_steps` heuristic, resulting in the generation of far more steps than needed for the requested duration.

## Fix

### 1. EncodecModel: Alignment with Upstream

The `EncodecModel` in `src/libs/musicgen_core/encodec_model.py` was completely replaced with a faithful version of the upstream MLX EnCodec example. This included:

*   A correct `_linear_overlap_add` method for windowed overlap-add reconstruction.
*   A correct `_decode_frame(codes, scale)` method for decoding single frames.
*   Recovery of the four key properties: `channels`, `sampling_rate`, `chunk_length`, and `chunk_stride`, ensuring they are correctly attached and accessible.
*   Implementation of the main `decode(audio_codes, audio_scales, padding_mask)` method to handle both single-frame and chunked decoding, utilizing `_decode_frame` and `_linear_overlap_add`.
*   Fixing `from_pretrained` to match the MLX pattern for loading models from local paths or Hugging Face repositories, including proper configuration loading, model instantiation, weight loading, and `mx.eval(model)` before processor creation.

This ensures that `MusicGen.__init__` can safely call `self._audio_decoder, _ = EncodecModel.from_pretrained(...)` and subsequent `audio = self._audio_decoder.decode(...)` calls function as expected without missing attributes.

### 2. MusicgenAdapter: Correct Duration Mapping

The `MusicgenAdapter` in `src/libs/musicgen_core/adapter.py` was updated to correctly respect the `~50 steps/sec` specification:

*   The `max_steps` in `MusicgenAdapter` is now computed as `int(duration_seconds * 50)` (with appropriate rounding/ceiling).
*   This `max_steps` value is passed to `MusicGen.generate(...)`.
*   A `_postprocess_duration` method was added to crop or pad the returned waveform to exactly `duration * sampling_rate` samples before saving, ensuring the API truly delivers "duration in seconds."

## Result

The `MusicGen` now utilizes a clean, upstream-compatible `EncodecModel`, and the `MusicgenAdapter` correctly maps user-facing duration (seconds) to model-facing `max_steps` (tokens), ensuring the resulting waveform duration matches expectations.

The unit test `tests/musicgen/test_musicgen_adapter.py::test_musicgen_adapter_generation` now passes, confirming:

*   `.wav` file creation under `./var/test_music_output`.
*   `samplerate == adapter.model.sampling_rate` (32 kHz).
*   Audio has content (`audio_data.size > 0`).
*   `abs(audio_data.shape[0] - duration * samplerate) < samplerate` holds, meaning the duration is within ±1 second.

The pipeline is now consistent with MLX + MusicGen theory and the project's own tests.