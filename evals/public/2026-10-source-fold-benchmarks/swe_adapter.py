#!/usr/bin/env python3
"""SWE repository workspace and official Docker oracle adapters, never prose scoring.

The runtime must explicitly implement this agent profile before SWE generation is ready.
Frozen swe_prepare logic is reused only from a hash-checked isolated copy, with Docker
and every temporary/output root redirected. No dependency installation or provider calls.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import re
import runpy
import subprocess
import sys
import tempfile
from types import SimpleNamespace

from scoring import ScoringBlocked, contained, data_path, frozen_path, verify_frozen_sources, _run


_SAFE = re.compile(r'^[A-Za-z0-9_.-]+$')


def _identifier(value):
    if not isinstance(value, str) or not _SAFE.fullmatch(value):
        raise ScoringBlocked('invalid oracle identifier')
    return value


def swe_readiness(config, items=None):
    issues, facts = [], {}
    try:
        verify_frozen_sources(config)
        frozen_path(config, 'harness/swe_prepare.py')
        py = config['scorer_python']
        p = _run([py, '-B', '-c', 'import swebench.harness.run_evaluation'], config)
        if p.returncode:
            issues.append('official swebench Python harness unavailable')
        rows = json.loads(data_path(config, 'swebench-mini-rows-pinned.json').read_text())
        pins = json.loads(data_path(config, 'swebench-image-digests.json').read_text())
        valid = json.loads(data_path(config, 'swebench-validity.json').read_text())
        selected = {r['item_id'] for r in items} if items is not None else {r['instance_id'] for r in rows if valid.get(r['instance_id'], {}).get('valid')}
        by_id = {r['instance_id']: r for r in rows}
        if not selected:
            issues.append('no selected valid SWE instances')
        for iid in sorted(selected):
            row = by_id[iid]
            image = pins[iid]
            if not valid.get(iid, {}).get('valid'):
                issues.append('instance lacks frozen validity: ' + iid)
            if row['image'] != image or '@sha256:' not in image:
                issues.append('SWE image digest mismatch: ' + iid)
                continue
            if row.get('image_assets'):
                issues.append('remote SWE image_assets require separately frozen local assets')
            p = _run([config.get('docker_binary', 'docker'), 'image', 'inspect', image], config)
            if p.returncode:
                issues.append('required pinned SWE image unavailable: ' + iid)
        facts['oracle'] = 'swebench.harness.run_evaluation; frozen pinned rows and Docker images'
        facts['runtime_profile_required'] = 'swe_repository'
        if config.get('swe_runtime_profile_verified') is not True:
            issues.append('SWE repository-editing profile still requires its live access canary; read-only/prose evidence is insufficient')
    except (OSError, KeyError, ValueError, subprocess.SubprocessError, ScoringBlocked) as exc:
        issues.append(str(exc))
    return {'ready': not issues, 'issues': issues, 'facts': facts}


def _prepare_module(config, attempt_dir):
    verify_frozen_sources(config)
    source = frozen_path(config, 'harness/swe_prepare.py')
    spec = importlib.util.spec_from_file_location('isolated_swe_prepare', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.DOCKER = config.get('docker_binary', 'docker')
    def command(args):
        args = list(args)
        if args[0] == module.DOCKER and len(args) > 1 and args[1] == 'run':
            args.insert(2, '--pull=never')
        return args
    module.subprocess = SimpleNamespace(
        run=lambda args, **kw: subprocess.run(command(args), **kw),
        Popen=lambda args, **kw: subprocess.Popen(command(args), **kw), PIPE=subprocess.PIPE)
    # Replace this module's tempfile reference, never mutate the process-global module.
    module.tempfile = SimpleNamespace(mkdtemp=lambda **kw: tempfile.mkdtemp(prefix='workspace-', dir=attempt_dir))
    return module


def _stop_container(module, config, container):
    container = _identifier(container)
    module.kill_container(container)
    result = _run([config.get('docker_binary', 'docker'), 'inspect', '--format', '{{.State.Running}}', container], config)
    gone = result.returncode != 0 and ('no such object' in result.stderr.lower() or 'no such container' in result.stderr.lower())
    stopped = result.returncode == 0 and result.stdout.strip() == 'false'
    if not (gone or stopped):
        raise ScoringBlocked('SWE container termination could not be confirmed; preserve workspace')
    return {'confirmed': True, 'state': 'removed' if gone else 'stopped'}


def prepare_repository(config, row, attempt_dir, snapshot_path=None, scratch_root=None):
    """Prepare a real base checkout and start an offline test container; no model call."""
    attempt = contained(attempt_dir, config['study_root'])
    attempt.mkdir(parents=True, exist_ok=True)
    scratch = contained(scratch_root, config.get('scratch_root', '/private/tmp')) if scratch_root is not None else attempt
    if scratch == Path(config.get('scratch_root', '/private/tmp')).resolve():
        raise ScoringBlocked('SWE scratch root must be a per-attempt child directory')
    scratch.mkdir(parents=True, exist_ok=True)
    if snapshot_path is not None:
        snapshot_path = contained(snapshot_path, scratch)
        if not snapshot_path.is_dir():
            raise ScoringBlocked('missing explicit plugin snapshot')
    if '@sha256:' not in row['image']:
        raise ScoringBlocked('SWE workspace requires a pinned image digest')
    p = _run([config.get('docker_binary', 'docker'), 'image', 'inspect', row['image']], config)
    if p.returncode:
        raise ScoringBlocked('pinned SWE image is not local; automatic pulls prohibited')
    module = _prepare_module(config, scratch)
    log = {'image': row['image']}
    root, repo, valid = module.prepare_workspace(row['image'], row['base_commit'], log)
    if not valid:
        (attempt / 'workspace.json').write_text(json.dumps(log, indent=2))
        raise ScoringBlocked('frozen SWE workspace assertions failed')
    container, command = module.start_container(row['image'], repo)
    try:
        wrapper = module.write_wrapper(root, container)
        # Frozen prompt and patch filter are kept; runtime must enforce this exact scoped tool profile.
        plan = {'profile': 'swe_repository', 'cwd': str(repo), 'workspace_root': str(root),
                'scratch_root': str(scratch), 'container': container, 'wrapper': str(wrapper), 'plugin_snapshot': str(snapshot_path) if snapshot_path else None,
                'prompt': module.render_prompt(row['problem_statement'], repo, wrapper),
                'tools': ['Read', 'Edit', 'Write', 'Glob', 'Grep', 'TodoWrite', 'Skill', 'Bash'],
                'allowed_tools': ['Read', 'Edit', 'Write', 'Glob', 'Grep', 'TodoWrite', 'Skill', f'Bash({wrapper}:*)'],
                'permission_mode': 'dontAsk', 'head': log['workspace_asserts']['head'], 'docker_run': command}
        (attempt / 'workspace.json').write_text(json.dumps({**log, **plan}, indent=2))
        return plan
    except BaseException:
        _stop_container(module, config, container)
        raise


def finish_repository(config, plan, attempt_dir):
    """Stop this task's container before capturing filtered and unfiltered real git diffs."""
    attempt = contained(attempt_dir, config['study_root'])
    scratch = contained(plan.get('scratch_root', attempt), config.get('scratch_root', '/private/tmp')) if plan.get('scratch_root') != str(attempt) else attempt
    repo = contained(plan['cwd'], scratch)
    module = _prepare_module(config, attempt)
    termination = _stop_container(module, config, plan['container'])
    (attempt / 'container-termination.json').write_text(json.dumps(termination))
    filtered, unfiltered = module.extract_patch(repo, plan['head'])
    (attempt / 'patch.diff').write_text(filtered)
    (attempt / 'patch.unfiltered.diff').write_text(unfiltered)
    return {'patch': str(attempt / 'patch.diff'), 'patch_unfiltered': str(attempt / 'patch.unfiltered.diff'),
            'patch_size': module.patch_size(filtered), 'unfiltered_patch_size': module.patch_size(unfiltered)}


