from types import ModuleType, SimpleNamespace

import pytest

from rag.llm import LLM


def _install_fake_openai(monkeypatch):
    clients = []

    class FakeOpenAI:
        def __init__(self, api_key, base_url=None):
            self.api_key = api_key
            self.base_url = base_url
            self.chat_requests = []
            self.embedding_requests = []
            self.chat = SimpleNamespace(
                completions=SimpleNamespace(
                    create=lambda **kwargs: self._chat(kwargs)
                )
            )
            self.embeddings = SimpleNamespace(
                create=lambda **kwargs: self._embed(kwargs)
            )
            clients.append(self)

        def _chat(self, kwargs):
            self.chat_requests.append(kwargs)
            return SimpleNamespace(
                usage=SimpleNamespace(prompt_tokens=3, completion_tokens=2),
                choices=[SimpleNamespace(message=SimpleNamespace(content="ok", tool_calls=None))],
            )

        def _embed(self, kwargs):
            self.embedding_requests.append(kwargs)
            return SimpleNamespace(
                usage=SimpleNamespace(prompt_tokens=2),
                data=[SimpleNamespace(embedding=[0.1, 0.2]) for _ in kwargs["input"]],
            )

    module = ModuleType("openai")
    module.OpenAI = FakeOpenAI
    monkeypatch.setitem(__import__("sys").modules, "openai", module)
    return clients


def test_azure_foundry_uses_configured_openai_compatible_endpoint(monkeypatch, tmp_path):
    clients = _install_fake_openai(monkeypatch)
    llm = LLM(
        "foundry-key",
        chat_model="chat-deployment",
        embed_model="embedding-deployment",
        provider="azure_foundry",
        base_url="https://example.services.ai.azure.com/models/v1/",
        cache_dir=str(tmp_path),
    )

    assert clients[0].api_key == "foundry-key"
    assert clients[0].base_url == "https://example.services.ai.azure.com/models/v1"

    message, _ = llm.chat([{"role": "user", "content": "hello"}])
    assert message.content == "ok"
    assert clients[0].chat_requests[0]["model"] == "chat-deployment"
    assert llm.embed(["hello"]).tolist() == [[0.1, 0.2]]
    assert clients[0].embedding_requests[0]["model"] == "embedding-deployment"


@pytest.mark.parametrize(
    ("api_key", "base_url"),
    [("", "https://example.com/v1"), ("foundry-key", "")],
)
def test_azure_foundry_requires_key_and_endpoint(api_key, base_url, tmp_path):
    with pytest.raises(ValueError, match="requires an API key and an OpenAI-compatible endpoint URL"):
        LLM(api_key, provider="azure_foundry", base_url=base_url, cache_dir=str(tmp_path))


def test_azure_foundry_embedding_cache_is_endpoint_specific(monkeypatch, tmp_path):
    _install_fake_openai(monkeypatch)
    first = LLM("key", provider="azure_foundry", base_url="https://first.example/v1",
                cache_dir=str(tmp_path))
    second = LLM("key", provider="azure_foundry", base_url="https://second.example/v1",
                 cache_dir=str(tmp_path))

    assert first._cache_path() != second._cache_path()
