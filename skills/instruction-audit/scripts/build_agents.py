#!/usr/bin/env python3
"""Build two model-specific dispatch plans; the host agent executes them, not this script."""
import argparse
from pathlib import Path
import sys
import audit


def build(case_path, out, models, available_models, max_trials=12, target=None):
    if len(models) != 2 or models[0] == models[1]:
        raise ValueError('Choose exactly two distinct model IDs')
    missing = [model for model in models if model not in available_models]
    if missing:
        raise ValueError('Requested models absent from host capability list: ' + ', '.join(missing))
    audit.prepare(case_path, out, models=models, max_trials=max_trials, target=target)
    directory, manifest = audit.load_run(out)
    dispatches = []
    for trial in manifest['trials']:
        prompt = (directory / 'prompts' / (trial['id'] + '.md')).read_text(encoding='utf-8')
        dispatches.append({
            'trialId': trial['id'],
            'group': 'model-a' if trial['model'] == models[0] else 'model-b',
            'spawnArguments': {
                'task_name': 'audit_' + trial['id'],
                'fork_turns': 'none',
                'model': trial['model'],
                'message': prompt,
            },
        })
    plan = {
        'status': 'NOT_EXECUTED',
        'groups': [{'name': 'model-a', 'model': models[0]}, {'name': 'model-b', 'model': models[1]}],
        'plannedSessions': len(dispatches),
        'capabilitySource': 'Coordinator-supplied host model list; access is only confirmed by actual dispatch.',
        'execution': 'Use native spawn_agent only if its actual schema supports these arguments. Each row needs a fresh child; never reuse a child between trials. Task names may need a run-specific prefix.',
        'trials': dispatches,
    }
    audit.write_new(directory / 'dispatch.json', audit.dump(plan))
    return plan


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('case')
    parser.add_argument('--models', nargs=2, required=True)
    parser.add_argument('--available-models', nargs='+', required=True)
    parser.add_argument('--max-trials', type=int, default=12)
    parser.add_argument('--out', required=True)
    parser.add_argument('--target', help='AGENTS.md, SKILL.md, or the selected Skill directory')
    args = parser.parse_args()
    try:
        plan = build(args.case, args.out, args.models, args.available_models, args.max_trials, args.target)
        print(audit.dump({'status': plan['status'], 'groups': plan['groups'], 'plannedSessions': plan['plannedSessions'], 'dispatchFile': str(Path(args.out) / 'dispatch.json')}), end='')
        return 0
    except (ValueError, OSError, KeyError, TypeError) as error:
        print('Error: ' + str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
