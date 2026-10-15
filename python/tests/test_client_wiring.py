"""Wiring + path tests for the Python SDK (mocked transport, no network)."""
import json

import httpx
import pytest

from huntrecht import HuntrechtClient


def _client(seen):
    client = HuntrechtClient(base_url="https://api.test",
                             access_token="tok")
    client._token_expires_at = 9999999999.0

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path,
                     dict(request.url.params),
                     request.content.decode() if request.content else None))
        return httpx.Response(200, json={"ok": True})

    client._http = httpx.Client(
        transport=httpx.MockTransport(handler),
        base_url="https://api.test/api/v1")
    return client


def test_all_resources_wired():
    client = HuntrechtClient(base_url="https://api.test",
                             access_token="tok")
    for name in ("auth", "clients", "orders", "payments", "subscriptions",
                 "credit", "kyc", "quotes", "users", "storefront",
                 "price_drops", "greencloud", "arena", "app_proxy",
                 "linked_payments"):
        assert getattr(client, name, None) is not None, name


def test_greencloud_pricing_and_calculator():
    seen = []
    client = _client(seen)
    client.greencloud.pricing()
    assert seen[-1][:2] == ("GET", "/api/v1/greencloud/pricing")
    client.greencloud.calculate_estimate("GC-H200", nodes=20, term_months=6)
    method, path, _, body = seen[-1]
    assert (method, path) == ("POST", "/api/v1/greencloud/calculator")
    assert json.loads(body) == {"sku": "GC-H200", "nodes": 20,
                                "term_months": 6}
    with pytest.raises(ValueError):
        client.greencloud.calculate_estimate("GC-H200", term_months=9)


def test_arena_settle_and_reconcile():
    seen = []
    client = _client(seen)
    client.arena.settle("o1", 10.5)
    method, path, _, body = seen[-1]
    assert (method, path) == ("POST", "/api/v1/arena/orders/o1/settle")
    assert json.loads(body) == {"settlement_price": 10.5}
    client.arena.reconcile(limit=10, dry_run=False)
    method, path, params, _ = seen[-1]
    assert (method, path) == ("POST", "/api/v1/arena/validation/reconcile")
    assert params.get("limit") == "10"
