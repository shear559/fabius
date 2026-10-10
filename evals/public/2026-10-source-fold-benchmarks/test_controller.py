import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import controller as c
import runtime


class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.cfg = SimpleNamespace(study_root=self.root, budget_authorized=False)
        self.item = {'item_key': '["finqa","x",1]', 'item_id': 'x', 'sample': 1, 'benchmark': 'finqa'}
        self.binding = {'manifest_sha256': 'synthetic-manifest'}
        (self.root / 'runtime-binding.json').write_text(json.dumps(self.binding))

    def attempt(self, ordinal, status='invalid', **changes):
        p = self.root / 'attempts' / runtime.digest(self.item['item_key']) / 'baseline' / ('attempt-' + str(ordinal))
        p.mkdir(parents=True)
        task = {'id': self.item['item_key'], 'prompt': 'Synthetic task'}
        binding = {'study': self.binding, 'arm': 'baseline', 'task': task, 'task_sha256': runtime.digest(task)}
        summary = {'status': status, 'task_sha256': binding['task_sha256'],
                   'manifest_sha256': self.binding['manifest_sha256'], **changes}
        (p / 'reservation.json').write_text(json.dumps({'ordinal': ordinal}))
        (p / 'binding.json').write_text(json.dumps(binding))
        (p / 'command.json').write_text('{}')
        (p / 'stream.jsonl').write_text('')
        (p / 'stderr.txt').write_text('')
        (p / 'summary.json').write_text(json.dumps(summary))
        runtime.seal_attempt(p, summary)
        return p

    def test_restarts_keep_all_attempts_and_first_terminal_output(self):
        self.attempt(1)
        self.attempt(2, 'outcome_limit', outcome_ready=True)
        attempts, chosen = c.history(self.cfg, self.item, 'baseline')
        self.assertEqual(len(attempts), 2)
        self.assertEqual(chosen['ordinal'], 2)
        # A second terminal answer cannot quietly replace the first after scoring.
        self.attempt(3, 'complete')
        with self.assertRaisesRegex(c.Blocked, 'multiple terminal'):
            c.history(self.cfg, self.item, 'baseline')

    def test_crash_after_reservation_requires_reconciliation(self):
        p = self.attempt(1)
        (p / 'summary.json').unlink()
        with self.assertRaisesRegex(c.Blocked, 'unreconciled'):
            c.history(self.cfg, self.item, 'baseline')

    def test_quota_and_authentication_never_become_exhausted_items(self):
        self.attempt(1, pause_reason='rate_limit')
        self.attempt(2, pause_reason='authentication')
        self.attempt(3, pause_reason='provider_error')
        attempts, outcome = c.history(self.cfg, self.item, 'baseline')
        self.assertIsNone(outcome)
        self.assertEqual(c.infrastructure_attempts(attempts), 1)

    def test_no_budget_means_no_provider_or_readiness_work(self):
        with patch.object(runtime, 'run_attempt') as run, patch.object(c, 'readiness') as preflight:
            with self.assertRaisesRegex(c.Blocked, 'authorization'):
                c.run_batch({}, self.cfg, {}, 'finqa', 1)
            run.assert_not_called()
            preflight.assert_not_called()

    def test_closure_refuses_pending_missing_arm(self):
        self.attempt(1, 'complete')
        with patch.object(c, 'verify_freeze'):
            with self.assertRaisesRegex(c.Blocked, 'pending conditions'):
                c.close_generation({}, self.cfg, {'items': [self.item]}, 'finqa')
        self.assertFalse((self.root / 'closed').exists())

    def test_read_evidence_resolves_relative_paths_without_guessing(self):
        summary = {'reads': [{'request': {'file_path': 'input/p.txt'}, 'delivered': True},
                             {'request': {'file_path': 'other/p.txt'}, 'delivered': True}]}
        result = list(c.read_record(summary, self.root / 'input/p.txt', self.root))
        self.assertEqual(len(result), 1)

    def test_mutated_response_is_not_reused(self):
        p = self.attempt(1, 'complete')
        (p / 'summary.json').chmod(0o644)
        (p / 'summary.json').write_text('{}')
        with self.assertRaisesRegex(runtime.RuntimeBlocked, 'hash mismatch'):
            c.history(self.cfg, self.item, 'baseline')

    def test_scoring_resume_reuses_bound_completed_batch(self):
        item = {**self.item, 'input_sha256': 'input-hash'}
        manifest = {'items': [item], 'manifest_sha256': 'manifest-hash'}
        config = {'scoring': {'study_root': str(self.root)}, 'freeze': {'commit': 'synthetic'}}
        c.write_once(self.root / 'closed/finqa.json', {'manifest_sha256': 'manifest-hash', 'receipts': {}})
        outcome = {'path': self.root, 'summary': {'final_text': '1', 'texts': ['1']}}
        invocations = []

        def score(cfg, benchmark, responses, destination, retained):
            arm = destination.parents[1].name
            invocations.append(arm)
            destination.mkdir(parents=True)
            (destination / 'oracle.txt').write_text(arm)
            if arm == 'old' and invocations.count('old') == 1:
                raise c.scoring.ScoringBlocked('synthetic interrupted scorer')
            return [{'item': 'x', 'status': 'complete', 'passed': 1, 'score': 1}]

        with patch.object(c, 'verify_freeze'), patch.object(c, 'history', return_value=([], outcome)), \
                patch.object(c.scoring, 'score_responses', side_effect=score):
            with self.assertRaisesRegex(c.scoring.ScoringBlocked, 'interrupted'):
                c.score_closed(config, self.cfg, manifest, 'finqa')
            result = c.score_closed(config, self.cfg, manifest, 'finqa')
            self.assertEqual(result['rows'], 3)
            self.assertEqual(invocations, ['baseline', 'old', 'old', 'candidate'])
            # Idempotent resume verifies stored bytes; it makes no new scorer calls.
            c.score_closed(config, self.cfg, manifest, 'finqa')
            self.assertEqual(len(invocations), 4)
            changed = self.root / 'scores/finqa/baseline/1/attempt-1/oracle.txt'
            changed.write_text('corrupted')
            with self.assertRaisesRegex(c.Blocked, 'receipt changed'):
                c.score_closed(config, self.cfg, manifest, 'finqa')


if __name__ == '__main__':
    unittest.main()
