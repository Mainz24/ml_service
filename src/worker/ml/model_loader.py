from llama_cpp import Llama
from functools import lru_cache
import os
from huggingface_hub import utils, hf_hub_download

utils.logging.set_verbosity_info()
utils.logging.set_verbosity_debug()

_model = None
# Параметры репозитория HF
REPO_ID = "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF"
FILENAME = "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"

def load_model():
    global _model
    if _model is not None:
        return

    try:
        model_path = hf_hub_download(
            repo_id=REPO_ID,
            filename=FILENAME,
        )
        print(f"Model successfully retrieved/downloaded to: {model_path}")
    except Exception as e:
        print(f"Error downloading model: {e}")
        raise RuntimeError("Failed to load model from Hugging Face.")

    _model = Llama(
        model_path=model_path,
        n_ctx=2048,          # максимальный контекст
        n_threads=2,         # количество CPU-потоков
        n_gpu_layers=0,      # 0 = только CPU
        verbose=False
    )


def generate_response(prompt: str) -> str:
    if _model is None:
        load_model()

    messages = [
        {"role": "user", "content": prompt}
    ]

    response = _model.create_chat_completion(
        messages=messages,
        max_tokens=128,
        temperature=0.7,
        top_p=0.95,
        stop=["<|end|>"]
    )

    return response["choices"][0]["message"]["content"].strip()


@lru_cache(maxsize=128)
def cached_generate_response(prompt: str) -> str:
    return generate_response(prompt)