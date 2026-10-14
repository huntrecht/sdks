/**
 * Smoke tests for the Huntrecht TypeScript SDK (mocked fetch — no network).
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { HuntrechtClient } from './client.js';
import { SDK_VERSION } from './version.js';

function mockJson(body: unknown, status = 200) {
  return Promise.resolve(new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  }));
}

describe('SDK_VERSION', () => {
  it('matches package.json', async () => {
    const pkg = await import('../package.json');
    expect(SDK_VERSION).toBe(pkg.version);
  });
});

describe('CreditRiskAPI', () => {
  let client: HuntrechtClient;
  let lastUrl: string;

  beforeEach(() => {
    client = new HuntrechtClient({ accessToken: 'test-token' });
    // Pretend the token is fresh (expiry gate is private).
    (client as unknown as Record<string, unknown>)._tokenExpiresAt =
      Date.now() + 3600_000;
    lastUrl = '';
    vi.stubGlobal('fetch', (url: string) => {
      lastUrl = url;
      return mockJson({ ok: true });
    });
  });

  it('getScore hits /api/v1/credit-risk/score', async () => {
    await client.creditRisk.getScore('cust-1');
    expect(lastUrl).toContain('/api/v1/credit-risk/score');
    expect(lastUrl).toContain('customer_id=cust-1');
  });

  it('assess posts to /api/v1/credit-risk/assess', async () => {
    await client.creditRisk.assess({ customer_id: 'c', amount: 100 });
    expect(lastUrl).toContain('/api/v1/credit-risk/assess');
  });

  it('getHistory hits data-connect with limit', async () => {
    await client.creditRisk.getHistory('cust-1', { limit: 5 });
    expect(lastUrl).toContain('/api/v1/data-connect/credit-history');
    expect(lastUrl).toContain('limit=5');
  });

  it('company assessment + improvement endpoints', async () => {
    await client.creditRisk.getAssessment('u-1');
    expect(lastUrl).toContain('/api/v1/company/credit-assessment');
    await client.creditRisk.requestAssessment({ user_id: 'u-1' });
    expect(lastUrl).toContain('/api/v1/company/credit-assessment/request');
    await client.creditRisk.getImprovementOptions();
    expect(lastUrl).toContain('/api/v1/credit-improvement/available-options');
    await client.creditRisk.connectWallet({ customer_id: 'c' });
    expect(lastUrl).toContain('/api/v1/credit-improvement/connect-wallet');
    await client.creditRisk.applyBoosts({ customer_id: 'c' });
    expect(lastUrl).toContain('/api/v1/credit-improvement/apply-boosts');
  });
});

describe('GreenCloudAPI', () => {
  let client: HuntrechtClient;
  let lastUrl: string;
  let lastInit: RequestInit | undefined;

  beforeEach(() => {
    client = new HuntrechtClient({ accessToken: 'test-token' });
    (client as unknown as Record<string, unknown>)._tokenExpiresAt =
      Date.now() + 3600_000;
    vi.stubGlobal('fetch', (url: string, init?: RequestInit) => {
      lastUrl = url;
      lastInit = init;
      return mockJson({ ok: true });
    });
  });

  it('pricing hits the public feed without auth', async () => {
    await client.greencloud.pricing();
    expect(lastUrl).toContain('/api/v1/greencloud/pricing');
    expect(lastInit?.headers).not.toMatchObject({ Authorization: expect.anything() });
  });

  it('calculateEstimate posts sku/nodes/term', async () => {
    await client.greencloud.calculateEstimate({ sku: 'GC-H200', nodes: 20, termMonths: 6 });
    expect(lastUrl).toContain('/api/v1/greencloud/calculator');
    expect(lastInit?.method).toBe('POST');
    expect(String(lastInit?.body)).toContain('"term_months":6');
  });

  it('rejects terms outside 3/6/12/24/36', async () => {
    await expect(client.greencloud.calculateEstimate({ sku: 'GC-H200', termMonths: 9 })).rejects.toThrow();
  });
});
