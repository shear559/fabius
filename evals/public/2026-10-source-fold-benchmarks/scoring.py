#!/usr/bin/env python3
"""Isolated adapters for frozen scorers. No provider calls or dependency installation.

Config: study_root, data_root (real copied inputs/scorers), scorer_python,
optional cyberseceval_python, docker_binary, nltk_data and ssl_cert_file.
scorer_sha256 binds every copied transitive source; scorer_image_ids binds mutable
Docker tags to immutable IDs. No missing identity is adopted during readiness.
score_responses is called AFTER a benchmark's generation schedule is complete.
Raw secondary metrics are retained; missing/pending scores never become zeros.
"""
from __future__ import annotations

import ast
import hashlib
import json
import math
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import sys

SKILLS = {'finqa', 'labbench', 'smartbugs', 'bfcl', 'ds1000', 'cyberseceval', 'longmemeval', 'design2code'}
BENCHMARKS = SKILLS | {'ifeval', 'humaneval', 'swebench'}
IMAGES = {
    'bfcl': 'python@sha256:0dd364ba7e10242f07755449e3a3d0e35f9efd987952737b90def6709ab0c5ce',
    'design2code': 'fabius-design2code-scorer:1.0',
    'humaneval': 'fabius-evalplus:0.3.1',
}


class ScoringBlocked(RuntimeError):
    pass


def contained(path, root):
    path, root = Path(path).resolve(), Path(root).resolve()
    if path != root and root not in path.parents:
        raise ScoringBlocked('path escapes configured isolated root')
    return path


def data_path(config, relative):
    root = Path(config['data_root'])
    p = contained(root / relative, root)
    # Copies must be actual files, including intermediate directories.
    raw = root / relative
    if any(x.is_symlink() for x in [raw, *raw.parents] if x == root or root in x.parents):
        raise ScoringBlocked('data/scorer paths must be real copies, not symlinks')
    return p


def frozen_path(config, relative):
    p = data_path(config, relative)
    expected = config.get('scorer_sha256', {}).get(relative)
    if not expected:
        raise ScoringBlocked('missing frozen scorer hash: ' + relative)
    if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != expected:
        raise ScoringBlocked('frozen scorer hash mismatch: ' + relative)
    return p


def verify_frozen_sources(config):
    """Recheck every configured transitive source pin, not only a scorer entry point."""
    pins = config.get('scorer_sha256', {})
    if not pins:
        raise ScoringBlocked('no frozen scorer/source hashes configured')
    for relative, expected in pins.items():
        path = data_path(config, relative)
        h = hashlib.sha256()
        with path.open('rb') as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b''):
                h.update(chunk)
        if h.hexdigest() != expected:
            raise ScoringBlocked('frozen transitive source hash mismatch: ' + relative)


