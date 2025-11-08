import json
from typing import Any, List, Union, Iterator, Dict
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

    def _normalize_output(self, output: Union[str, List[str]]) -> Union[str, List[Dict[str, str]]]:
        if isinstance(output, list):
            text = "".join(output)
        else:
            text = str(output)

        text = text.strip()

        # Attempt to parse as JSON first
        try:
            parsed_json = json.loads(text)
            return parsed_json
        except json.JSONDecodeError:
            pass # Fallback to text normalization if not valid JSON

        # Existing text normalization heuristic
        if "\n\n<|assistant|>":
            final = text.split("\n\n<|assistant|>".strip(), 1)[0].strip()
        elif "\n\n" in text:
            final = text.split("\n\n", 1)[0].strip()
        else:
            final = text

        return final.replace("\n", " ").strip()

    def generate(self, prompt: str, max_tokens: int = 512, **kwargs: Any) -> Union[str, List[Dict[str, str]]]:
        if self.model_type != "text":
            raise ValueError(f"Unsupported model type: {self.model_type}")

        raw = generate(
            self.model,
            self.tokenizer,
            prompt=prompt,
            max_tokens=max_tokens,
            **kwargs,
        )
        return self._normalize_output(raw)

    def stream_generate(self, prompt: str, max_tokens: int = 512, **kwargs: Any) -> Iterator[str]:
        if self.model_type != "text":
            raise ValueError(f"Unsupported model type: {self.model_type}")

        # The underlying stream_generate yields objects; we iterate and yield the text attribute.
        for token_obj in stream_generate(
            self.model,
            self.tokenizer,
            prompt=prompt,
            max_tokens=max_tokens,
            **kwargs,
        ):
            yield token_obj.text