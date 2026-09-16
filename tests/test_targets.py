import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'skills/instruction-audit/scripts'))
from targets import load_target
import build_agents


class TargetTests(unittest.TestCase):
    def test_user_selected_skill_and_agents(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'SKILL.md').write_text('---\nname: chosen\n---\nSpecific selected instruction.', encoding='utf-8')
            (root / 'AGENTS.md').write_text('Project instruction.', encoding='utf-8')
            text, metadata = load_target(root)
            self.assertIn('Specific selected', text)
            self.assertEqual(metadata['kind'], 'skill')
            self.assertEqual(load_target(root / 'AGENTS.md')[1]['kind'], 'agents')
            case = root / 'case.json'
            case.write_text(json.dumps({'name': 'target test', 'models': ['placeholder'], 'protected': 'Mandatory rule.', 'original': 'Wrong original.', 'tasks': [{'id': 'one', 'split': 'holdout', 'prompt': 'Task', 'expected': 'answer'}]}), encoding='utf-8')
            plan = build_agents.build(case, root / 'run', ['a', 'b'], ['a', 'b'], target=root)
            prompts = [r['spawnArguments']['message'] for r in plan['trials']]
            self.assertEqual(sum('Specific selected' in p for p in prompts), 2)
            self.assertTrue(all('Wrong original' not in p for p in prompts))
            self.assertTrue(all('Mandatory rule.' in p for p in prompts))
            self.assertEqual(json.loads((root / 'run/manifest.json').read_text())['case']['target']['kind'], 'skill')

    def test_missing_empty_and_noninstruction_targets(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with self.assertRaises(FileNotFoundError):
                load_target(root)
            (root / 'SKILL.md').write_text('   ')
            with self.assertRaises(ValueError):
                load_target(root)
            (root / 'README.md').write_text('not a selected instruction')
            with self.assertRaises(ValueError):
                load_target(root / 'README.md')
