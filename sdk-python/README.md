# lattice-sdk

Lightweight Python client for the Lattice Dev Edition API.

## Install

```bash
pip install lattice-sdk
# or for local development
pip install -e .
```

## Usage

```python
from lattice_sdk import LatticeClient

client = LatticeClient()  # defaults to http://localhost:8000
result = client.complete(
    prompt="Classify the following text as pii/non-pii.",
    band="low",
)
print(result.text, result.cost["total_cost"], result.tags)
```

The legacy `rajos` import path continues to work via a shim that re-exports `LatticeClient` and `CompleteResult`.
