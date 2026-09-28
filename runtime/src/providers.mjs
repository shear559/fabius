// The BYOK gateway — one call shape over every provider fabius runs on.
//
// One roster and one tier map, so a task routed locally picks a model the same way on
// every provider. `frontier` is the strongest widely
// released tier per provider; R11 reserves it for ambiguity, architecture, security
// and irreversible work, and takes the cheap tier for mechanical work.

import { ENV_KEY, providerKey, loadConfig, redact } from './config.mjs';

// Every id and rate below was read from the provider's OWN page on the date in its comment —
// never from memory, never from a reseller's list. Re-read the page before changing a row.
export const PROVIDERS = {
  // platform.claude.com/docs/en/models/overview (read 2026-09-28): current lineup Fable 5.1 ·
  // Opus 5.5 · Sonnet 5 · Haiku 4.5; Fable 5 and Opus 5 moved to the legacy list. Fable 5.1 bills
  // the same rate Fable 5 did, so the top rung moves at no cost.
  anthropic: { label: 'Anthropic', tiers: { frontier: 'claude-fable-5-1', mid: 'claude-sonnet-5', fast: 'claude-haiku-4-5' } },
  // `gpt-5.6` is an alias for sol — pin the explicit id so a rung can't be re-pointed under the
  // ledger. gpt-5/-mini/-nano still answer, but their dated snapshots (`gpt-5-2025-08-07` and
  // siblings) shut down 2026-12-11 with sol / terra / luna named as the replacements.
  // platform.openai.com/docs/pricing (read 2026-09-28) also lists a GPT-6 line (astra / sol /
  // luna); its rows are in PRICES so an explicit override bills honestly, but the tier defaults
  // stay on 5.6 until the maintainer re-pins — a roster move is a decision, not a price fix.
  openai: { label: 'OpenAI', tiers: { frontier: 'gpt-5.6-sol', mid: 'gpt-5.6-terra', fast: 'gpt-5.6-luna' } },
  // ai.google.dev/gemini-api/docs/models + /pricing + /deprecations (read 2026-09-28). Four GA
  // Flash generations answer; Google's own words break the tie: 3.8 Flash is "our most intelligent
  // Flash model, engineered for long-horizon software engineering" and takes `frontier`; 3.7 and
  // 3.6 are "previous-generation" — 3.6 Flash, "balancing speed and multimodal capabilities across
  // general agentic and everyday tasks", is the everyday rung and takes `mid` at the same list
  // price as 3.8; 3.5 Flash is now the "legacy Flash model" and is no longer a default. 3.5
  // Flash-Lite stays `fast`: still stable, no shutdown date announced (it is the named replacement
  // for 3.1 Flash-Lite, which shuts down 2027-05-07). There is no GA Gemini 3 Pro — the only
  // Pro-tier option is `gemini-3.1-pro-preview`, PREVIEW, so it is not a default here; name it
  // explicitly if wanted and accept preview-tier churn in exchange for Pro reasoning. The 2.5
  // line still answers and carries no announced shutdown date — a safe pin, a stale default.
  google: { label: 'Google Gemini', tiers: { frontier: 'gemini-3.8-flash', mid: 'gemini-3.6-flash', fast: 'gemini-3.5-flash-lite' } },
  // Pinned by version, never by `-latest`. An alias re-points under the ledger while the price
  // table keeps quoting the old rate — under-counting, the failure that spends the owner's money
  // instead of stopping the run: `mistral-medium-latest` moved from Medium 3 ($0.4/$2) to
  // Medium 3.5 ($1.5/$7.50) and nothing here noticed. Medium 3.5 is Mistral's frontier-class model
  // and outprices Large 3, so it takes the top rung; Large 3 sits at `mid`.
  mistral: { label: 'Mistral', tiers: { frontier: 'mistral-medium-3-5', mid: 'mistral-large-2512', fast: 'mistral-small-2603' } },
  // Llama-free since Groq shut down llama-3.3-70b-versatile and llama-3.1-8b-instant on
  // 2026-08-16 (announced 2026-06-17; free and developer tiers — committed-spend enterprise
  // contracts were exempt). `qwen/qwen3.6-27b` is Groq's other named replacement for the 70B
  // slot but sits under PREVIEW, so it is not a default here; name it explicitly if wanted.
  groq: { label: 'Groq', tiers: { frontier: 'openai/gpt-oss-120b', mid: 'openai/gpt-oss-120b', fast: 'openai/gpt-oss-20b' } },
  // One token, hundreds of open models across every partner. Any `org/name` repo id
  // passed as a custom model overrides the tier default — that is the "run any open
  // model" path. Ids are case-sensitive repo ids, read from router.huggingface.co/v1/models
  // (2026-09-28). The open rungs are the Qwen 3.5/3.6 line — Apache-2.0 across the whole
  // family, which is the doctrine's default open backbone; Llama ships under a community
  // licence with its own acceptable-use terms, so it stays an explicit override, not a default.
  huggingface: { label: 'HuggingFace', router: true, tiers: { frontier: 'openai/gpt-oss-120b', mid: 'Qwen/Qwen3.6-27B', fast: 'Qwen/Qwen3.5-9B' } },
  // openrouter.ai/api/v1/models (read 2026-09-28) — the gateway spells Anthropic ids with a dot
  // (`claude-fable-5.1`), the native API with a dash. Same generation as the first-party rungs
  // above, so a fallback through the gateway does not silently drop a generation.
  openrouter: { label: 'OpenRouter', router: true, tiers: { frontier: 'anthropic/claude-fable-5.1', mid: 'anthropic/claude-sonnet-5', fast: 'openai/gpt-5.6-luna' } },
  // Local inference. No key, no network, no cost — and no true frontier tier: whatever fits on
  // one machine is a `fast`-class model against a hosted frontier, so the local ladder is by
  // size: a 27B dense coder on top, a 35B mixture with 3B active in the middle, a 4B at the
  // bottom. Tags read from ollama.com/library (2026-09-28); same Apache-2.0 reason as the
  // HuggingFace rungs.
  ollama: { label: 'Ollama (local)', local: true, tiers: { frontier: 'qwen3.6:27b-coding', mid: 'qwen3.6:35b-a3b-coding', fast: 'qwen3.5:4b' } },
};

