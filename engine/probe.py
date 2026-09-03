"""
Diagnostic: what can this API key actually do?

Runs before generation in the test workflow. One cheap call that answers three
questions at once: is the key valid, which image models exist, and what methods
do they support. Costs nothing and turns a blind "exit code 1" into a fact.
"""
from __future__ import annotations
import os, sys, requests

BASE = "https://generativelanguage.googleapis.com/v1beta"


def main() -> int:
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        print("FAIL: GEMINI_API_KEY is empty. Check the repo secret name is exactly "
              "GEMINI_API_KEY (Settings > Secrets and variables > Actions).")
        return 1

    print(f"key present: {len(key)} chars, starts {key[:6]}...")
    try:
        r = requests.get(f"{BASE}/models", headers={"x-goog-api-key": key},
                         params={"pageSize": 200}, timeout=60)
    except Exception as e:
        print(f"FAIL: could not reach the API at all: {e}")
        return 1

    print(f"GET /models -> HTTP {r.status_code}")
    if r.status_code != 200:
        print(r.text[:1200])
        if r.status_code in (400, 403):
            print("\nThat usually means the key is invalid, or the Generative "
                  "Language API is not enabled on its Google Cloud project.")
        return 1

    models = r.json().get("models", [])
    print(f"{len(models)} models visible to this key\n")

    image_models = [m for m in models if "image" in m.get("name", "").lower()]
    print("--- IMAGE-CAPABLE MODELS ---")
    if not image_models:
        print("NONE. This key cannot generate images.")
    for m in image_models:
        name = m["name"].removeprefix("models/")
        methods = ",".join(m.get("supportedGenerationMethods", []) or ["?"])
        print(f"  {name:38s} methods: {methods}")

    print("\n--- ALL MODEL IDS ---")
    for m in models:
        print("  " + m["name"].removeprefix("models/"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
