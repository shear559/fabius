#!/usr/bin/env node
// Original Fabius dependency scheduler. Execution exists only through a caller's runner.
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const fail = message => { throw new TypeError(message); };
const object = value => value !== null && typeof value === 'object' && !Array.isArray(value);
const poison = key => ['__proto__', 'prototype', 'constructor'].includes(key);
const identifier = value => typeof value === 'string' && /^[a-z][a-z0-9_-]{0,63}$/.test(value) && !poison(value);
const text = (value, limit, label) => { if (typeof value !== 'string' || !value.trim() || value.length > limit) fail(`${label}: expected non-empty text up to ${limit} characters`); };
function keys(value, allowed, label) {
  if (!object(value)) fail(`${label}: expected object`);
  for (const key of Object.keys(value)) if (!allowed.includes(key)) fail(`${label}: unknown key ${key}`);
}
function unique(values, label) {
  if (!Array.isArray(values) || new Set(values).size !== values.length) fail(`${label}: expected array without duplicate values`);
}
function freeze(value) {
  if (value && typeof value === 'object') { for (const item of Object.values(value)) freeze(item); Object.freeze(value); }
  return value;
}

// Reject accessors/toJSON/custom prototypes rather than invoking untrusted conversion code.
function snapshot(value, label, maxBytes) {
  const seen = new Set(); let nodes = 0;
  function copy(item, depth) {
    if (++nodes > 10000 || depth > 16) fail(`${label}: JSON complexity limit exceeded`);
    if (item === null || typeof item === 'boolean') return item;
    if (typeof item === 'number') { if (!Number.isFinite(item)) fail(`${label}: numbers must be finite`); return item; }
    if (typeof item === 'string') { if (Buffer.byteLength(item) > maxBytes) fail(`${label}: byte limit exceeded`); return item; }
    if (typeof item !== 'object') fail(`${label}: expected JSON data`);
    if (seen.has(item)) fail(`${label}: cyclic JSON data`);
    const array = Array.isArray(item), proto = Object.getPrototypeOf(item);
    if (!array && proto !== Object.prototype && proto !== null) fail(`${label}: expected plain JSON object`);
    seen.add(item);
    const result = array ? [] : {}, descriptors = Object.getOwnPropertyDescriptors(item);
    for (const key of Reflect.ownKeys(descriptors)) {
      if (array && key === 'length') continue;
      const descriptor = descriptors[key];
      if (typeof key !== 'string' || poison(key) || !descriptor.enumerable || !Object.hasOwn(descriptor, 'value')) fail(`${label}: only ordinary JSON data properties are allowed`);
      if (array && (!/^(0|[1-9][0-9]*)$/.test(key) || Number(key) >= item.length)) fail(`${label}: invalid array property`);
      result[key] = copy(descriptor.value, depth + 1);
    }
    if (array && Object.keys(descriptors).length !== item.length + 1) fail(`${label}: sparse arrays are not JSON data`);
    seen.delete(item); return result;
  }
  const result = copy(value, 0);
  if (Buffer.byteLength(JSON.stringify(result)) > maxBytes) fail(`${label}: byte limit exceeded`);
  return freeze(result);
}

function schemaCheck(schema, label, depth = 0) {
  if (depth > 8) fail(`${label}: schema depth exceeds 8`);
  const allowed = { object: ['properties', 'required', 'additionalProperties'], array: ['items', 'maxItems'], string: ['maxLength', 'enum'], integer: ['enum'], number: ['enum'], boolean: ['enum'], null: ['enum'] };
  if (!object(schema) || !Object.hasOwn(allowed, schema.type)) fail(`${label}: unsupported schema type`);
  keys(schema, ['type', ...allowed[schema.type]], label);
  if (schema.type === 'object') {
    if (!object(schema.properties) || Object.keys(schema.properties).length > 32) fail(`${label}: expected at most 32 properties`);
    if (schema.additionalProperties !== false) fail(`${label}: additionalProperties must be false`);
    unique(schema.required, `${label}.required`);
    if (!schema.required.every(key => typeof key === 'string' && Object.hasOwn(schema.properties, key))) fail(`${label}: required fields must exist in properties`);
    for (const [key, child] of Object.entries(schema.properties)) schemaCheck(child, `${label}.${key}`, depth + 1);
  } else if (schema.type === 'array') {
    if (!Number.isInteger(schema.maxItems) || schema.maxItems < 0 || schema.maxItems > 256) fail(`${label}: maxItems must be 0..256`);
    schemaCheck(schema.items, `${label}[]`, depth + 1);
  } else {
    if (schema.type === 'string' && Object.hasOwn(schema, 'maxLength') && (!Number.isInteger(schema.maxLength) || schema.maxLength < 0 || schema.maxLength > 8192)) fail(`${label}: maxLength must be 0..8192`);
    if (Object.hasOwn(schema, 'enum')) {
      unique(schema.enum, `${label}.enum`);
      if (!schema.enum.length || schema.enum.length > 32) fail(`${label}: enum must contain 1..32 values`);
      for (const value of schema.enum) outputCheck(value, { type: schema.type }, label);
    }
  }
}