export const PROVIDER_ORDER = ['anthropic', 'openai', 'google', 'mistral', 'groq', 'huggingface', 'openrouter', 'ollama'];
export const TIERS = ['frontier', 'mid', 'fast'];

// [usd_in, usd_out] per 1M tokens ≡ micro-USD per token, so the ledger stays integer.
const PRICES = {
  // platform.claude.com/docs/en/about-claude/pricing (read 2026-09-28). Fable 5 and Opus 5 are
  // legacy but still answer — their rows stay so an explicit override bills honestly.
  anthropic: { 'claude-fable-5-1': [10, 50], 'claude-opus-5-5': [4, 20], 'claude-sonnet-5': [2, 10], 'claude-haiku-4-5': [1, 5], 'claude-fable-5': [10, 50], 'claude-opus-5': [5, 25] },
  // platform.openai.com/docs/pricing, Standard tier (read 2026-09-28). Superseded-but-still-live
  // ids keep their row so an explicit override still bills honestly. Rates are the PROVIDER's own
  // list price, not a gateway's resale price — the runtime calls OpenAI directly, and a reseller's
  // discounted row would under-bill every native call. Where the page prices a long-context rung
  // (sol: $4/$20 short, $8/$30 long; the GPT-6 line likewise) the ledger carries the LONG rung —
  // same policy as Google — so a long prompt can't under-bill. terra and luna carry one rate.
  openai: { 'gpt-5.6-sol': [8, 30], 'gpt-5.6-terra': [2, 12], 'gpt-5.6-luna': [0.2, 1.2], 'gpt-6-astra': [20, 75], 'gpt-6-sol': [4, 15], 'gpt-6-luna': [0.2, 0.75], 'gpt-5': [1.25, 10], 'gpt-5-mini': [0.25, 2], 'gpt-5-nano': [0.05, 0.4] },
  // ai.google.dev/gemini-api/docs/pricing (read 2026-09-28). Google tiers the Pro rate by prompt
  // length and the 3.6–3.8 Flash rate by date ($0.75/$3.75 through 2026-12-31, $1.50/$7.50 from
  // 2027-01-01); the ledger carries the HIGHER rung in both cases so a long prompt or a new year
  // can't under-bill — and that rung is what an unknown Google model falls back to.
  google: { 'gemini-3.8-flash': [1.5, 7.5], 'gemini-3.7-flash': [1.5, 7.5], 'gemini-3.6-flash': [1.5, 7.5], 'gemini-3.5-flash': [1.5, 9], 'gemini-3.5-flash-lite': [0.3, 2.5], 'gemini-3.1-pro-preview': [4, 18], 'gemini-2.5-pro': [1.25, 10], 'gemini-2.5-flash': [0.3, 2.5], 'gemini-2.5-flash-lite': [0.1, 0.4] },
  // No `-latest` row on purpose: a moving alias must MISS this table and fall to maxRate.
  mistral: { 'mistral-medium-3-5': [1.5, 7.5], 'mistral-large-2512': [0.5, 1.5], 'mistral-small-2603': [0.15, 0.6] },
  // The Llama rows stay until they stop answering: shutdown is 2026-08-16 for free and developer
  // tiers, and never for committed-spend enterprise contracts. Drop the row and an explicit
  // `llama-3.3-70b-versatile` falls to maxRate [0.15, 0.6] against a real [0.59, 0.79] — a 46%
  // under-count on the run, which is the direction that spends the owner's money.
  groq: { 'openai/gpt-oss-120b': [0.15, 0.6], 'openai/gpt-oss-20b': [0.075, 0.3], 'llama-3.3-70b-versatile': [0.59, 0.79], 'llama-3.1-8b-instant': [0.05, 0.08] },
  // router.huggingface.co/v1/models (read 2026-09-28) prices each repo PER PARTNER and the router
  // picks the partner, so a row carries the MAX over the live partners — a single partner's rate
  // would under-bill whenever the router lands elsewhere.
  huggingface: { 'openai/gpt-oss-120b': [0.35, 0.75], 'Qwen/Qwen3.6-27B': [0.47, 3.2], 'Qwen/Qwen3.5-9B': [0.17, 0.25], 'meta-llama/Llama-3.3-70B-Instruct': [1.04, 1.04], 'meta-llama/Llama-3.1-8B-Instruct': [0.06, 0.06] },
  // openrouter.ai/api/v1/models (read 2026-09-28) — the gateway's own resale rate IS the billed
  // rate here, because the runtime calls the gateway. Prior-generation rows stay for overrides.
  openrouter: { 'anthropic/claude-fable-5.1': [10, 50], 'anthropic/claude-sonnet-5': [2, 10], 'openai/gpt-5.6-luna': [0.2, 1.2], 'anthropic/claude-sonnet-4.5': [3, 15], 'openai/gpt-4.1-mini': [0.4, 1.6], 'meta-llama/llama-3.3-70b-instruct': [0.1, 0.32] },
  ollama: {},   // local inference costs no money
};

