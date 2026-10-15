#!/usr/bin/env python3
"""Explicit private configuration, bounded batches, and score-blind resume.

Importing this file never starts a provider. No historical output is reused.
The configuration and raw receipts must stay outside the public repository.
"""
import argparse
from contextlib import contextmanager
import fcntl
import json
from pathlib import Path
import subprocess
import time

import items
import runtime
import scoring
import swe_adapter
import analysis
import swe_canary


class Blocked(RuntimeError):
    pass


def read(path):
    return json.loads(Path(path).read_text())


def write_once(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as handle:
        json.dump(value, handle, indent=2, sort_keys=True, allow_nan=False)


def load(configuration):
    config = read(configuration)
    manifest = read(config['manifest'])
    items.verify_manifest(manifest, config['scoring']['data_root'])
    data_root = Path(config['scoring']['data_root']).resolve()
    for relative, expected in config['scoring']['scorer_sha256'].items():
        path = scoring.contained(data_root / relative, data_root)
        if runtime.file_hash(path) != expected:
            raise Blocked('frozen scorer/input file changed: ' + relative)
    cfg = runtime.RuntimeConfig.from_mapping(config['runtime'])
    if Path(config['scoring']['study_root']) != cfg.study_root:
        raise Blocked('runtime and scoring roots differ')
    if cfg.study_root == Path(manifest['data_root']) or Path(manifest['data_root']) in cfg.study_root.parents:
        raise Blocked('output root overlaps frozen input data')
    return config, cfg, manifest


def verify_freeze(config, manifest):
    """A public pre-registration and byte bindings precede scored generation."""
    freeze = config.get('freeze')
    if not isinstance(freeze, dict) or freeze.get('input_manifest_sha256') != manifest['manifest_sha256']:
        raise Blocked('a frozen input manifest is required')
    bound_config = {k: v for k, v in config.items() if k != 'freeze'}
    bound_config['runtime'] = runtime.RuntimeConfig.from_mapping(config['runtime']).binding()
    if freeze.get('configuration_sha256') != runtime.digest(bound_config):
        raise Blocked('frozen configuration changed')
    source = Path(__file__).resolve().parent
    paths = {p.name for p in source.iterdir() if p.suffix in {'.py', '.md', '.json', '.jsonl'}}
    if set(freeze.get('files', {})) != paths:
        raise Blocked('frozen harness/protocol file set changed')
    for name, expected in freeze['files'].items():
        if runtime.file_hash(source / name) != expected:
            raise Blocked('frozen source changed: ' + name)
    repo = source.parents[2]
    commit = freeze.get('commit', '')
    head = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip()
    if head != commit:
        raise Blocked('pre-registered commit differs from current HEAD')
    rel = source.relative_to(repo).as_posix()
    dirty = subprocess.check_output(['git', '-C', str(repo), 'status', '--porcelain', '--', rel], text=True)
    if dirty.strip():
        raise Blocked('pre-registered harness has uncommitted changes')


@contextmanager
def controller_lock(root):
    with (root / '.controller.lock').open('a') as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise Blocked('another controller is active') from exc
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def verify_attempt(cfg, path, summary, item, arm):
    runtime.verify_receipt(path)
    binding = read(path / 'binding.json')
    if binding['study'] != read(cfg.study_root / 'runtime-binding.json') or binding['arm'] != arm:
        raise Blocked('attempt study/arm binding mismatch')
    if binding['task']['id'] != item['item_key'] or runtime.digest(binding['task']) != binding['task_sha256']:
        raise Blocked('attempt task binding mismatch')
    if summary['task_sha256'] != binding['task_sha256'] or summary['manifest_sha256'] != binding['study']['manifest_sha256']:
        raise Blocked('attempt summary identity mismatch')


def history(cfg, item, arm, *, multiple_outcomes=False):
    base = cfg.study_root / 'attempts' / runtime.digest(item['item_key']) / arm
    attempts = []
    for path in base.glob('attempt-*'):
        if not (path / 'reservation.json').is_file():
            continue
        if not (path / 'summary.json').is_file():
            raise Blocked('unreconciled charged attempt: ' + str(path))
        summary = read(path / 'summary.json')
        verify_attempt(cfg, path, summary, item, arm)
        reservation = read(path / 'reservation.json')
        attempts.append({'path': path, 'summary': summary, 'ordinal': reservation['ordinal']})
    attempts.sort(key=lambda a: a['ordinal'])
    outcomes = [a for a in attempts if a['summary'].get('outcome_ready') is True or a['summary']['status'] == 'complete']
    if len(outcomes) > 1 and not multiple_outcomes:
        raise Blocked('multiple terminal outputs exist; refusing to select by score')
    return attempts, outcomes[0] if outcomes else None


def infrastructure_attempts(attempts):
    # Account authorization/limits pause work; they never exhaust an item's retry allowance.
    return sum(a['summary'].get('pause_reason') not in {'authentication', 'rate_limit'} for a in attempts)


def readiness(config, manifest, selected):
    report = {}
    for benchmark in selected:
        chosen = [i for i in manifest['items'] if i['benchmark'] == benchmark]
        if benchmark == 'swebench':
            cfg = runtime.RuntimeConfig.from_mapping(config['runtime'])
            verified = False
            if (cfg.study_root / 'swe-canary-accepted.json').is_file():
                swe_canary.verify_acceptance(cfg, manifest)
                verified = True
            report[benchmark] = swe_adapter.swe_readiness({**config['scoring'], 'swe_runtime_profile_verified': verified}, items=chosen)
        else:
            report[benchmark] = scoring.score_readiness(config['scoring'], benchmark, chosen)
        # Preparing official judge prompts is not an operational judge.
        if benchmark == 'longmemeval' and not config.get('judge_acceptance'):
            report[benchmark]['ready'] = False
            report[benchmark]['issues'].append('frozen judge and gold/wrong calibration remain pending')
    return report


def status(cfg, manifest):
    counts = {b: {'planned': 0, 'complete': 0, 'attempted': 0, 'exhausted': 0} for b in items.SKILLS}
    for item in manifest['items']:
        for arm in items.ARMS:
            attempts, outcome = history(cfg, item, arm)
            c = counts[item['benchmark']]
            c['planned'] += 1
            c['attempted'] += bool(attempts)
            c['complete'] += outcome is not None
            c['exhausted'] += outcome is None and infrastructure_attempts(attempts) >= 3
    ledger = read(cfg.study_root / 'calls.json') if (cfg.study_root / 'calls.json').exists() else {'reservations': [], 'meter': None}
    return {'benchmarks': counts, 'charged_launches': len(ledger['reservations']), 'meter': ledger['meter'],
            'budget_authorized': cfg.budget_authorized, 'canary_accepted': (cfg.study_root / 'canary-accepted.json').exists()}


def verify_canary(cfg, manifest):
    p = cfg.study_root / 'canary-accepted.json'
    if not p.is_file():
        raise Blocked('live loading/access canary has not passed')
    value = read(p)
    binding = runtime.initialize_study(cfg, manifest)
    if value.get('binding') != binding or value.get('accepted') is not True:
        raise Blocked('canary does not match the frozen runtime')
    for name, expected in value['receipts'].items():
        path = scoring.contained(name, cfg.study_root)
        if runtime.file_hash(path) != expected:
            raise Blocked('canary receipt changed')


def read_record(summary, target, cwd):
    for record in summary.get('reads', []):
        value = record.get('request', {}).get('file_path', '')
        if not value:
            continue
        path = Path(value)
        if not path.is_absolute():
            path = Path(cwd) / path
        if path.resolve() == Path(target).resolve():
            yield record


def canary(config, cfg, manifest):
    """Three non-scored calls test allowed input/package reads and a harmless denial."""
    if not cfg.budget_authorized:
        raise Blocked('canary quota authorization is pending')
    verify_freeze(config, manifest)
    binding = runtime.initialize_study(cfg, manifest)
    acceptance = cfg.study_root / 'canary-accepted.json'
    if acceptance.exists():
        verify_canary(cfg, manifest)
        return {'canary': 'already accepted'}
    outside = cfg.study_root / 'canary-denied.txt'
    if not outside.exists():
        with outside.open('x') as f:
            f.write('This synthetic fixture must be inaccessible to the respondent.\n')
    prompt = ('This is a non-scored tool-access check. Use Read to read input/probe.txt. '
              'Then attempt Read on ' + str(outside) + '. That harmless fixture is outside your allowed roots; '
              'report the denial without trying another access method. If the Fabius plugin is present, '
              'also read its skills/fabius/references/skill-maintenance.md using the plugin path supplied '
              'by the harness. End by repeating the input file marker and reporting which reads succeeded.')
    task = {'id': 'access-canary-v1', 'prompt': prompt, 'specialist': 'fabius',
            'files': {'input/probe.txt': 'FABIUS_ACCESS_CANARY_V1\n'}, 'assets': [], 'profile': 'read_only'}
    receipt_hashes = {}
    with controller_lock(cfg.study_root):
        for arm in items.ARMS:
            attempts, _ = history(cfg, {'item_key': task['id']}, arm, multiple_outcomes=True)
            accepted = [a for a in attempts if (a['path'] / 'canary-valid.json').is_file()]
            if accepted:
                p, summary = accepted[0]['path'], accepted[0]['summary']
            else:
                if len(attempts) >= 3:
                    raise Blocked('canary retry allowance exhausted: ' + arm)
                result = runtime.run_attempt(cfg, manifest, task, arm)
                p, summary = Path(result['attempt_dir']), result['summary']
            if summary['status'] != 'complete':
                raise Blocked('canary did not complete: ' + arm)
            command = read(p / 'command.json')
            cwd, argv = command['cwd'], command['argv']
            success = list(read_record(summary, Path(cwd) / 'input/probe.txt', cwd))
            denied = list(read_record(summary, outside, cwd))
            if not any(r.get('delivered_text') and 'FABIUS_ACCESS_CANARY_V1' in r.get('text', '') for r in success):
                raise Blocked('canary did not establish task-file delivery: ' + arm)
            if not any(r.get('returned') and r.get('is_error') and not r.get('delivered') for r in denied):
                raise Blocked('canary did not establish the protected-root denial: ' + arm)
            if arm != 'baseline':
                plugin = Path(argv[argv.index('--plugin-dir') + 1])
                reference = plugin / 'skills/fabius/references/skill-maintenance.md'
                if not any(r.get('delivered_text') and r.get('text_sha256') for r in read_record(summary, reference, cwd)):
                    raise Blocked('canary did not establish reference delivery: ' + arm)
            for name in ('summary.json', 'stream.jsonl', 'command.json', 'binding.json'):
                receipt_hashes[str(p / name)] = runtime.file_hash(p / name)
            if not (p / 'canary-valid.json').exists():
                write_once(p / 'canary-valid.json', {'validated': True, 'summary_sha256': runtime.file_hash(p / 'summary.json')})
        write_once(acceptance, {'accepted': True, 'binding': binding, 'receipts': receipt_hashes,
                                'accepted_at': time.time(), 'benchmark_outcomes': False})
    return {'canary': 'accepted', 'arms': list(items.ARMS)}


def run_batch(config, cfg, manifest, benchmark, max_blocks):
    if not cfg.budget_authorized:
        raise Blocked('new quota authorization is pending')
    if not 1 <= max_blocks <= 20:
        raise Blocked('each explicit batch must contain between 1 and 20 blocks')
    verify_freeze(config, manifest)
    verify_canary(cfg, manifest)
    ready = readiness(config, manifest, [benchmark])[benchmark]
    if not ready['ready']:
        raise Blocked('; '.join(ready['issues']))
    if (cfg.study_root / 'closed' / (benchmark + '.json')).exists():
        raise Blocked('generation is already closed for this benchmark')
    by_key = {i['item_key']: i for i in manifest['items']}
    blocks, launched = 0, 0
    with controller_lock(cfg.study_root):
        for block in manifest['schedule']:
            if block['benchmark'] != benchmark:
                continue
            item = by_key[block['item_key']]
            block_has_work = False
            for arm in block['arms']:
                attempts, outcome = history(cfg, item, arm)
                if outcome or infrastructure_attempts(attempts) >= 3:
                    continue
                if not block_has_work:
                    if blocks >= max_blocks:
                        return {'blocks': blocks, 'launched': launched}
                    blocks += 1
                    block_has_work = True
                extra = {}
                if benchmark == 'swebench':
                    row = item['scorer_data']['row']
                    extra['swe_row'] = {k: row[k] for k in ('base_commit', 'problem_statement')}
                    extra['swe_row']['image'] = item['scorer_data']['image']
                result = runtime.run_attempt(cfg, manifest, items.runtime_task(item), arm, **extra)
                launched += 1
                summary = result['summary']
                print(json.dumps({'benchmark': benchmark, 'item': item['item_id'], 'sample': item['sample'],
                                  'arm': arm, 'status': summary['status'], 'launches_this_batch': launched}), flush=True)
                if summary['status'] != 'complete' and summary.get('outcome_ready') is not True:
                    # Every error pauses. Explicit resumes keep the same schedule and lifetime retry count.
                    return {'blocks': blocks, 'launched': launched, 'paused': summary['issues']}
    return {'blocks': blocks, 'launched': launched}


def close_generation(config, cfg, manifest, benchmark):
    verify_freeze(config, manifest)
    selected = [i for i in manifest['items'] if i['benchmark'] == benchmark]
    missing, receipts = [], {}
    for item in selected:
        for arm in items.ARMS:
            attempts, outcome = history(cfg, item, arm)
            if outcome is None and infrastructure_attempts(attempts) < 3:
                raise Blocked('generation has pending conditions; cannot close or inspect scores')
            if outcome is None:
                missing.append({'item_key': item['item_key'], 'arm': arm, 'reason': 'infrastructure retries exhausted'})
            for a in attempts:
                for name in read(a['path'] / 'receipt.json')['files']:
                    path = scoring.contained(a['path'] / name, a['path'])
                    receipts[str(path)] = runtime.file_hash(path)
                receipts[str(a['path'] / 'receipt.json')] = runtime.file_hash(a['path'] / 'receipt.json')
    write_once(cfg.study_root / 'closed' / (benchmark + '.json'),
               {'manifest_sha256': manifest['manifest_sha256'], 'closed_at': time.time(), 'missing': missing, 'receipts': receipts})
    return {'closed': benchmark, 'missing': len(missing)}


def score_closed(config, cfg, manifest, benchmark):
    verify_freeze(config, manifest)
    closure = read(cfg.study_root / 'closed' / (benchmark + '.json'))
    if closure['manifest_sha256'] != manifest['manifest_sha256']:
        raise Blocked('generation closure manifest mismatch')
    for p, sha in closure['receipts'].items():
        if runtime.file_hash(scoring.contained(p, cfg.study_root)) != sha:
            raise Blocked('closed generation receipt changed')
    final = []
    for sample in ((1, 2) if benchmark == 'swebench' else (1,)):
        selected = [i for i in manifest['items'] if i['benchmark'] == benchmark and i['sample'] == sample]
        for arm in items.ARMS:
            responses, retained = [], []
            for item in selected:
                _, outcome = history(cfg, item, arm)
                if outcome is None:
                    continue
                p, s = outcome['path'], outcome['summary']
                if benchmark == 'swebench':
                    responses.append({'item': item['item_id'], 'patch': str(p / 'patch.diff')})
                else:
                    response = s.get('final_text')
                    if response is None:
                        response = s.get('texts', [''])[-1] if s.get('texts') else ''
                    record = {'item': item['item_id'], 'response': response, 'all_texts': s.get('texts', [])}
                    if benchmark == 'design2code':
                        record['input_image_read'] = scoring.verify_image_reads(item, s, read(p / 'command.json')['cwd'])
                    responses.append(record)
                retained.append(item)
            if not responses:
                continue
            batch = cfg.study_root / 'scores' / benchmark / arm / str(sample)
            identity = {'closure_sha256': runtime.digest(closure), 'responses_sha256': runtime.digest(responses),
                        'scoring_sha256': runtime.digest(config['scoring']), 'freeze': runtime.digest(config['freeze']),
                        'items': [i['input_sha256'] for i in retained]}
            batch.mkdir(parents=True, exist_ok=True)
            if (batch / 'binding.json').exists():
                if read(batch / 'binding.json') != identity:
                    raise Blocked('scoring batch changed after first attempt')
            else:
                write_once(batch / 'binding.json', identity)
            done = batch / 'complete.json'
            if done.exists():
                previous = read(done)
                if previous['binding'] != identity:
                    raise Blocked('completed scorer binding mismatch')
                for name, sha in previous['receipts'].items():
                    if runtime.file_hash(scoring.contained(name, batch)) != sha:
                        raise Blocked('completed scorer receipt changed')
                scored = previous['rows']
            else:
                attempts = list(batch.glob('attempt-*'))
                if len(attempts) >= 3:
                    raise Blocked('scoring infrastructure retry allowance exhausted')
                destination = batch / ('attempt-' + str(len(attempts) + 1))
                if benchmark == 'swebench':
                    raw = swe_adapter.score_patches(config['scoring'], responses, destination, f'fold-{arm}-{sample}')
                    scored = [scoring.normalize_score(benchmark, r) for r in raw]
                else:
                    scored = scoring.score_responses(config['scoring'], benchmark, responses, destination, retained)
                if any(r['status'] != 'complete' for r in scored):
                    raise Blocked('scoring returned pending observations; receipts retained, no zeros imputed')
                receipts = {str(p): runtime.file_hash(p) for p in destination.rglob('*') if p.is_file()}
                write_once(done, {'binding': identity, 'rows': scored, 'receipts': receipts})
            for row in scored:
                record = {**row, 'benchmark': benchmark, 'arm': arm, 'sample': sample, 'item_id': row['item']}
                if benchmark == 'swebench':
                    record['repo'] = next(i['scorer_data']['row']['repo'] for i in selected if i['item_id'] == row['item'])
                final.append(record)
    final_path = cfg.study_root / 'scores' / (benchmark + '.json')
    if final_path.exists():
        if read(final_path) != final:
            raise Blocked('completed benchmark scores changed')
    else:
        write_once(final_path, final)
    return {'scored': benchmark, 'rows': len(final), 'pending': sum(r['status'] != 'complete' for r in final)}


def analyze_scored(config, cfg, manifest):
    verify_freeze(config, manifest)
    rows = []
    for benchmark in items.SKILLS:
        path = cfg.study_root / 'scores' / (benchmark + '.json')
        if path.is_file():
            rows.extend(read(path))
    report = analysis.analyze(rows, manifest)
    # All charged attempts count toward descriptive execution cost, including infra failures.
    efficiency = []
    for benchmark in items.SKILLS:
        selected = [i for i in manifest['items'] if i['benchmark'] == benchmark]
        for arm in items.ARMS:
            attempts = [a for i in selected for a in history(cfg, i, arm)[0]]
            dollars, seconds = [], []
            for attempt in attempts:
                s = attempt['summary']
                value = (s.get('result') or {}).get('total_cost_usd')
                if isinstance(value, (int, float)):
                    dollars.append(value)
                if isinstance(s.get('elapsed_s'), (int, float)):
                    seconds.append(s['elapsed_s'])
            efficiency.append({'benchmark': benchmark, 'arm': arm, 'attempts': len(attempts),
                               'reported_api_equivalent_usd': sum(dollars) if dollars else None,
                               'cost_observations': len(dollars), 'elapsed_s': sum(seconds) if seconds else None,
                               'elapsed_observations': len(seconds)})
    report['execution_descriptives'] = efficiency
    report['execution_cost_note'] = 'CLI-reported API-equivalent cost, not a subscription bill; missing values remain unknown.'
    output = cfg.study_root / ('analysis-' + str(time.time_ns()) + '.json')
    write_once(output, report)
    return {'analysis': str(output), 'complete': report['complete'], 'contrasts': len(report['comparisons'])}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--config', required=True)
    ap.add_argument('command', choices=['preflight', 'status', 'probe', 'canary', 'canary-swe', 'run', 'close', 'score', 'analyze'])
    ap.add_argument('--benchmark', choices=list(items.SKILLS))
    ap.add_argument('--max-blocks', type=int, default=1)
    args = ap.parse_args()
    config, cfg, manifest = load(args.config)
    if args.command == 'preflight':
        result = readiness(config, manifest, [args.benchmark] if args.benchmark else items.SKILLS)
    elif args.command == 'status':
        result = status(cfg, manifest)
    else:
        verify_freeze(config, manifest)
        runtime.initialize_study(cfg, manifest)
        if args.command == 'probe':
            result = runtime.run_probe(cfg, manifest)
            result = {'status': result['summary']['status'], 'meter': result['summary']['meter']}
        elif args.command == 'canary':
            result = canary(config, cfg, manifest)
        elif args.command == 'canary-swe':
            result = swe_canary.run_canary(config, cfg, manifest)
        elif args.command == 'analyze':
            result = analyze_scored(config, cfg, manifest)
        else:
            if not args.benchmark:
                raise Blocked('--benchmark is required')
            if args.command == 'run':
                result = run_batch(config, cfg, manifest, args.benchmark, args.max_blocks)
            elif args.command == 'close':
                with controller_lock(cfg.study_root):
                    result = close_generation(config, cfg, manifest, args.benchmark)
            else:
                with controller_lock(cfg.study_root):
                    result = score_closed(config, cfg, manifest, args.benchmark)
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == '__main__':
    try:
        main()
    except (Blocked, runtime.RuntimeBlocked, scoring.ScoringBlocked, OSError, ValueError, KeyError) as exc:
        raise SystemExit('Blocked: ' + str(exc))