def oracle_command(config, predictions_path, output_dir, run_id, item_ids, workers=1):
    output = contained(output_dir, config['study_root'])
    predictions = contained(predictions_path, output)
    _identifier(run_id)
    if workers not in (1, 2):
        raise ScoringBlocked('SWE oracle workers must be 1 or 2')
    args = [config['scorer_python'], '-B', '-m', 'swebench.harness.run_evaluation', '-d',
            str(data_path(config, 'swebench-mini-rows-pinned.json')), '-p', str(predictions),
            '-id', run_id, '--max_workers', str(workers), '-t', '1800', '-i', *[_identifier(i) for i in item_ids]]
    return {'args': args, 'cwd': str(output)}


def score_patches(config, patches, output_dir, run_id):
    """One arm/sample batch. Missing oracle report remains pending infrastructure."""
    out = contained(output_dir, config['study_root'])
    out.mkdir(parents=True, exist_ok=False)
    model = _identifier(run_id)
    predictions, empty = [], set()
    for row in patches:
        iid = _identifier(row['item'])
        patch = contained(row['patch'], config['study_root']).read_text()
        if not patch.strip():
            empty.add(iid)
        else:
            predictions.append({'instance_id': iid, 'model_name_or_path': model, 'model_patch': patch})
    pp = out / 'predictions.jsonl'
    pp.write_text(''.join(json.dumps(r) + '\n' for r in predictions))
    if predictions:
        plan = oracle_command(config, pp, out, run_id, [p['instance_id'] for p in predictions])
        job = out / 'oracle-job.json'
        job.write_text(json.dumps(plan))
        # Run the official CLI with Docker SDK pulls blocked, preserving all oracle semantics.
        p = _run([config['scorer_python'], '-B', Path(__file__).resolve(), '--oracle-worker', job], config,
                 cwd=out, timeout=config.get('score_timeout_s', 14400))
        (out / 'stdout.txt').write_text(p.stdout)
        (out / 'stderr.txt').write_text(p.stderr)
    results = []
    for row in patches:
        iid = row['item']
        report = out / 'logs/run_evaluation' / run_id / model / iid / 'report.json'
        if iid in empty:
            results.append({'item': iid, 'passed': 0, 'empty_patch': True, 'harness_error': False})
        elif report.is_file():
            value = json.loads(report.read_text()).get(iid)
            if not isinstance(value, dict) or type(value.get('resolved')) is not bool or value.get('infra_failure'):
                results.append({'item': iid, 'passed': None, 'harness_error': True, 'raw': value})
            else:
                results.append({'item': iid, 'passed': int(value['resolved']), 'harness_error': False, 'raw': value})
        else:
            results.append({'item': iid, 'passed': None, 'harness_error': True})
    (out / 'scores.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in results))
    return results


def _oracle_worker(plan):
    import docker.models.images
    def no_pull(*args, **kwargs):
        raise ScoringBlocked('SWE oracle image pull/build is prohibited; required image must already exist')
    docker.models.images.ImageCollection.pull = no_pull
    docker.models.images.ImageCollection.build = no_pull
    sys.argv = [plan['args'][3], *plan['args'][4:]]
    runpy.run_module('swebench.harness.run_evaluation', run_name='__main__')


if __name__ == '__main__':
    if len(sys.argv) != 3 or sys.argv[1] != '--oracle-worker':
        raise SystemExit('import the SWE helpers; provider execution requires a verified runtime profile')
    _oracle_worker(json.loads(Path(sys.argv[2]).read_text()))