// An UNKNOWN model is estimated at the MAX rate in this provider's LOCAL table, not
// the provider's entire live catalog. A newer or more expensive model can exceed that
// estimate; provider-side spending controls are the billing boundary. A moving alias
// (`*-latest`) is kept OUT of the table so it cannot keep a stale model-specific rate.
function maxRate(table) {
  let mi = 0, mo = 0;
  for (const k of Object.keys(table)) { mi = Math.max(mi, table[k][0]); mo = Math.max(mo, table[k][1]); }
  return (mi > 0 || mo > 0) ? [mi, mo] : null;
}
export function costMicro(provider, model, usage) {
  const table = PRICES[provider];
  if (!table) return 0;
  const rate = table[model] || maxRate(table);
  if (!rate) return 0;
  const tin = Math.max(0, Number(usage?.input_tokens) || 0);
  const tout = Math.max(0, Number(usage?.output_tokens) || 0);
  return Math.round(tin * rate[0] + tout * rate[1]);
}

// Reserve the maximum a call can cost BEFORE dispatch. UTF-8 byte length is a safe
// upper bound on tokenizer output for ordinary text (a token cannot represent less than
// one encoded byte); the fixed envelope allowance covers provider message framing. The
// output token ceiling is then reduced until the whole reservation fits. Missing usage
// is charged at this reservation rather than at zero.
export function reserveCallBudget({ provider, model, system = '', messages = [], maxTokens = 2048, remainingMicro }) {
  const remaining = Math.max(0, Math.floor(Number(remainingMicro) || 0));
  const requested = Math.max(1, Math.floor(Number(maxTokens) || 1));
  if (provider === 'ollama') return { maxTokens: requested, reserveMicro: 0, inputTokenUpper: 0 };
  const envelope = JSON.stringify({ system: String(system), messages });
  const inputTokenUpper = Buffer.byteLength(envelope, 'utf8') + 256 + messages.length * 32;
  const inputOnly = costMicro(provider, model, { input_tokens: inputTokenUpper, output_tokens: 0 });
  if (inputOnly >= remaining) return null;
  let lo = 1, hi = requested, fit = 0;
  while (lo <= hi) {
    const mid = Math.floor((lo + hi) / 2);
    const cost = costMicro(provider, model, { input_tokens: inputTokenUpper, output_tokens: mid });
    if (cost <= remaining) { fit = mid; lo = mid + 1; } else hi = mid - 1;
  }
  if (!fit) return null;
  return {
    maxTokens: fit,
    reserveMicro: costMicro(provider, model, { input_tokens: inputTokenUpper, output_tokens: fit }),
    inputTokenUpper,
  };
}

