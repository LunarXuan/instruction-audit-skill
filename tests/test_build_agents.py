import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'skills/instruction-audit/scripts'))
import build_agents


class BuildAgentsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.case = self.root / 'case.json'
        self.case.write_text(json.dumps({'name': 'test', 'models': ['placeholder'], 'protected': 'Return only answer.', 'original': 'Check calculation.', 'tasks': [{'id': 'one', 'split': 'holdout', 'prompt': 'Compute 2+3.', 'expected': 'SECRET_EXPECTED'}]}), encoding='utf-8')

    def test_two_models_and_fresh_blinded_dispatch(self):
        plan = build_agents.build(self.case, self.root / 'run', ['a', 'b'], ['a', 'b'])
        self.assertEqual(plan['plannedSessions'], 4)
        self.assertEqual(plan['status'], 'NOT_EXECUTED')
        self.assertEqual({r['spawnArguments']['model'] for r in plan['trials']}, {'a', 'b'})
        self.assertEqual(len({r['spawnArguments']['task_name'] for r in plan['trials']}), 4)
        for row in plan['trials']:
            self.assertEqual(row['spawnArguments']['fork_turns'], 'none')
            self.assertNotIn('SECRET_EXPECTED', row['spawnArguments']['message'])
        self.assertEqual(json.loads(self.case.read_text())['models'], ['placeholder'])

    def test_unavailable_or_duplicate_models_do_not_create_run(self):
        for models in [['a', 'missing'], ['a', 'a']]:
            with self.assertRaises(ValueError):
                build_agents.build(self.case, self.root / 'run', models, ['a', 'b'])
            self.assertFalse((self.root / 'run').exists())

    def test_call_limit_and_existing_directory(self):
        with self.assertRaises(ValueError):
            build_agents.build(self.case, self.root / 'run', ['a', 'b'], ['a', 'b'], 3)
        self.assertFalse((self.root / 'run').exists())
        build_agents.build(self.case, self.root / 'run', ['a', 'b'], ['a', 'b'])
        with self.assertRaises(FileExistsError):
            build_agents.build(self.case, self.root / 'run', ['a', 'b'], ['a', 'b'])


if __name__ == '__main__':
    unittest.main()
