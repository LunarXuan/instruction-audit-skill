import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

MODULE = Path(__file__).resolve().parents[1] / 'skills/instruction-audit/scripts/audit.py'
SPEC = importlib.util.spec_from_file_location('telemetry_audit', MODULE)
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


class TelemetryTests(unittest.TestCase):
    def response(self, **extra):
        result = dict(status='COMPLETED', answer='5', requestedModel='model', observedModel='model',
                      identitySource='host-metadata', sessionId='session', isolated=True, synthetic=False)
        result.update(extra)
        return result

    def metric(self, value=10, unit='ms', source='host', evidence='Host result metadata'):
        return dict(value=value, unit=unit, source=source, evidence=evidence)

    def test_reject_invalid_numbers_units_and_provenance(self):
        bad = [self.metric(value=v) for v in (True, -1, float('nan'), float('inf'), '10', 10**400)]
        bad += [self.metric(unit='seconds'), self.metric(source='self-report'), self.metric(evidence=' ')]
        for measurement in bad:
            with self.subTest(measurement=measurement), self.assertRaises(ValueError):
                audit.validate_response(self.response(metrics={'elapsedMs': measurement}), {'model': 'model'})
        for name, unit in [('thinkingMs', 'ms'), ('inputTokens', 'tokens'), ('quotaUsed', 'credits')]:
            with self.subTest(name=name), self.assertRaises(ValueError):
                audit.validate_response(self.response(metrics={name: self.metric(unit=unit, source='coordinator-timer')}), {'model': 'model'})
        for metrics in (None, [], {'unknown': self.metric()}, {'elapsedMs': 2}):
            with self.subTest(metrics=metrics), self.assertRaises(ValueError):
                audit.validate_response(self.response(metrics=metrics), {'model': 'model'})

    def test_private_reasoning_rejected_public_summary_escaped(self):
        for name in ('rawChainOfThought', 'thinkingProcess', 'privateReasoning'):
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'executionSummary'):
                audit.validate_response(self.response(**{name: 'private'}), {'model': 'model'})
        response = self.response(executionSummary='<tool>|[link]\n*done*')
        audit.validate_response(response, {'model': 'model'})
        text = '\n'.join(audit.telemetry_report([(dict(id='t001', model='model', variant='original'), response, True)], ['model'], ['original']))
        self.assertIn('&lt;tool&gt;&#124;&#91;link&#93; &#42;done&#42;', text)
        self.assertNotIn('<tool>', text)

    def test_means_coverage_and_mixed_units_exclude_incomplete(self):
        rows = []
        for i in range(4):
            response = self.response(status='COMPLETED' if i < 3 else 'ERROR')
            if i != 2:
                response['metrics'] = {'elapsedMs': self.metric(value=[10, 30, 0, 9999][i]),
                                       'quotaUsed': self.metric(value=1, unit='credits' if i == 0 else 'percent')}
            rows.append((dict(id=f't{i+1:03d}', model='model', variant='original'), response, i < 3))
        text = '\n'.join(audit.telemetry_report(rows, ['model'], ['original']))
        self.assertIn('| elapsedMs | 20 | ms | 2/3 |', text)
        self.assertIn('| quotaUsed | not aggregated | mixed: credits, percent | 2/3 |', text)
        self.assertIn('| thinkingMs | unknown | unknown | 0/3 |', text)
        self.assertIn('| t004 | ERROR | elapsedMs | 9999 |', text)

    def test_measurements_persist_with_provenance_and_no_inferred_quota(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            case = dict(name='Test', models=['model'], protected='Protect.', original='Instructions.',
                        tasks=[dict(id='task', split='holdout', prompt='2+3', expected='5')])
            (root / 'case.json').write_text(json.dumps(case), encoding='utf-8')
            run = root / 'run'
            audit.prepare(root / 'case.json', run)
            response = self.response(metrics={'inputTokens': self.metric(value=123, unit='tokens', evidence='usage.input_tokens'),
                                              'elapsedMs': self.metric(value=0, source='coordinator-timer', evidence='monotonic end-start')})
            (root / 'response.json').write_text(json.dumps(response), encoding='utf-8')
            audit.record(run, 't001', root / 'response.json')
            recorded = audit.read_json(run / 'results/t001.json')
            self.assertEqual(recorded['metrics'], response['metrics'])
            self.assertNotIn('quotaUsed', recorded['metrics'])
            text = audit.report(run)
            self.assertIn('| inputTokens | 123 | tokens | host | usage.input', text)
            self.assertIn('| elapsedMs | 0 | ms | coordinator-timer | monotonic end-start |', text)
            self.assertIn('| quotaUsed | unknown | unknown | unknown | unknown |', text)

    def test_old_responses_remain_valid_missing_telemetry_preserves_quality(self):
        audit.validate_response(self.response(), {'model': 'model'})
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            case = dict(name='Legacy', models=['model'], protected='Protect.', original='Instructions.',
                        tasks=[dict(id='task', split='holdout', prompt='2+3', expected='5')])
            (root / 'case.json').write_text(json.dumps(case), encoding='utf-8')
            audit.prepare(root / 'case.json', root / 'run')
            for trial_id in ('t001', 't002'):
                response = self.response(sessionId=trial_id)
                (root / 'response.json').write_text(json.dumps(response), encoding='utf-8')
                audit.record(root / 'run', trial_id, root / 'response.json')
            text = audit.report(root / 'run')
            self.assertIn('**Overall: COMPLETE OBSERVATIONS', text)
            self.assertIn('**INCONCLUSIVE**', text)
            self.assertIn('| elapsedMs | unknown | unknown | 0/1 |', text)
            self.assertIn('Tokens are not subscription quota', text)


if __name__ == '__main__':
    unittest.main()