function providerReady(provider, cfg, { requested = false } = {}) {
  if (!PROVIDERS[provider]) return false;
  if (provider !== 'ollama') return !!providerKey(provider, cfg);
  // Ollama is keyless, but it must be CHOSEN. Silently falling back from an unkeyed
  // cloud provider to whatever happens to answer on localhost changes both quality and
  // privacy semantics. An explicit/configured Ollama choice is ready at its default
  // localhost URL; OLLAMA_HOST merely overrides that URL.
  return requested || cfg?.provider === 'ollama' || !!providerKey('ollama', cfg);
}

export function availableProviders(cfg = loadConfig(), requestedProvider = null) {
  return PROVIDER_ORDER.filter((p) => providerReady(p, cfg, { requested: p === requestedProvider }));
}

// Resolve {provider, model, tier} honouring what is actually keyed; fall back along
// PROVIDER_ORDER to the first keyed provider. null when NOTHING is keyed.
export function resolveModel(provider, tier, cfg = loadConfig()) {
  const t = TIERS.includes(tier) ? tier : 'mid';
  const tryP = (p, requested = false) => providerReady(p, cfg, { requested }) ? { provider: p, model: PROVIDERS[p].tiers[t], tier: t } : null;
  const first = tryP(provider, true);
  if (first) return first;
  for (const p of PROVIDER_ORDER) { const r = tryP(p, false); if (r) return r; }
  return null;
}

// A custom model id overrides the tier default ONLY when the caller explicitly named
// the provider it belongs to — never paste an HF repo id onto a fallback call.
export function overrideModel(resolved, wantProvider, model) {
  const m = typeof model === 'string' ? model.trim() : '';
  if (!resolved || !m || !wantProvider || !PROVIDERS[wantProvider]) return resolved;
  if (resolved.provider !== wantProvider) return resolved;
  return { provider: resolved.provider, model: m.slice(0, 200), tier: resolved.tier };
}

const ZERO = { input_tokens: 0, output_tokens: 0 };

// ── the single call. { provider, model, system, messages, maxTokens } → { ok, output, usage, status }
export async function callLLM({ provider, model, system, messages, maxTokens = 2048, timeoutMs = 120000 }, cfg = loadConfig()) {
  const key = providerKey(provider, cfg);
  if (!key && provider !== 'ollama') return { ok: false, output: '', usage: ZERO, status: 'no-key' };
  const ac = new AbortController();
  const timer = setTimeout(() => ac.abort(), timeoutMs);
  try {
    const r = await CALLERS[provider]({ key, model, system, messages, maxTokens, signal: ac.signal });
    return r;
  } catch (e) {
    // Never surface a provider's raw error body — it can echo the key back.
    const msg = e?.name === 'AbortError' ? `timed out after ${Math.round(timeoutMs / 1000)}s` : redact(e?.message || 'unknown error', cfg);
    return { ok: false, output: '', usage: ZERO, status: 'error: ' + String(msg).slice(0, 200) };
  } finally { clearTimeout(timer); }
}

