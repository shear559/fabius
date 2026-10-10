import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import scoring


class ScoringTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.data = self.root / 'data'
        self.data.mkdir()
        self.config = {'study_root': str(self.root), 'data_root': str(self.data), 'scorer_python': sys.executable,
                       'scorer_sha256': {}}

    def script(self, benchmark, text):
        relative = f'skills-bench/{benchmark}/score.py'
        p = self.data / relative
        p.parent.mkdir(parents=True)
        p.write_text(text)
        (p.parent / 'items.jsonl').write_text('{}\n')
        self.config['scorer_sha256'][relative] = hashlib.sha256(p.read_bytes()).hexdigest()
        return p

    def test_pending_judge_cannot_be_booleanized(self):
        r = scoring.normalize_score('longmemeval', {'item': 'a', 'passed': None, 'status': 'awaiting_judge'})
        self.assertEqual(r['status'], 'pending_judge')
        self.assertIsNone(r['score'])
        self.assertIsNone(r['passed'])

    def test_visual_primary_is_continuous(self):
        r = scoring.normalize_score('design2code', {'item': 'a', 'passed': 0, 'score': .805})
        self.assertEqual(r['score'], .805)
        self.assertEqual(r['passed'], 0)
        self.assertEqual(r['metric_kind'], 'continuous')

    def test_missing_and_infrastructure_never_score_zero(self):
        for row in ({'passed': None}, {'passed': 0, 'sandbox_error': True}, {'passed': 1, 'icd_error': 'crash'}):
            r = scoring.normalize_score('ds1000', {'item': 'a', **row})
            self.assertIsNone(r['score'])
            self.assertTrue(r['status'].startswith('pending'))

    def test_changed_transitive_helper_blocks_readiness(self):
        p = self.script('finqa', '# frozen')
        helper = p.parent / 'helper.py'
        helper.write_text('# original')
        self.config['scorer_sha256']['skills-bench/finqa/helper.py'] = hashlib.sha256(helper.read_bytes()).hexdigest()
        helper.write_text('# changed')
        result = scoring.score_readiness(self.config, 'finqa')
        self.assertFalse(result['ready'])
        self.assertIn('transitive', ' '.join(result['issues']))

    def test_no_string_truthiness(self):
        with self.assertRaises(scoring.ScoringBlocked):
            scoring.normalize_score('finqa', {'item': 'a', 'passed': 'false'})

    def test_real_frozen_style_worker_and_nested_ids(self):
        self.script('finqa', "import sys,json\nrows=[json.loads(x) for x in open(sys.argv[1])]\nwith open(sys.argv[2],'w') as f:\n for r in rows: f.write(json.dumps({'item':r['item'],'passed':int(r['response']=='Answer: 2')})+'\\n')\n")
        before = {p.relative_to(self.data): p.read_bytes() for p in self.data.rglob('*') if p.is_file()}
        rows = scoring.score_responses(self.config, 'finqa', [{'item': 'nested/path/7', 'response': 'Answer: 2'}], self.root / 'scores')
        self.assertEqual(rows[0]['item'], 'nested/path/7')
        self.assertEqual(rows[0]['score'], 1)
        self.assertEqual(before, {p.relative_to(self.data): p.read_bytes() for p in self.data.rglob('*') if p.is_file()})

    def test_mutated_script_and_symlink_fail_closed(self):
        p = self.script('finqa', '# scorer')
        p.write_text('# changed')
        self.assertFalse(scoring.score_readiness(self.config, 'finqa')['ready'])
        p.unlink()
        target = self.root / 'legacy.py'
        target.write_text('# scorer')
        p.symlink_to(target)
        with self.assertRaises(scoring.ScoringBlocked):
            scoring.data_path(self.config, 'skills-bench/finqa/score.py')

    def test_duplicate_missing_and_old_output_rejected(self):
        self.script('finqa', '# scorer')
        for responses in ([{'item': 'a', 'response': None}], [{'item': 'a', 'response': ''}] * 2):
            with self.assertRaises(scoring.ScoringBlocked):
                scoring.score_responses(self.config, 'finqa', responses, self.root / 'scores')
        with self.assertRaises(scoring.ScoringBlocked):
            scoring.score_responses(self.config, 'finqa', [], self.data / 'scores')
        with self.assertRaises(scoring.ScoringBlocked):
            scoring.contained(self.root.parent / 'outside', self.root)

    def test_design_readiness_requires_actual_images_and_render(self):
        self.script('design2code', '# scorer')
        good = subprocess.CompletedProcess([], 0, json.dumps([{'Id': 'sha256:fixture'}]), '')
        with patch('scoring._run', return_value=good):
            result = scoring.score_readiness(self.config, 'design2code')
            self.assertFalse(result['ready'])
            self.assertTrue(any('images' in x for x in result['issues']))
        with patch('scoring._run', return_value=subprocess.CompletedProcess([], 1, '', 'missing')):
            result = scoring.score_readiness(self.config, 'design2code', [])
            self.assertFalse(result['ready'])

    def test_image_evidence_requires_delivered_image_block(self):
        item = {'assets': [{'path': 'input/screenshot.png'}]}
        read = {'request': {'file_path': 'input/screenshot.png'}, 'returned': True,
                'delivered': True, 'is_error': False, 'non_text_blocks': [{'type': 'image'}]}
        self.assertTrue(scoring.verify_image_reads(item, {'reads': [read]}, self.root))
        for change in ({'is_error': True}, {'non_text_blocks': []}, {'returned': False},
                       {'request': {'file_path': 'unrelated.png'}}):
            self.assertFalse(scoring.verify_image_reads(item, {'reads': [{**read, **change}]}, self.root))

    def test_mutable_image_requires_frozen_identity(self):
        self.script('design2code', '# scorer')
        good = subprocess.CompletedProcess([], 0, json.dumps([{'Id': 'sha256:actual'}]), '')
        with patch('scoring._run', return_value=good):
            r = scoring.score_readiness(self.config, 'design2code', [])
            self.assertIn('missing frozen Docker image ID', ' '.join(r['issues']))
            self.config['scorer_image_ids'] = {'design2code': 'sha256:other'}
            r = scoring.score_readiness(self.config, 'design2code', [])
            self.assertIn('image ID mismatch', ' '.join(r['issues']))

    def test_canonical_failure_blocks_before_participant_evaluation(self):
        cache = self.data / 'humanevalplus/cache'
        cache.mkdir(parents=True)
        dataset = [{'task_id': i, 'prompt': 'def f():', 'canonical_solution': 'return 1'} for i in ('HumanEval/0', 'HumanEval/32')]
        (cache / 'HumanEvalPlus-v0.1.10.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in dataset))
        responses = self.root / 'responses.jsonl'
        responses.write_text(json.dumps({'item': 'HumanEval_0', 'response': 'def f(): return 1'})+'\n')
        out = self.root / 'scores'
        out.mkdir()
        job = {'config': self.config, 'responses': str(responses), 'output': str(out / 'raw.jsonl')}
        control = {'HumanEval/0': [{'base_status': 'fail', 'plus_status': 'fail'}]}
        with patch('scoring._evalplus_run', return_value=control) as run:
            with self.assertRaises(scoring.ScoringBlocked):
                scoring._humaneval(job)
            self.assertEqual(run.call_count, 1)
            self.assertEqual(run.call_args.args[3], 'canonical')
        self.assertFalse((out/'samples.jsonl').exists())

    def test_worker_executes_immutable_image_identity(self):
        self.script('design2code', "import subprocess\nsubprocess.run(['docker','run','fabius-design2code-scorer:1.0'],check=True)\n")
        docker = self.root / 'fixture-docker'
        docker.write_text("#!/bin/sh\nprintf '%s\\n' \"$@\"\n")
        docker.chmod(0o755)
        self.config.update(docker_binary=str(docker), scorer_image_ids={'design2code': 'sha256:frozen'})
        job = {'config': self.config, 'benchmark': 'design2code', 'responses': 'unused', 'output': str(self.root/'unused')}
        jp = self.root / 'job.json';jp.write_text(json.dumps(job))
        p = subprocess.run([sys.executable, '-B', scoring.__file__, '--worker', str(jp)], capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn('sha256:frozen', p.stdout)
        self.assertNotIn('fabius-design2code-scorer:1.0', p.stdout)
        self.assertIn('--pull=never', p.stdout)

    def test_worker_blocks_implicit_install(self):
        self.script('ds1000', "import subprocess\nsubprocess.run(['docker','build','x'],check=True)\n")
        job = {'config': self.config, 'benchmark': 'ds1000', 'responses': 'unused', 'output': 'unused'}
        jp = self.root / 'job.json'
        jp.write_text(json.dumps(job))
        p = subprocess.run([sys.executable, '-B', scoring.__file__, '--worker', str(jp)], capture_output=True, text=True)
        self.assertNotEqual(p.returncode, 0)
        self.assertIn('installation is prohibited', p.stderr)


if __name__ == '__main__':
    unittest.main()
