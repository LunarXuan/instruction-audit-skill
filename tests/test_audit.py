import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

MODULE = Path(__file__).resolve().parents[1] / 'skills/instruction-audit/scripts/audit.py'
SPEC = importlib.util.spec_from_file_location('audit', MODULE)
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.case = dict(name='Example', models=['old', 'new'], protected='Keep protected policy.',
                         original='Original unique text.', candidate='Candidate unique text.', repeats=2,
                         maxTrials=24, tasks=[dict(id='one', split='holdout', prompt='Compute 2+3.', expected='HIDDEN_EXPECTATION'),
                                             dict(id='two', split='development', prompt='Compute 3+4.', expected='7')])

    def save(self, name, value):
        path = self.root / name
        path.write_text(json.dumps(value), encoding='utf-8')
        return path

    def prepare(self):
        run = self.root / 'run'
        audit.prepare(self.save('case.json', self.case), run)
        self.manifest = json.loads((run / 'manifest.json').read_text(encoding='utf-8'))
        return run

    def response(self, trial):
        expected = next(t['expected'] for t in self.case['tasks'] if t['id'] == trial['taskId'])
        return dict(answer=expected, status='COMPLETED', requestedModel=trial['model'], observedModel=trial['model'],
                    identitySource='host-metadata', sessionId=trial['id'], isolated=True, synthetic=False)

    def fill(self, run, change=None):
        for index, trial in enumerate(self.manifest['trials']):
            response = self.response(trial)
            if change:
                change(index, response)
            audit.record(run, trial['id'], self.save('response.json', response))

    def test_expected_and_other_condition_not_in_prompt(self):
        run = self.prepare()
        for trial in self.manifest['trials']:
            prompt = (run / 'prompts' / (trial['id'] + '.md')).read_text(encoding='utf-8')
            self.assertNotIn('HIDDEN_EXPECTATION', prompt)
            self.assertIn('Keep protected policy.', prompt)
            self.assertEqual('Original unique text.' in prompt, trial['variant'] == 'original')
            self.assertEqual('Candidate unique text.' in prompt, trial['variant'] == 'candidate')

    def test_validation_before_output_creation(self):
        self.case['tasks'].append(self.case['tasks'][0])
        with self.assertRaises(ValueError):
            self.prepare()
        self.assertFalse((self.root / 'run').exists())

    def test_no_overwrite(self):
        run = self.prepare()
        with self.assertRaises(FileExistsError):
            audit.prepare(self.root / 'case.json', run)
        trial = self.manifest['trials'][0]
        response_path = self.save('response.json', self.response(trial))
        audit.record(run, trial['id'], response_path)
        with self.assertRaises(FileExistsError):
            audit.record(run, trial['id'], response_path)

    def test_missing_forces_inconclusive(self):
        result = audit.report(self.prepare())
        self.assertIn('**Overall: INCONCLUSIVE**', result)
        self.assertIn('missing result', result)

    def test_synthetic_forces_inconclusive(self):
        run = self.prepare()
        self.fill(run, lambda i, r: r.update(synthetic=True) if i == 0 else None)
        self.assertIn('**Overall: INCONCLUSIVE**', audit.report(run))

    def test_identity_unknown_mismatch_and_self_report(self):
        run = self.prepare()
        trial = self.manifest['trials'][0]
        response = self.response(trial)
        response['identitySource'] = 'model-self-report'
        with self.assertRaises(ValueError):
            audit.record(run, trial['id'], self.save('response.json', response))
        self.fill(run, lambda i, r: r.update(identitySource='unknown', observedModel=None) if i == 0 else r.update(observedModel='different'))
        self.assertIn('unknown or mismatched host model identity', audit.report(run))
        self.assertIn('**Overall: INCONCLUSIVE**', audit.report(run))

    def test_contaminated_and_reused_sessions(self):
        run = self.prepare()
        self.fill(run, lambda i, r: r.update(sessionId='same', isolated=False if i == 0 else True))
        result = audit.report(run)
        self.assertIn('session is not isolated', result)
        self.assertIn('session reused', result)
        self.assertIn('**Overall: INCONCLUSIVE**', result)

    def test_blocked_and_error_rows(self):
        run = self.prepare()
        self.fill(run, lambda i, r: r.update(status='BLOCKED' if i == 0 else 'ERROR', answer='', note='<problem>|[x]'))
        result = audit.report(run)
        self.assertIn('BLOCKED', result)
        self.assertIn('ERROR', result)
        self.assertIn('&lt;problem&gt;&#124;&#91;x&#93;', result)
        self.assertIn('**Overall: INCONCLUSIVE**', result)

    def test_repeats_do_not_inflate_paired_n(self):
        run = self.prepare()
        self.fill(run)
        result = audit.report(run)
        self.assertIn('COMPLETE OBSERVATIONS', result)
        self.assertEqual(result.count('paired holdout n=1;'), 2)
        self.assertNotIn('KEEP_CANDIDATE (', result)

    def test_passed_claim_ignored(self):
        run = self.prepare()
        trial = self.manifest['trials'][0]
        response = self.response(trial)
        response.update(answer='wrong', passed=True)
        self.assertFalse(audit.record(run, trial['id'], self.save('response.json', response))['passed'])

    def test_modified_manifest_cannot_hide_missing_trials(self):
        run = self.prepare()
        self.manifest['trials'].pop()
        (run / 'manifest.json').write_text(json.dumps(self.manifest), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'missing matrix cells'):
            audit.report(run)

    def test_safety_limits_and_requested_model(self):
        run = self.prepare()
        trial = self.manifest['trials'][0]
        response = self.response(trial)
        response['requestedModel'] = '../wrong'
        with self.assertRaises(ValueError):
            audit.record(run, trial['id'], self.save('response.json', response))
        oversized = self.root / 'huge.json'
        oversized.write_bytes(b' ' * (audit.LIMIT + 1))
        with self.assertRaises(ValueError):
            audit.read_json(oversized)

    def test_symlink_rejected_when_supported(self):
        self.prepare()
        link = self.root / 'linked.json'
        try:
            link.symlink_to(self.root / 'case.json')
        except OSError:
            self.skipTest('Symlink creation unavailable to this account')
        with self.assertRaises(ValueError):
            audit.read_json(link)


if __name__ == '__main__':
    unittest.main()