function outputCheck(value, schema, label) {
  const matches = schema.type === 'null' ? value === null : schema.type === 'array' ? Array.isArray(value)
    : schema.type === 'object' ? object(value) : schema.type === 'integer' ? Number.isInteger(value) : typeof value === schema.type;
  if (!matches) fail(`${label}: expected ${schema.type}`);
  if (schema.enum && !schema.enum.includes(value)) fail(`${label}: value is outside enum`);
  if (schema.type === 'object') {
    for (const key of schema.required) if (!Object.hasOwn(value, key)) fail(`${label}: missing field ${key}`);
    for (const [key, child] of Object.entries(value)) {
      if (!Object.hasOwn(schema.properties, key)) fail(`${label}: unexpected field ${key}`);
      outputCheck(child, schema.properties[key], `${label}.${key}`);
    }
  } else if (schema.type === 'array') {
    if (value.length > schema.maxItems) fail(`${label}: maxItems exceeded`);
    value.forEach((item, index) => outputCheck(item, schema.items, `${label}[${index}]`));
  } else if (schema.type === 'string' && value.length > (schema.maxLength ?? 8192)) fail(`${label}: maxLength exceeded`);
}

/** Validate and return an immutable copy plus deterministic dependency order/layers. */
export function validatePlan(input) {
  const plan = snapshot(input, 'plan', 262144);
  keys(plan, ['schema', 'agents', 'tasks'], 'plan');
  if (plan.schema !== 'fabius-cohort/v1') fail('plan.schema: expected fabius-cohort/v1');
  if (!Array.isArray(plan.agents) || !plan.agents.length || plan.agents.length > 32) fail('plan.agents: expected 1..32 definitions');
  if (!Array.isArray(plan.tasks) || !plan.tasks.length || plan.tasks.length > 64) fail('plan.tasks: expected 1..64 tasks');
  const agents = new Set(), tasks = new Map();
  for (const agent of plan.agents) {
    keys(agent, ['id', 'description', 'instructions', 'tools', 'permissions', 'output'], 'agent');
    if (!identifier(agent.id) || agents.has(agent.id)) fail('invalid or duplicate agent id');
    agents.add(agent.id); text(agent.description, 1024, `${agent.id}.description`); text(agent.instructions, 8192, `${agent.id}.instructions`);
    unique(agent.tools, `${agent.id}.tools`);
    if (agent.tools.length > 32 || !agent.tools.every(tool => typeof tool === 'string' && /^[a-zA-Z][a-zA-Z0-9_.:-]{0,79}$/.test(tool))) fail(`${agent.id}: invalid tool allowlist`);
    keys(agent.permissions, ['read', 'write', 'execute', 'network'], `${agent.id}.permissions`);
    for (const cap of ['read', 'write', 'execute', 'network']) if (!['allow', 'ask', 'deny'].includes(agent.permissions[cap])) fail(`${agent.id}.permissions.${cap}: expected allow, ask or deny`);
    schemaCheck(agent.output, `${agent.id}.output`);
    if (agent.output.type !== 'object') fail(`${agent.id}.output: top-level output must be object`);
  }
  for (const task of plan.tasks) {
    keys(task, ['id', 'agent', 'input', 'dependsOn'], 'task');
    if (!identifier(task.id) || tasks.has(task.id)) fail('invalid or duplicate task id');
    if (!agents.has(task.agent)) fail(`${task.id}: unknown agent`);
    if (!object(task.input)) fail(`${task.id}.input: expected object`);
    unique(task.dependsOn, `${task.id}.dependsOn`);
    tasks.set(task.id, task);
  }
  for (const task of plan.tasks) for (const dep of task.dependsOn) if (!tasks.has(dep)) fail(`${task.id}: unknown dependency ${dep}`);
  const order = [], levels = [], done = new Set();
  while (done.size < tasks.size) {
    const level = plan.tasks.filter(task => !done.has(task.id) && task.dependsOn.every(id => done.has(id))).map(task => task.id);
    if (!level.length) fail('plan contains a dependency cycle');
    levels.push(level); order.push(...level); level.forEach(id => done.add(id));
  }
  return freeze({ plan, order, levels });
}

