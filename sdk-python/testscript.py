import time
from lattice_sdk import LatticeClient

# Adjust if running locally or remotely:
BASE_URL = "http://localhost:8000"
API_KEY = None  # or your hosted Lattice key if testing free hosted tier

client = LatticeClient(base_url=BASE_URL, api_key=API_KEY)


def test_basic_completion():
    print("➡️ Testing: Basic /v1/complete call")

    resp = client.complete(
        prompt="Hello Lattice! My email is test@example.com.",
        band="low"   # tests router + forced band
    )

    assert resp.text, "No response content returned"
    assert resp.provider, "Provider not set"
    assert resp.model, "Model not set"
    assert resp.cost["total_cost"] >= 0, "Cost missing or negative"
    assert resp.latency_ms > 0, "Latency missing"
    assert resp.usage["input_tokens"] >= 1, "Input tokens missing"
    assert isinstance(resp.tags, list), "Tags must be a list"

    print("   ✓ Completion works")
    print("   ✓ Provider:", resp.provider)
    print("   ✓ Model:", resp.model)
    print("   ✓ Cost:", resp.cost)
    print("   ✓ Latency:", resp.latency_ms, "ms")
    print("   ✓ Tags:", resp.tags)


def test_routing_override():
    print("\n➡️ Testing: Forced model override")

    resp = client.complete(
        prompt="Give me 3 bullet points about routing.",
        model="gpt-4o-mini"   # bypasses band
        #model="gemini-2.0-flash",   # bypasses band
    )

    assert resp.model == "gpt-4o-mini", "Override model not honored"
    print("   ✓ Model override works")


def test_cache_behavior():
    print("\n➡️ Testing: Cache alias (if enabled)")

    p = "Repeatable prompt for cache test"
    first = client.complete(prompt=p, band="low")
    time.sleep(0.5)  # ensure TTL not expired
    second = client.complete(prompt=p, band="low")

    # If cache is enabled -> second call should be MUCH faster
    print("   First latency:", first.latency_ms)
    print("   Second latency:", second.latency_ms)

    if second.latency_ms < first.latency_ms * 0.5:
        print("   ✓ Cache appears to be working")
    else:
        print("   ⚠️ Cache may be disabled or TTL expired (this is okay for dev)")


def test_metrics_endpoint():
    print("\n➡️ Testing: /v1/metrics")

    import requests
    resp = requests.get(f"{BASE_URL}/v1/metrics")
    assert resp.status_code == 200, "/v1/metrics did not return HTTP 200"

    data = resp.json()

    required_keys = [
        "total_requests", "total_cost", "average_latency_ms",
        "providers", "bands"
    ]

    for key in required_keys:
        assert key in data, f"Missing metrics key: {key}"

    print("   ✓ Metrics endpoint works")
    print("   Current metrics snapshot:")
    for k, v in data.items():
        print("   ", k, ":", v)


if __name__ == "__main__":
    print("===============================================")
    print("   LATTICE v0.3 SMOKE TEST")
    print("===============================================")

    try:
        test_basic_completion()
        test_routing_override()
        test_cache_behavior()
        test_metrics_endpoint()
        print("\n🎉 All smoke tests passed (or cache optional)! Lattice is ready.")
    except Exception as e:
        print("\n❌ Smoke test FAILED:")
        print(str(e))
        print("Fix this before shipping MVP.\n")
