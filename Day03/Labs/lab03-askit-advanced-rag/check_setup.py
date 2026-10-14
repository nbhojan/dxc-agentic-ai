"""Run this before the lab: python check_setup.py
Checks configured AWS Bedrock, OpenAI, and Azure AI Foundry providers."""
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[3] / ".env")   # course .env (AWS keys, BEDROCK_SMALL_MODEL_ID)
load_dotenv()

from rag import config  # noqa: E402
from rag.llm import LLM, bedrock_ready  # noqa: E402


def check(llm):
    t = time.time()
    v = llm.embed(["hello"], op="check")[0]
    print(f"OK embeddings  {llm.embed_model}: dim={len(v)} ({time.time() - t:.1f}s)")
    t = time.time()
    msg, row = llm.chat([{"role": "user", "content": 'Reply with JSON {"ok": true}'}], op="check", json_mode=True)
    print(f"OK chat        {llm.chat_model}: {msg.content!r} tokens={row['input_tokens']}+{row['output_tokens']} ({time.time() - t:.1f}s)")


ok = False
if bedrock_ready():
    try:
        check(LLM(provider="bedrock", cache_dir=".cache_check"))
        ok = True
    except Exception as e:
        print(f"Bedrock FAILED: {str(e)[:300]}")
else:
    print("Bedrock not configured: need AWS keys and BEDROCK_SMALL_MODEL_ID in the course .env")
if os.getenv("OPENAI_API_KEY"):
    try:
        check(LLM(os.getenv("OPENAI_API_KEY"), cache_dir=".cache_check"))
        ok = True
    except Exception as e:
        print(f"OpenAI FAILED: {str(e)[:300]}")
foundry_key = os.getenv("AZURE_AI_FOUNDRY_API_KEY")
foundry_endpoint = os.getenv("AZURE_AI_FOUNDRY_ENDPOINT")
if foundry_key and foundry_endpoint:
    try:
        check(LLM(foundry_key, provider="azure_foundry", base_url=foundry_endpoint,
                  cache_dir=".cache_check"))
        ok = True
    except Exception as e:
        print(f"Azure AI Foundry FAILED: {str(e)[:300]}")
elif foundry_key or foundry_endpoint:
    print("Azure AI Foundry not configured: set both AZURE_AI_FOUNDRY_API_KEY and AZURE_AI_FOUNDRY_ENDPOINT")
if not ok:
    sys.exit("No working provider. Ask the trainer. (The app still runs in offline mode.)")
print("All good. Start the app with: streamlit run app.py")
