import { test } from 'node:test';
import assert from 'node:assert/strict';
import { callLLM, costMicro } from '../src/providers.mjs';

test('a long-context rung is what the ledger bills, never the short rung', () => {
  // OpenAI prices gpt-5.6-sol at $4/M short and $8/M long (platform.openai.com/docs/pricing,
  // 2026-09-28); the ledger must carry the long rung or a long prompt under-bills by half.
  assert.equal(costMicro('openai', 'gpt-5.6-sol', { input_tokens: 1e6, output_tokens: 0 }), 8_000_000);
  assert.equal(costMicro('openai', 'gpt-5.6-sol', { input_tokens: 0, output_tokens: 1e6 }), 30_000_000);
  // Anthropic's own list price for Sonnet 5 is $2/$10 (platform.claude.com pricing, 2026-09-28).
  assert.equal(costMicro('anthropic', 'claude-sonnet-5', { input_tokens: 1e6, output_tokens: 1e6 }), 12_000_000);
});

test('Google API credentials travel in a header, never in the URL', async () => {
  const original = globalThis.fetch;
  let seen;
  globalThis.fetch = async (url, options) => {
    seen = { url: String(url), options };
    return new Response(JSON.stringify({ candidates: [{ content: { parts: [{ text: 'ok' }] } }], usageMetadata: {} }), {
      status: 200, headers: { 'content-type': 'application/json' },
    });
  };
  try {
    const key = 'AIzaSyntheticCredentialForHeaderOnly123456';
    const r = await callLLM({ provider: 'google', model: 'gemini-test', system: 's', messages: [], maxTokens: 1 }, { keys: { google: key } });
    assert.equal(r.ok, true);
    assert.doesNotMatch(seen.url, /AIza|[?&]key=/);
    assert.equal(seen.options.headers['x-goog-api-key'], key);
  } finally { globalThis.fetch = original; }
});

test('provider exceptions are redacted before entering status text', async () => {
  const original = globalThis.fetch;
  const key = 'sk-proj-SyntheticCredentialMaterial123456789';
  globalThis.fetch = async () => { throw new Error(`transport repeated ${key}`); };
  try {
    const r = await callLLM({ provider: 'openai', model: 'gpt-test', system: 's', messages: [], maxTokens: 1 }, { keys: { openai: key } });
    assert.equal(r.ok, false);
    assert.doesNotMatch(r.status, /SyntheticCredentialMaterial/);
    assert.match(r.status, /redacted/);
  } finally { globalThis.fetch = original; }
});
