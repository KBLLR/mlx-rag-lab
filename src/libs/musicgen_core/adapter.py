import math
import os
from pathlib import Path
from typing import Optional

import mlx.core as mx

from .musicgen_mlx import MusicGen   # or `from musicgen import MusicGen` if in same pkg
from .utils import save_audio        # your MLX-style save_audio


class MusicgenAdapter:
    """
    Thin adapter around MLX MusicGen that:
    - Loads a MusicGen model (optionally from a local cache dir)
    - Exposes a duration-based generate_music(prompt, duration_s, output_dir) API
    - Ensures the written .wav has ~duration_s seconds of audio
    """

    def __init__(
        self,
        model_id: str = "facebook/musicgen-small",
        local_model_dir: str = "mlx-models",
    ) -> None:
        self.model_id = model_id
        self.local_model_dir = Path(local_model_dir)

        # Handle 'melody' model_id which is 'facebook/musicgen-melody' not 'facebook/musicgen-melody'
        if model_id.lower() == "melody":
            hf_model_id = "facebook/musicgen-melody"
        else:
            hf_model_id = f"facebook/musicgen-{model_id}"

        # Try local first, then fall back to HF
        local_path = self.local_model_dir / hf_model_id.split("/")[-1]
        if local_path.exists():
            print(f"Loading MusicGen model from local path: {local_path}")
            self.model = MusicGen.from_pretrained(str(local_path))
        else:
            print(f"Loading MusicGen model from {hf_model_id}...")
            self.model = MusicGen.from_pretrained(hf_model_id)
            # Optionally: cache to disk yourself if you want

        print("Musicgen model loaded.")

    @property
    def sampling_rate(self) -> int:
        return self.model.sampling_rate

    def _seconds_to_steps(self, duration_s: float) -> int:
        """
        Convert desired seconds into MusicGen steps.

        MusicGen uses EnCodec 32kHz with 4 codebooks at 50 Hz,
        so there are ~50 steps per second. The MLX devs explicitly
        recommend using this rule-of-thumb.
        """
        if duration_s <= 0:
            raise ValueError(f"duration must be positive, got {duration_s}")
        steps_per_second = 50.0
        return max(1, int(math.ceil(duration_s * steps_per_second)))

    def _postprocess_duration(
        self,
        audio: mx.array,
        duration_s: float,
    ) -> mx.array:
        """
        Crop or pad the waveform to match the requested duration in samples.
        """
        sr = self.sampling_rate
        target_n = int(round(duration_s * sr))

        # Ensure 1D (MusicGen returns shape (num_samples,))
        if audio.ndim > 1:
            # collapse extra dims if something weird happened
            audio = audio.reshape(-1)

        n = int(audio.shape[0])

        if n > target_n:
            # Too long -> crop
            audio = audio[:target_n]
        elif n < target_n:
            # Too short -> zero-pad at the end
            pad = target_n - n
            audio = mx.pad(audio, (0, pad))

        return audio

    def generate_music(
        self,
        prompt: str,
        duration_s: float,
        output_dir: str,
        seed: int = -1,
        top_k: int = 250,
        temp: float = 1.0,
        guidance_coef: float = 3.0,
    ) -> str:
        """
        Generate music from a text prompt and save a .wav file.

        Returns the absolute path of the generated file.
        """
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

        max_steps = self._seconds_to_steps(duration_s)

        print(
            f"Generating music for: {prompt!r} with duration {duration_s}s "
            f"(max_steps={max_steps})..."
        )

        audio = self.model.generate(
            prompt,
            max_steps=max_steps,
            seed=seed,
            top_k=top_k,
            temp=temp,
            guidance_coef=guidance_coef,
        )

        # audio is mx.array of shape (num_samples,)
        audio = self._postprocess_duration(audio, duration_s)

        # Construct a reasonably safe filename
        safe_prompt = "".join(
            c if c.isalnum() or c in ("-", "_") else "_" for c in prompt.strip()
        )[:50]
        filename = f"musicgen_{safe_prompt or 'sample'}_{int(duration_s)}s.wav"
        output_path = output_dir_path / filename

        print(f"Saving generated audio to: {output_path}")
        save_audio(str(output_path), audio, self.sampling_rate)

        return str(output_path.resolve())
