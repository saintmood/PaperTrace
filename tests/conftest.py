import os
from pathlib import Path

import pytest
from deepeval.models.base_model import DeepEvalBaseLLM
from openai import OpenAI

from config import settings


class LocalDeepEvalModel(DeepEvalBaseLLM):
    """Bridge for DeepEval to use our local llama.cpp server."""

    def __init__(self):
        self.client = OpenAI(
            base_url=settings.test_llm_base_url, api_key=settings.test_openai_api_key
        )
        self.model_name = settings.llm_model_name

    def load_model(self):
        return self.client

    def generate(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model_name, messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content

    async def a_generate(self, prompt: str) -> str:
        # For simplicity, using sync generation in async wrapper
        return self.generate(prompt)

    def get_model_name(self):
        return "Local-Qwen-7B"


@pytest.fixture(scope="session")
def deepeval_judge():
    """Provides a single instance of the local judge for all tests."""
    return LocalDeepEvalModel()


@pytest.fixture(scope="session")
def proj_directory_path() -> str:
    return os.path.abspath(os.curdir)


@pytest.fixture(scope="session")
def test_study_path(proj_directory_path: str) -> Path:
    """Provides a path to a dummy whitepaper for testing."""
    return Path(proj_directory_path) / "tests" / "test_study.pdf"
