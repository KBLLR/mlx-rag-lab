from typing import Any, List, Union, Iterator
from mlx_lm import load, generate, stream_generate
import os

class MLXModelEngine:
    def __init__(self, model_id: str, model_type: str = "text", **kwargs: Any) -> None:
        self.model_id = model_id
        self.model_type = model_type
        self.model = None
        self.tokenizer = None
        self._load_model(**kwargs)

    def _load_model(self, **kwargs: Any) -> None:
        if self.model_type == "text":
            self.model, self.tokenizer = load(self.model_id, **kwargs)
        else:
            raise ValueError(f"Unsupported model type: {self.model_type}")

    def _normalize_output(self, output: Union[str, List[str]]) -> str:
        # mlx_lm.generate may return a single string or a list of strings
        if isinstance(output, list):
            text = "".join(output)
        else:
            text = str(output)

        text = text.strip()

        # keep your “take first answer” heuristic
        if "\n\n<|assistant|>" in text:
            final = text.split("\n\n<|assistant|>:", 1)[0].strip()
        elif "\n\n" in text:
            final = text.split("\n\n", 1)[0].strip()
        else:
            final = text

        return final.replace("\n", " ").strip()

    def generate(self, prompt: str, max_tokens: int = 512, **kwargs: Any) -> str:
        if self.model_type != "text":
            raise ValueError(f"Unsupported model type: {self.model_type}")

        raw = generate(
            self.model,
            self.tokenizer,
            prompt=prompt,
            verbose=False,
            max_tokens=max_tokens,
            **kwargs,
        )
        return self._normalize_output(raw)

    def stream_generate(self, prompt: str, max_tokens: int = 512, **kwargs: Any) -> Iterator[str]:
        if self.model_type != "text":
            raise ValueError(f"Unsupported model type: {self.model_type}")

        for chunk in stream_generate(
            self.model,
            self.tokenizer,
            prompt=prompt,
            verbose=False,
            max_tokens=max_tokens,
            **kwargs,
        ):
            # chunk may be string or list-like; yield normalized incremental piece
            yield "".join(chunk) if isinstance(chunk, list) else str(chunk)