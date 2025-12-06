# RAJOS Python SDK

Developer-first helpers for talking to the local RAJOS backend.

## Install

```bash
pip install -e .
```

## Usage

```python
from rajos import RajosClient, trace_llm_call

client = RajosClient()  # defaults to http://localhost:8000
client.list_traces(limit=10)

@trace_llm_call(provider="openai", model="gpt-4o-mini")
def ask(prompt: str, rajos_metadata=None):
    return call_my_llm(prompt)
```

Pass `rajos_metadata` when calling the wrapped function to add run-specific metadata into the stored trace.
