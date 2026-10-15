import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch, Mock

import scoring
import swe_adapter as swe


class SWEAdapterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.data = self.root / 'data'
        self.data.mkdir()
        self.config = {'study_root': str(self.root), 'data_root': str(self.data), 'scorer_python': '/configured/python',
                       'docker_binary': '/configured/docker', 'scorer_sha256': {}}

    def test_failed_kill_cannot_be_mistaken_for_stopped_container(self):
        module = Mock()
        with patch('swe_adapter._run', return_value=subprocess.CompletedProcess([], 0, 'true\n', '')):
            with self.assertRaises(scoring.ScoringBlocked):
                swe._stop_container(module, self.config, 'task-container')
        with patch('swe_adapter._run', return_value=subprocess.CompletedProcess([], 1, '', 'daemon unavailable')):
            with self.assertRaises(scoring.ScoringBlocked):
                swe._stop_container(module, self.config, 'task-container')
        with patch('swe_adapter._run', return_value=subprocess.CompletedProcess([], 1, '', 'error: no such object: task-container')):
            self.assertEqual(swe._stop_container(module, self.config, 'task-container')['state'], 'removed')

    def test_command_uses_only_explicit_paths(self):
        out = self.root / 'oracle'
        plan = swe.oracle_command(self.config, out / 'predictions.jsonl', out, 'new-study-arm', ['repo__task-1'])
        self.assertEqual(plan['cwd'], str(out))
        self.assertIn(str(self.data / 'swebench-mini-rows-pinned.json'), plan['args'])
        self.assertIn(str(out / 'predictions.jsonl'), plan['args'])
        self.assertNotIn('bypassPermissions', str(plan))
        with self.assertRaises(scoring.ScoringBlocked):
            swe.oracle_command(self.config, self.root.parent / 'legacy.jsonl', out, 'new-study', ['x'])
        with self.assertRaises(scoring.ScoringBlocked):
            swe.oracle_command(self.config, out / 'p', out, '../old', ['x'])

    def test_missing_oracle_report_is_pending_empty_patch_is_failure(self):
        patch_file = self.root / 'patch.diff'
        patch_file.write_text('diff --git a/x b/x\n')
        empty = self.root / 'empty.diff'
        empty.write_text('')
        with patch('swe_adapter._run', return_value=subprocess.CompletedProcess([], 1, '', 'daemon unavailable')):
            result = swe.score_patches(self.config, [{'item': 'x', 'patch': str(patch_file)}, {'item': 'y', 'patch': str(empty)}], self.root / 'out', 'run-1')
        self.assertIsNone(result[0]['passed'])
        self.assertTrue(result[0]['harness_error'])
        self.assertEqual(result[1]['passed'], 0)
        self.assertTrue(result[1]['empty_patch'])

    def test_official_infrastructure_report_is_pending(self):
        patch_file = self.root / 'patch.diff'
        patch_file.write_text('diff --git a/x b/x\n')
        out = self.root / 'oracle'
        def run(*args, **kwargs):
            report = out / 'logs/run_evaluation/run-1/run-1/x/report.json'
            report.parent.mkdir(parents=True)
            report.write_text(json.dumps({'x': {'resolved': False, 'infra_failure': True}}))
            return subprocess.CompletedProcess([], 0, '', '')
        with patch('swe_adapter._run', side_effect=run):
            r = swe.score_patches(self.config, [{'item': 'x', 'patch': str(patch_file)}], out, 'run-1')[0]
        self.assertIsNone(r['passed'])
        self.assertTrue(r['harness_error'])
        self.assertTrue(r['raw']['infra_failure'])

    def test_readiness_refuses_prose_profile_even_with_deps(self):
        source = self.data / 'harness/swe_prepare.py'
        source.parent.mkdir()
        source.write_text('# frozen fixture')
        self.config['scorer_sha256']['harness/swe_prepare.py'] = hashlib.sha256(source.read_bytes()).hexdigest()
        image = 'example@sha256:' + 'a' * 64
        (self.data / 'swebench-mini-rows-pinned.json').write_text(json.dumps([{'instance_id': 'x', 'image': image}]))
        (self.data / 'swebench-image-digests.json').write_text(json.dumps({'x': image}))
        (self.data / 'swebench-validity.json').write_text(json.dumps({'x': {'valid': True}}))
        with patch('swe_adapter._run', return_value=subprocess.CompletedProcess([], 0, '', '')):
            result = swe.swe_readiness(self.config)
        self.assertFalse(result['ready'])
        self.assertIn('prose mode is invalid', ' '.join(result['issues']))

    def test_prepare_redirects_temp_and_docker_without_global_mutation(self):
        source = self.data / 'harness/swe_prepare.py'
        source.parent.mkdir()
        source.write_text('import tempfile, subprocess\nDOCKER="old"\n')
        self.config['scorer_sha256']['harness/swe_prepare.py'] = hashlib.sha256(source.read_bytes()).hexdigest()
        attempt = self.root / 'attempt'
        attempt.mkdir()
        original = tempfile.mkdtemp
        module = swe._prepare_module(self.config, attempt)
        self.assertIs(tempfile.mkdtemp, original)
        self.assertEqual(module.DOCKER, '/configured/docker')
        self.assertEqual(Path(module.tempfile.mkdtemp(dir='/old-study')).parent, attempt)
        with patch('swe_adapter.subprocess.run') as run:
            module.subprocess.run(['/configured/docker', 'run', 'image'])
        self.assertIn('--pull=never', run.call_args.args[0])


if __name__ == '__main__':
    unittest.main()