async function readJson(res) {
  const text = await res.text();
  try { return JSON.parse(text); } catch { return { __raw: text.slice(0, 400) }; }
}

// OpenAI-compatible chat/completions — used verbatim by five of the eight providers.
function openaiCompatible(url, extraHeaders = {}) {
  return async ({ key, model, system, messages, maxTokens, signal }) => {
    const res = await fetch(url, {
      method: 'POST', signal,
      headers: { 'content-type': 'application/json', authorization: `Bearer ${key}`, ...extraHeaders },
      body: JSON.stringify({
        model,
        max_tokens: maxTokens,
        messages: [{ role: 'system', content: system }, ...messages],
      }),
    });
    const d = await readJson(res);
    if (!res.ok) return { ok: false, output: '', usage: ZERO, status: `http ${res.status}` };
    const out = d.choices?.[0]?.message?.content ?? '';
    return {
      ok: true, output: String(out), status: 'done',
      usage: { input_tokens: d.usage?.prompt_tokens || 0, output_tokens: d.usage?.completion_tokens || 0 },
    };
  };
}

const CALLERS = {
  anthropic: async ({ key, model, system, messages, maxTokens, signal }) => {
    const res = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST', signal,
      headers: { 'content-type': 'application/json', 'x-api-key': key, 'anthropic-version': '2023-06-01' },
      body: JSON.stringify({ model, max_tokens: maxTokens, system, messages }),
    });
    const d = await readJson(res);
    if (!res.ok) return { ok: false, output: '', usage: ZERO, status: `http ${res.status}` };
    const out = (d.content || []).filter((b) => b.type === 'text').map((b) => b.text).join('');
    return { ok: true, output: out, status: 'done', usage: { input_tokens: d.usage?.input_tokens || 0, output_tokens: d.usage?.output_tokens || 0 } };
  },

  google: async ({ model, key, system, messages, maxTokens, signal }) => {
    const res = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${encodeURIComponent(model)}:generateContent`, {
      method: 'POST', signal,
      headers: { 'content-type': 'application/json', 'x-goog-api-key': key },
      body: JSON.stringify({
        systemInstruction: { parts: [{ text: system }] },
        contents: messages.map((m) => ({ role: m.role === 'assistant' ? 'model' : 'user', parts: [{ text: m.content }] })),
        generationConfig: { maxOutputTokens: maxTokens },
      }),
    });
    const d = await readJson(res);
    if (!res.ok) return { ok: false, output: '', usage: ZERO, status: `http ${res.status}` };
    const out = (d.candidates?.[0]?.content?.parts || []).map((p) => p.text || '').join('');
    return { ok: true, output: out, status: 'done', usage: { input_tokens: d.usageMetadata?.promptTokenCount || 0, output_tokens: d.usageMetadata?.candidatesTokenCount || 0 } };
  },

  openai: openaiCompatible('https://api.openai.com/v1/chat/completions'),
  mistral: openaiCompatible('https://api.mistral.ai/v1/chat/completions'),
  groq: openaiCompatible('https://api.groq.com/openai/v1/chat/completions'),
  huggingface: openaiCompatible('https://router.huggingface.co/v1/chat/completions'),
  openrouter: openaiCompatible('https://openrouter.ai/api/v1/chat/completions', {
    'http-referer': 'https://fabius-landing.vercel.app', 'x-title': 'fabius',
  }),

  // Local. The "key" is the host URL; absence of a key means the caller never chose it.
  ollama: async ({ key, model, system, messages, maxTokens, signal }) => {
    const host = (key && key.startsWith('http')) ? key.replace(/\/$/, '') : 'http://127.0.0.1:11434';
    const res = await fetch(`${host}/api/chat`, {
      method: 'POST', signal,
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ model, stream: false, options: { num_predict: maxTokens }, messages: [{ role: 'system', content: system }, ...messages] }),
    });
    const d = await readJson(res);
    if (!res.ok) return { ok: false, output: '', usage: ZERO, status: `http ${res.status}` };
    return {
      ok: true, output: String(d.message?.content || ''), status: 'done',
      usage: { input_tokens: d.prompt_eval_count || 0, output_tokens: d.eval_count || 0 },
    };
  },
};

export { ENV_KEY };