def _env(config):
    env = {k: v for k, v in os.environ.items() if not any(x in k.upper() for x in ('KEY', 'TOKEN', 'SECRET', 'PASSWORD'))}
    env.update(PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1')
    if config.get('ssl_cert_file'):
        env['SSL_CERT_FILE'] = str(config['ssl_cert_file'])
    if config.get('nltk_data'):
        env['NLTK_DATA'] = str(config['nltk_data'])
    return env


def _run(args, config, **kwargs):
    return subprocess.run([str(x) for x in args], capture_output=True, text=True,
                          env=_env(config), timeout=kwargs.pop('timeout', 60), **kwargs)


def _python(config, bench):
    return config.get('cyberseceval_python') if bench == 'cyberseceval' else config.get('scorer_python')


def score_readiness(config, benchmark, items=None):
    """Read-only dependency checks; offline render probe for Design2Code. Never installs."""
    issues, facts = [], {}
    try:
        verify_frozen_sources(config)
        if benchmark not in BENCHMARKS:
            raise ScoringBlocked('unknown benchmark')
        if benchmark == 'swebench':
            from swe_adapter import swe_readiness
            return swe_readiness(config, items)
        py = _python(config, benchmark)
        if not py or not Path(py).is_file():
            raise ScoringBlocked('missing configured scorer interpreter for ' + benchmark)
        if benchmark in SKILLS:
            script = frozen_path(config, f'skills-bench/{benchmark}/score.py')
            if not data_path(config, f'skills-bench/{benchmark}/items.jsonl').is_file():
                raise ScoringBlocked('missing frozen items.jsonl')
            facts['scorer_sha256'] = hashlib.sha256(script.read_bytes()).hexdigest()
            code = "import sys,pathlib;compile(pathlib.Path(sys.argv[1]).read_text(),sys.argv[1],'exec')"
            p = _run([py, '-B', '-c', code, script], config)
            if p.returncode:
                issues.append('frozen scorer is not compatible with configured interpreter')
            if benchmark in ('labbench', 'longmemeval'):
                code = "import sys;sys.path.insert(0,sys.argv[1]);" + (
                    "import official;official.parse_answer('[ANSWER]B[/ANSWER]',3)" if benchmark == 'labbench'
                    else "import official_loader;official_loader.verify();official_loader.get_anscheck_prompt()")
                p = _run([py, '-B', '-c', code, script.parent], config)
                if p.returncode:
                    issues.append('frozen official parser/prompt dependencies unavailable')
        if benchmark == 'ifeval':
            frozen_path(config, 'ifeval/instruction_following_eval/evaluation_lib.py')
            code = "import sys;sys.path.insert(0,sys.argv[1]);import langdetect,nltk;from instruction_following_eval import evaluation_lib;langdetect.DetectorFactory.seed=0;nltk.data.load('nltk:tokenizers/punkt/english.pickle');nltk.word_tokenize('dependency probe')"
            p = _run([py, '-B', '-c', code, data_path(config, 'ifeval')], config)
            if p.returncode:
                issues.append('official IFEval import/dependency check failed: ' + p.stderr[-600:])
        if benchmark == 'cyberseceval':
            p = _run([py, '-B', '-c', "from importlib.metadata import version;assert version('semgrep')=='1.51.0'"], config)
            if p.returncode:
                issues.append('frozen semgrep 1.51.0 environment unavailable')
            vendor = data_path(config, 'skills-bench/cyberseceval/vendor/PurpleLlama')
            code = "import sys,importlib.util,pathlib;d=pathlib.Path(list(importlib.util.find_spec('semgrep.bin').submodule_search_locations)[0]);assert (d/'osemgrep').is_symlink(),'missing pre-existing osemgrep alias; read-only dependency setup required';sys.path.insert(0,sys.argv[1]);from CodeShield.insecure_code_detector import insecure_code_detector;from CybersecurityBenchmarks.benchmark.bleu import compute_bleu_score"
            p = _run([py, '-B', '-c', code, vendor], config)
            if p.returncode:
                issues.append('frozen CyberSecEval detector dependencies unavailable')
            if p.returncode == 0:
                code = """import sys,tempfile,subprocess,json,pathlib
sys.path.insert(0,sys.argv[1])
from CodeShield.insecure_code_detector import oss
with tempfile.TemporaryDirectory(prefix='scorer-probe-') as directory:
 p=pathlib.Path(directory)/'probe.py';p.write_text('print(1)\\n')
 r=subprocess.run(oss.SEMGREP_COMMAND+[str(oss.SEMGREP_RULE_REPO_PATH/'python'),'--project-root','/',str(p)],capture_output=True,text=True)
 assert r.returncode==0,(r.stdout+r.stderr)[-800:]
 report=json.loads(r.stdout[r.stdout.find('{'):]);assert str(p.resolve()) in {str(pathlib.Path(v).resolve()) for v in report['paths']['scanned']}
"""
                p = _run([py, '-B', '-c', code, vendor], config)
                if p.returncode:
                    issues.append('frozen semgrep execution/target-scan probe failed: ' + p.stderr[-900:])
            pin = json.loads(data_path(config, 'skills-bench/cyberseceval/source.json').read_text())
            for rel, expected in pin['scorer']['rule_files_sha256'].items():
                if hashlib.sha256(contained(vendor / rel, vendor).read_bytes()).hexdigest() != expected:
                    issues.append('CyberSecEval rule hash mismatch: ' + rel)
        image = IMAGES.get(benchmark)
        if benchmark == 'ds1000':
            directory = data_path(config, 'skills-bench/ds1000/docker')
            h = hashlib.sha256()
            for name in ('Dockerfile', 'execution.py', 'fetch_data.py', 'requirements.lock.txt', 'run_one.py'):
                h.update(name.encode() + b'\0' + (directory / name).read_bytes() + b'\0')
            image = 'fabius-ds1000:' + h.hexdigest()[:12]
        if image:
            docker = config.get('docker_binary', 'docker')
            p = _run([docker, 'image', 'inspect', image], config)
            if p.returncode:
                issues.append('required local Docker image unavailable: ' + image)
            else:
                facts['image'] = image
                facts['image_id'] = json.loads(p.stdout)[0]['Id']
                if benchmark in ('humaneval', 'design2code', 'ds1000'):
                    expected = config.get('scorer_image_ids', {}).get(benchmark)
                    if not expected:
                        issues.append('missing frozen Docker image ID: ' + benchmark)
                    elif expected != facts['image_id']:
                        issues.append('frozen Docker image ID mismatch: ' + benchmark)
                if benchmark == 'design2code' and not issues:
                    # Checks the actual browser and cached CLIP weights offline, not just the tag.
                    code = "import clip;clip.load('ViT-B/32',device='cpu');from playwright.sync_api import sync_playwright\nwith sync_playwright() as p:\n b=p.chromium.launch();s=b.new_page();s.set_content('<p>render probe</p>');assert len(s.screenshot())>100;b.close()"
                    p = _run([docker, 'run', '--rm', '--pull=never', '--network', 'none', facts['image_id'], 'python', '-c', code], config, timeout=120)
                    if p.returncode:
                        issues.append('Design2Code offline Chromium/CLIP render probe failed')
                    else:
                        facts['offline_render_verified'] = True
        if benchmark == 'humaneval':
            for name in ('HumanEvalPlus-v0.1.10.jsonl',):
                if not data_path(config, 'humanevalplus/cache/' + name).is_file():
                    issues.append('missing frozen EvalPlus cache: ' + name)
        if benchmark == 'design2code':
            if not items:
                issues.append('Design2Code item images have not been verified')
            else:
                for item in items:
                    assets = item.get('assets', [])
                    if not assets:
                        issues.append('Design2Code item missing image asset')
                    for asset in assets:
                        p = contained(asset['source'], config['data_root'])
                        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != asset['sha256']:
                            issues.append('Design2Code screenshot missing or changed')
                facts['image_read_required'] = True
        if benchmark == 'longmemeval':
            facts['judge_status'] = 'awaiting separately authorized frozen judge; no model substitution'
    except (OSError, ValueError, KeyError, subprocess.SubprocessError, ScoringBlocked) as exc:
        issues.append(str(exc))
    return {'ready': not issues, 'issues': issues, 'facts': facts}


def normalize_score(benchmark, row):
    """A successful process is not proof of an available score."""
    result = {'item': str(row['item']), 'status': 'complete', 'metric_kind': 'continuous' if benchmark == 'design2code' else 'binary',
              'score': None, 'passed': None, 'raw': row}
    if row.get('status') == 'awaiting_judge':
        result['status'] = 'pending_judge'
        return result
    if row.get('sandbox_error') or row.get('icd_error') or row.get('harness_error'):
        result['status'] = 'pending_infrastructure'
        return result
    passed = row.get('passed')
    if passed is not None and not (type(passed) in (bool, int) and passed in (0, 1)):
        raise ScoringBlocked('non-binary passed value')
    if benchmark == 'design2code':
        value = row.get('score')
        if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1:
            result['status'] = 'pending_score'
        else:
            # Frozen pipeline defines rendering failures as zero; retain scorer_ok/error.
            result.update(score=float(value), passed=passed)
    elif passed is None:
        result['status'] = 'pending_score'
    else:
        result.update(score=int(passed), passed=int(passed))
    return result


def score_responses(config, benchmark, responses, output_dir, items=None):
    """One batch with unique item IDs; caller groups arms/samples independently."""
    ready = score_readiness(config, benchmark, items)
    if not ready['ready']:
        raise ScoringBlocked('; '.join(ready['issues']))
    if benchmark == 'swebench':
        raise ScoringBlocked('SWE requires repository patches and swe_adapter.score_patches')
    ids = [str(r['item']) for r in responses]
    if len(ids) != len(set(ids)):
        raise ScoringBlocked('duplicate item in one scoring batch')
    if any(not isinstance(r.get('response'), str) for r in responses):
        raise ScoringBlocked('missing response is infrastructure, not an empty model answer')
    if benchmark == 'design2code' and any(r.get('input_image_read') is not True for r in responses):
        raise ScoringBlocked('Design2Code requires successful image Read evidence for every generation')
    out = contained(output_dir, config['study_root'])
    data = Path(config['data_root']).resolve()
    if out == data or data in out.parents:
        raise ScoringBlocked('scoring output must be outside frozen data')
    out.mkdir(parents=True, exist_ok=False)
    rp, sp = out / 'responses.jsonl', out / 'scored.raw.jsonl'
    rp.write_text(''.join(json.dumps(r) + '\n' for r in responses))
    job = {'config': config, 'benchmark': benchmark, 'responses': str(rp), 'output': str(sp)}
    job_path = out / 'score-job.json'
    job_path.write_text(json.dumps(job))
    proc = _run([_python(config, benchmark), '-B', Path(__file__).resolve(), '--worker', job_path], config,
                cwd=out, timeout=config.get('score_timeout_s', 14400))
    (out / 'stdout.txt').write_text(proc.stdout)
    (out / 'stderr.txt').write_text(proc.stderr)
    if proc.returncode:
        raise ScoringBlocked('frozen scorer failed; inspect retained scoring stderr')
    rows = [json.loads(line) for line in sp.read_text().splitlines() if line.strip()]
    if sorted(str(r['item']) for r in rows) != sorted(ids):
        raise ScoringBlocked('scorer item set mismatch')
    normalized = [normalize_score(benchmark, row) for row in rows]
    (out / 'scores.jsonl').write_text(''.join(json.dumps(r, allow_nan=False) + '\n' for r in normalized))
    return normalized


def verify_image_reads(item, summary, cwd):
    """Validate controller-recorded successful image tool delivery, never a prose claim."""
    cwd = Path(cwd).resolve()
    required = {(cwd / a['path']).resolve() for a in item.get('assets', [])}
    delivered = set()
    for read in summary.get('reads', []):
        request = read.get('request', {})
        value = request.get('file_path') or request.get('path')
        if not isinstance(value, str):
            continue
        path = Path(value)
        path = (cwd / path).resolve() if not path.is_absolute() else path.resolve()
        if (read.get('returned') and read.get('delivered') and not read.get('is_error')
                and any(b.get('type') == 'image' for b in read.get('non_text_blocks', []))):
            delivered.add(path)
    return bool(required) and required <= delivered


def score_attempt(config, benchmark, item, attempt_dir):
    """Convenience adapter; orchestration still defers it until generation completes."""
    attempt = contained(attempt_dir, config['study_root'])
    summary = json.loads((attempt / 'summary.json').read_text())
    if summary.get('status') != 'complete':
        raise ScoringBlocked('attempt is not a complete generation; do not score infrastructure as an outcome')
    command = json.loads((attempt / 'command.json').read_text()) if (attempt / 'command.json').is_file() else {}
    return score_responses(config, benchmark, [{'item': item['item_id'], 'response': summary.get('final_text'),
                          'all_texts': summary.get('all_texts', summary.get('texts', [])),
                          'input_image_read': verify_image_reads(item, summary, command.get('cwd', summary.get('cwd', attempt / 'workspace')))}], attempt / 'scoring', [item])[0]


def _ifeval(job):
    config = job['config']
    sys.path.insert(0, str(data_path(config, 'ifeval')))
    import langdetect
    from instruction_following_eval import evaluation_lib as lib
    langdetect.DetectorFactory.seed = 0
    ip = data_path(config, 'ifeval/instruction_following_eval/data/input_data.jsonl')
    prompts = {str(r['key']): r['prompt'] for r in map(json.loads, ip.read_text().splitlines())}
    inputs = {r.prompt: r for r in lib.read_prompt_list(str(ip))}
    rows = []
    for r in map(json.loads, Path(job['responses']).read_text().splitlines()):
        prompt = prompts[str(r['item'])]
        row = {'item': r['item']}
        for name, text in [('final', r['response']), ('concat', '\n\n'.join(r.get('all_texts') or []) or r['response'])]:
            for strict, fn in [(True, lib.test_instruction_following_strict), (False, lib.test_instruction_following_loose)]:
                result = fn(inputs[prompt], {prompt: text})
                key = ('passed' if strict else 'loose_passed') + ('_concat' if name == 'concat' else '')
                row[key] = int(result.follow_all_instructions)
                row[f'{name}_{"strict" if strict else "loose"}_instructions'] = list(result.follow_instruction_list)
        rows.append(row)
    Path(job['output']).write_text(''.join(json.dumps(r) + '\n' for r in rows))


def _evalplus_run(config, out, cache, name, repeat):
    command = (f'python -m evalplus.sanitize --samples {name}.jsonl && '
               f'python -m evalplus.evaluate --dataset humaneval --samples {name}-sanitized.jsonl --parallel 8 --i-just-wanna-run')
    ev = out / f'{name}-sanitized_eval_results.json'
    if ev.exists():
        ev.unlink()
    subprocess.run([config.get('docker_binary', 'docker'), 'run', '--rm', '--pull=never', '--network', 'none',
                    '-v', f'{out}:/work', '-w', '/work', '-v', f'{cache}:/root/.cache/evalplus',
                    config['scorer_image_ids']['humaneval'], 'bash', '-c', command], check=True)
    result = json.loads(ev.read_text())['eval']
    shutil.copyfile(ev, out / f'{name}-eval-{repeat}.json')
    return result


def _humaneval(job):
    config, out = job['config'], Path(job['output']).parent
    cache = out / 'evalplus-cache'
    shutil.copytree(data_path(config, 'humanevalplus/cache'), cache, symlinks=False)
    rows = {r['item']: r for r in map(json.loads, Path(job['responses']).read_text().splitlines())}
    dataset = [json.loads(l) for l in (cache / 'HumanEvalPlus-v0.1.10.jsonl').read_text().splitlines()]
    all_ids = [r['task_id'] for r in dataset]
    canonical = [{'task_id': r['task_id'], 'solution': r['prompt'] + r['canonical_solution']} for r in dataset]
    (out / 'canonical.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in canonical))
    control = _evalplus_run(config, out, cache, 'canonical', 1)
    failed = [tid for tid in all_ids if tid != 'HumanEval/32' and
              (tid not in control or not control[tid] or any(control[tid][0].get(k) != 'pass' for k in ('base_status', 'plus_status')))]
    (out / 'canonical-validity.json').write_text(json.dumps({'unexpected_failures': failed, 'registered_exclusion': 'HumanEval/32'}))
    if failed:
        raise ScoringBlocked('same-session EvalPlus canonical validity failed; participant outcomes remain pending')
    samples = [{'task_id': tid, 'solution': rows.get(tid.replace('/', '_'), {}).get('response', '') if tid != 'HumanEval/32' else ''} for tid in all_ids]
    (out / 'samples.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in samples))
    results = [_evalplus_run(config, out, cache, 'samples', repeat) for repeat in (1, 2)]
    scored = []
    for iid in rows:
        tid = iid.replace('_', '/')
        a, b = results[0][tid][0], results[1][tid][0]
        scored.append({'item': iid, 'passed': None if tid == 'HumanEval/32' else int(a['plus_status'] == 'pass'),
                       'base_passed': int(a['base_status'] == 'pass'), 'excluded': 'frozen canonical-solution failure' if tid == 'HumanEval/32' else '',
                       'flip': (a['base_status'], a['plus_status']) != (b['base_status'], b['plus_status'])})
    Path(job['output']).write_text(''.join(json.dumps(r) + '\n' for r in scored))


def _worker(job):
    config, benchmark = job['config'], job['benchmark']
    verify_frozen_sources(config)
    sys.dont_write_bytecode = True
    # Frozen scorers may auto-build. Preserve their metrics but prohibit implicit setup.
    original_run = subprocess.run
    def run(args, *pos, **kw):
        if isinstance(args, (list, tuple)) and args and Path(str(args[0])).name == 'docker':
            args = list(args)
            args[0] = config.get('docker_binary', 'docker')
            if any(x in args[1:3] for x in ('build', 'pull')):
                raise ScoringBlocked('automatic Docker installation is prohibited')
            if len(args) > 1 and args[1] == 'run' and '--pull=never' not in args:
                args.insert(2, '--pull=never')
            expected = config.get('scorer_image_ids', {}).get(benchmark)
            if benchmark in ('humaneval', 'design2code', 'ds1000'):
                if not expected:
                    raise ScoringBlocked('missing frozen Docker image ID')
                args = [expected if value == IMAGES.get(benchmark) or
                        (benchmark == 'ds1000' and str(value).startswith('fabius-ds1000:')) else value for value in args]
        return original_run(args, *pos, **kw)
    subprocess.run = run
    if benchmark == 'ifeval':
        return _ifeval(job)
    if benchmark == 'humaneval':
        return _humaneval(job)
    script = frozen_path(config, f'skills-bench/{benchmark}/score.py')
    sys.path.insert(0, str(script.parent))
    sys.argv = [str(script), job['responses'], job['output']]
    if benchmark == 'design2code':
        sys.argv += ['--jobs', '1', '--work-dir', str(Path(job['output']).parent / 'render')]
    if benchmark == 'cyberseceval':
        # Import under a non-main name to avoid the frozen wrapper's hardcoded venv exec.
        # Retarget only the frozen script's temporary-directory assignment. The detector,
        # extraction and scoring functions remain the original AST; data_root stays read-only.
        tree = ast.parse(script.read_text(), filename=str(script))
        bindings = [n for n in tree.body if isinstance(n, ast.Assign) and
                    any(isinstance(t, ast.Name) and t.id == 'TMP' for t in n.targets)]
        if len(bindings) != 1:
            raise ScoringBlocked('frozen CyberSecEval temporary-path binding changed')
        bindings[0].value = ast.Call(func=ast.Name(id='Path', ctx=ast.Load()),
                                     args=[ast.Constant(str(Path(job['output']).parent / 'icd-temp'))], keywords=[])
        namespace = {'__file__': str(script), '__name__': 'frozen_cyberseceval'}
        exec(compile(ast.fix_missing_locations(tree), str(script), 'exec'), namespace)
        raise SystemExit(namespace['main'](sys.argv))
    runpy.run_path(str(script), run_name='__main__')


if __name__ == '__main__':
    if len(sys.argv) != 3 or sys.argv[1] != '--worker':
        raise SystemExit('import score_readiness/score_responses; internal worker requires a job file')
    _worker(json.loads(Path(sys.argv[2]).read_text()))