/** Execute only through caller-owned policy/runner functions. No built-in tools or models. */
export async function executePlan(input, { runner, authorize, concurrency = 2, signal } = {}) {
  const { plan } = validatePlan(input);
  if (typeof runner !== 'function') fail('runner must be an explicitly supplied function');
  if (typeof authorize !== 'function') fail('authorize must be an explicitly supplied synchronous function');
  if (!Number.isInteger(concurrency) || concurrency < 1 || concurrency > 16) fail('concurrency must be 1..16');
  if (signal !== undefined && !(signal instanceof AbortSignal)) fail('signal must be an AbortSignal');
  let cancelled = false;
  // The shared signal notifies callbacks; private state decides scheduling.
  const controller = new AbortController(), abort = () => { cancelled = true; controller.abort(); };
  signal?.addEventListener('abort', abort, { once: true });
  if (signal?.aborted) abort();
  const agents = new Map(plan.agents.map(agent => [agent.id, agent]));
  const states = Object.fromEntries(plan.tasks.map(task => [task.id, { status: 'pending' }]));
  const active = new Map(), terminalFailure = state => ['failed', 'denied', 'blocked', 'cancelled'].includes(state.status);
  function launch(task) {
    states[task.id] = { status: 'running' };
    const agent = agents.get(task.agent);
    const dependencies = Object.freeze(Object.fromEntries(task.dependsOn.map(id => [id, snapshot(states[id].output, `dependency ${id}`, 65536)])));
    const frame = Object.freeze({ task, agent, dependencies, signal: controller.signal });
    const pending = (async () => {
      let stage = 'authorize';
      try {
        const allowed = authorize(frame);
        if (typeof allowed !== 'boolean') {
          // Reject async policies; consume a rejected promise to avoid an unhandled rejection.
          if (allowed instanceof Promise) allowed.catch(() => {});
          fail('authorize must return a boolean synchronously');
        }
        if (cancelled) { states[task.id] = { status: 'cancelled' }; return; }
        if (!allowed) { states[task.id] = { status: 'denied' }; return; }
        stage = 'runner';
        const raw = await runner(frame);
        if (cancelled) { states[task.id] = { status: 'cancelled' }; return; }
        stage = 'output';
        const output = snapshot(raw, `${task.id}.output`, 65536);
        outputCheck(output, agent.output, `${task.id}.output`);
        states[task.id] = { status: 'succeeded', output };
      } catch (error) {
        states[task.id] = cancelled ? { status: 'cancelled' }
          : { status: 'failed', error: { stage, message: String(error?.message ?? error).slice(0, 1000) } };
      }
    })().finally(() => active.delete(task.id));
    active.set(task.id, pending);
  }
  try {
    while (active.size || Object.values(states).some(state => state.status === 'pending')) {
      for (const task of plan.tasks) {
        if (states[task.id].status !== 'pending') continue;
        if (cancelled) { states[task.id] = { status: 'cancelled' }; continue; }
        const blockedBy = task.dependsOn.filter(id => terminalFailure(states[id]));
        if (blockedBy.length) { states[task.id] = { status: 'blocked', blockedBy }; continue; }
        if (active.size < concurrency && task.dependsOn.every(id => states[id].status === 'succeeded')) launch(task);
      }
      if (active.size) await Promise.race(active.values());
    }
  } finally { signal?.removeEventListener('abort', abort); }
  const status = cancelled ? 'cancelled' : Object.values(states).every(state => state.status === 'succeeded') ? 'succeeded' : 'failed';
  return freeze({ status, tasks: states });
}

if (process.argv[1] && pathToFileURL(resolve(process.argv[1])).href === import.meta.url) {
  try {
    const [command, filename, ...extra] = process.argv.slice(2);
    if (!['check', 'plan'].includes(command) || !filename || extra.length) fail('usage: node cohort.mjs check|plan <plan.json>');
    const bytes = readFileSync(filename);
    if (bytes.length > 262144) fail('plan: byte limit exceeded');
    const checked = validatePlan(JSON.parse(bytes));
    console.log(JSON.stringify(command === 'check' ? { ok: true, tasks: checked.plan.tasks.length, agents: checked.plan.agents.length } : checked, null, 2));
  } catch (error) { console.error(JSON.stringify({ ok: false, error: String(error.message) })); process.exitCode = 1; }
}
