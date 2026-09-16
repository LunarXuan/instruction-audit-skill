#!/usr/bin/env python3
"""Offline trial preparation, host-result recording, and conservative summaries."""
import argparse
import json
import math
from pathlib import Path
import re
import sys

LIMIT = 1_000_000
SAFE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,79}$")
METRICS = ('elapsedMs', 'thinkingMs', 'inputTokens', 'outputTokens', 'reasoningTokens', 'quotaUsed')


def fail(message):
    raise ValueError(message)


def no_links(path):
    path = Path(path).absolute()
    for item in (path, *path.parents):
        if item.is_symlink() or (hasattr(item, 'is_junction') and item.is_junction()):
            fail('Symlink/junction paths are not allowed')
    return path


def read_json(path):
    path = no_links(path)
    with path.open('rb') as stream:
        data = stream.read(LIMIT + 1)
    if len(data) > LIMIT:
        fail('JSON exceeds 1 MB')
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                fail('Duplicate JSON key: ' + key)
            result[key] = value
        return result
    value = json.loads(data, object_pairs_hook=unique)
    if not isinstance(value, dict):
        fail('Expected a JSON object')
    return value


def write_new(path, text):
    path = no_links(path)
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(text)


def dump(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + '\n'


def text_field(value, name):
    if not isinstance(value, str) or not value.strip():
        fail(name + ' must be a nonempty string')
    return value


def integer(value, name, low, high):
    if type(value) is not int or not low <= value <= high:
        fail(f'{name} must be an integer in {low}..{high}')
    return value


def validate_case(case):
    text_field(case.get('name'), 'name')
    if 'target' in case and not isinstance(case['target'], dict):
        fail('target metadata must be an object')
    for key in ('protected', 'original'):
        text_field(case.get(key), key)
    if 'candidate' in case:
        text_field(case['candidate'], 'candidate')
    models = case.get('models')
    if not isinstance(models, list) or not 1 <= len(models) <= 4:
        fail('models requires 1..4 unique host model labels')
    for model in models:
        text_field(model, 'model')
    if len(set(models)) != len(models):
        fail('Duplicate model labels')
    repeats = integer(case.get('repeats', 1), 'repeats', 1, 5)
    maximum = integer(case.get('maxTrials', 12), 'maxTrials', 1, 120)
    tasks = case.get('tasks')
    if not isinstance(tasks, list) or not 1 <= len(tasks) <= 50:
        fail('tasks requires 1..50 tasks')
    ids = set()
    for task in tasks:
        if not isinstance(task, dict):
            fail('Each task must be an object')
        task_id = task.get('id')
        if not isinstance(task_id, str) or not SAFE.fullmatch(task_id) or task_id in ids:
            fail('Task IDs must be unique safe identifiers')
        ids.add(task_id)
        if task.get('split') not in ('development', 'holdout'):
            fail('Task split must be development or holdout')
        text_field(task.get('prompt'), 'prompt')
        if not isinstance(task.get('expected'), str):
            fail('expected must be a string')
    variants = ['without', 'original'] + (['candidate'] if 'candidate' in case else [])
    count = len(tasks) * len(models) * repeats * len(variants)
    if count > maximum:
        fail(f'{count} trials exceed maxTrials={maximum}')
    return repeats, variants


def prepare(case_path, out, *, models=None, max_trials=None, target=None):
    case = read_json(case_path)
    if target is not None:
        from targets import load_target
        original, metadata = load_target(target)
        case['original'] = original
        case['target'] = metadata
    if models is not None:
        case['models'] = models
    if max_trials is not None:
        case['maxTrials'] = max_trials
    repeats, variants = validate_case(case)
    out = no_links(out)
    trials = []
    prompts = []
    for repeat in range(repeats):
        for index, task in enumerate(case['tasks']):
            ordered = variants if (repeat + index) % 2 == 0 else list(reversed(variants))
            models = case['models'] if (repeat + index) % 2 == 0 else list(reversed(case['models']))
            for variant in ordered:
                for model in models:
                    trial_id = f't{len(trials) + 1:03d}'
                    trials.append(dict(id=trial_id, model=model, variant=variant,
                                       taskId=task['id'], split=task['split'], repeat=repeat + 1))
                    content = '# Common protected instructions\n\n' + case['protected']
                    if variant != 'without':
                        content += '\n\n# Additional instructions\n\n' + case[variant]
                    content += '\n\n# Task\n\n' + task['prompt'] + '\n'
                    prompts.append((trial_id, content))
    manifest_text = dump(dict(version=1, case=case, trials=trials))
    if len(manifest_text.encode('utf-8')) > LIMIT:
        fail('Prepared manifest exceeds 1 MB; reduce input size')
    out.mkdir(parents=True, exist_ok=False)
    (out / 'prompts').mkdir()
    (out / 'results').mkdir()
    write_new(out / 'manifest.json', manifest_text)
    for trial_id, prompt in prompts:
        write_new(out / 'prompts' / (trial_id + '.md'), prompt)
    return dict(directory=str(out), trials=len(trials))


def load_run(directory):
    directory = no_links(directory)
    manifest = read_json(directory / 'manifest.json')
    repeats, variants = validate_case(manifest['case'])
    if manifest.get('version') != 1 or not isinstance(manifest.get('trials'), list):
        fail('Unsupported manifest')
    seen = set()
    cells = set()
    case = manifest['case']
    tasks = {t['id']: t for t in case['tasks']}
    expected_cells = {(model, variant, task['id'], repeat)
                      for model in case['models'] for variant in variants
                      for task in case['tasks'] for repeat in range(1, repeats + 1)}
    for trial in manifest['trials']:
        trial_id = trial.get('id')
        if not isinstance(trial_id, str) or not re.fullmatch(r't\d{3}', trial_id) or trial_id in seen:
            fail('Invalid manifest trial ID')
        seen.add(trial_id)
        cell = (trial.get('model'), trial.get('variant'), trial.get('taskId'), trial.get('repeat'))
        if cell not in expected_cells or cell in cells or type(trial.get('repeat')) is not int:
            fail('Invalid or duplicate manifest matrix cell')
        if trial.get('split') != tasks[trial['taskId']]['split']:
            fail('Manifest task split mismatch')
        cells.add(cell)
    if cells != expected_cells:
        fail('Manifest is missing matrix cells')
    no_links(directory / 'results')
    return directory, manifest


def validate_response(response, trial):
    if any(key in response for key in ('rawChainOfThought', 'thinkingProcess', 'privateReasoning')):
        fail('Private chain-of-thought fields are not accepted; use executionSummary for public tool traces or a high-level summary')
    if 'executionSummary' in response and not isinstance(response['executionSummary'], str):
        fail('executionSummary must be a string containing only public observations')
    metrics = response.get('metrics', {})
    if not isinstance(metrics, dict):
        fail('metrics must be an object; omit unavailable measurements')
    for name, measurement in metrics.items():
        if name not in METRICS or not isinstance(measurement, dict):
            fail('Unknown or malformed metric: ' + str(name))
        value = measurement.get('value')
        try:
            valid_number = type(value) in (int, float) and math.isfinite(value) and value >= 0
        except OverflowError:
            valid_number = False
        if not valid_number:
            fail(name + '.value must be a nonnegative finite number')
        unit = text_field(measurement.get('unit'), name + '.unit')
        expected_unit = 'ms' if name.endswith('Ms') else 'tokens' if name.endswith('Tokens') else None
        if expected_unit and unit != expected_unit:
            fail(name + '.unit must be ' + expected_unit)
        source = measurement.get('source')
        if source not in ('host', 'coordinator-timer') or (source == 'coordinator-timer' and name != 'elapsedMs'):
            fail(name + '.source must be host (coordinator-timer is allowed only for elapsedMs)')
        text_field(measurement.get('evidence'), name + '.evidence')
    if response.get('status') not in ('COMPLETED', 'BLOCKED', 'ERROR'):
        fail('status must be COMPLETED, BLOCKED, or ERROR')
    if not isinstance(response.get('answer'), str):
        fail('answer is required for every status; use empty string if blocked/error')
    if response.get('requestedModel') != trial['model']:
        fail('requestedModel must match the trial model label')
    if 'observedModel' not in response or (response['observedModel'] is not None and not isinstance(response['observedModel'], str)):
        fail('observedModel must be a string or null')
    if response.get('identitySource') not in ('host-metadata', 'unknown'):
        fail('identitySource must be host-metadata or unknown; self-reports are not evidence')
    if 'sessionId' not in response or (response['sessionId'] is not None and not isinstance(response['sessionId'], str)):
        fail('sessionId must be a string or null')
    for key in ('isolated', 'synthetic'):
        if type(response.get(key)) is not bool:
            fail(key + ' must be boolean')
    if 'note' in response and not isinstance(response['note'], str):
        fail('note must be a string')


def record(directory, trial_id, response_path):
    directory, manifest = load_run(directory)
    trial = next((t for t in manifest['trials'] if t['id'] == trial_id), None)
    if trial is None:
        fail('Unknown trial')
    response = read_json(response_path)
    validate_response(response, trial)
    expected = next(t['expected'] for t in manifest['case']['tasks'] if t['id'] == trial['taskId'])
    response['passed'] = response['status'] == 'COMPLETED' and response['answer'] == expected
    write_new(directory / 'results' / (trial_id + '.json'), dump(response))
    return dict(trial=trial_id, passed=response['passed'])


def escape(value):
    return str(value).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('|', '&#124;').replace('\r', ' ').replace('\n', ' ').replace('`', '&#96;').replace('*', '&#42;').replace('_', '&#95;').replace('[', '&#91;').replace(']', '&#93;').replace('\\', '&#92;')


def telemetry_report(rows, models, variants):
    lines = ['', '## Recorded timing and usage', '',
             'Wall-clock elapsed time is not thinking time. Tokens are not subscription quota. Missing values are unknown, never zero; no quota is inferred from tokens. No hidden chain of thought is collected.', '',
             'Means below use completed trials only (all task splits). Coverage is measurements / completed trials, not evidence of paired efficiency gains. Mixed units are not aggregated. Missing telemetry does not alter quality conclusions and cannot establish an efficiency advantage.', '',
             '| Model | Variant | Metric | Mean | Unit | Coverage |', '|---|---|---|---:|---|---:|']
    for model in models:
        for variant in variants:
            completed = [r for t, r, _ in rows if t['model'] == model and t['variant'] == variant and r is not None and r['status'] == 'COMPLETED']
            for name in METRICS:
                measurements = [r['metrics'][name] for r in completed if name in r.get('metrics', {})]
                units = {m['unit'] for m in measurements}
                mean = 'unknown'
                unit = 'unknown'
                if len(units) == 1:
                    # Divide before summing to avoid overflow for otherwise valid large values.
                    mean = f"{math.fsum(m['value'] / len(measurements) for m in measurements):.6g}"
                    unit = escape(next(iter(units)))
                elif len(units) > 1:
                    mean = 'not aggregated'
                    unit = 'mixed: ' + ', '.join(escape(u) for u in sorted(units))
                lines.append(f'| {escape(model)} | {variant} | {name} | {mean} | {unit} | {len(measurements)}/{len(completed)} |')
    lines += ['', '### Per-trial measurement evidence', '',
              '| Trial | Status | Metric | Value | Unit | Source | Evidence |', '|---|---|---|---:|---|---|---|']
    for trial, response, _ in rows:
        status = response['status'] if response else 'MISSING'
        for name in METRICS:
            measurement = response.get('metrics', {}).get(name) if response else None
            cells = [escape(measurement[key]) for key in ('value', 'unit', 'source', 'evidence')] if measurement else ['unknown'] * 4
            lines.append('| ' + ' | '.join([trial['id'], status, name, *cells]) + ' |')
    lines += ['', '### Public execution summaries', '', '| Trial | Summary |', '|---|---|']
    for trial, response, _ in rows:
        summary = response.get('executionSummary') if response else None
        lines.append('| ' + trial['id'] + ' | ' + (escape(summary) if summary else 'unknown') + ' |')
    return lines


def report(directory):
    directory, manifest = load_run(directory)
    case = manifest['case']
    rows = []
    reasons = []
    sessions = set()
    tasks = {t['id']: t for t in case['tasks']}
    for trial in manifest['trials']:
        path = directory / 'results' / (trial['id'] + '.json')
        no_links(path)
        if not path.exists():
            reasons.append(trial['id'] + ': missing result')
            rows.append((trial, None, False))
            continue
        response = read_json(path)
        validate_response(response, trial)
        passed = response['status'] == 'COMPLETED' and response['answer'] == tasks[trial['taskId']]['expected']
        rows.append((trial, response, passed))
        observed = response['observedModel']
        if response['status'] != 'COMPLETED':
            reasons.append(trial['id'] + ': ' + response['status'])
        if response['synthetic']:
            reasons.append(trial['id'] + ': synthetic result')
        if response['identitySource'] != 'host-metadata' or not observed or not (observed == trial['model'] or observed.startswith(trial['model'] + '-')):
            reasons.append(trial['id'] + ': unknown or mismatched host model identity')
        if not response['isolated']:
            reasons.append(trial['id'] + ': session is not isolated')
        session = response['sessionId']
        if not session or not session.strip():
            reasons.append(trial['id'] + ': missing session identity')
        elif session in sessions:
            reasons.append(trial['id'] + ': session reused in matrix')
        else:
            sessions.add(session)
    lines = ['# Instruction audit: ' + escape(case['name']), '',
             '**Overall: INCONCLUSIVE**' if reasons else '**Overall: COMPLETE OBSERVATIONS — see comparison evidence below**', '',
             'Instruction-content evaluation, not native discovery. No automatic deletion. Model identity and isolation are supplied by the host operator; this offline tool cannot independently attest them.', '',
             'Exact answer matching is computed locally. Repeated executions are averaged within each holdout task; they do not increase the independent task count. Development tasks are excluded from comparison conclusions.', '',
             '| Model | Variant | Completed | Passed / completed |', '|---|---|---:|---:|']
    variants = ['without', 'original'] + (['candidate'] if 'candidate' in case else [])
    if 'target' in case:
        metadata = case['target']
        lines[2:2] = ['Target: ' + '; '.join(key + '=' + escape(metadata.get(key, 'unknown')) for key in ('kind', 'path', 'scope')), '']
    for model in case['models']:
        for variant in variants:
            selected = [(r, p) for t, r, p in rows if t['model'] == model and t['variant'] == variant]
            completed = sum(r is not None and r['status'] == 'COMPLETED' for r, _ in selected)
            passed = sum(p for _, p in selected)
            lines.append(f'| {escape(model)} | {variant} | {completed}/{len(selected)} | {passed}/{completed} |')
    lines += ['', '## Paired holdout observations', '', '| Model | Task | Original − without | Candidate − original |', '|---|---|---:|---:|']
    for model in case['models']:
        differences = []
        for task in case['tasks']:
            if task['split'] != 'holdout':
                continue
            values = {}
            for variant in variants:
                selected = [(r, p) for t, r, p in rows if t['model'] == model and t['variant'] == variant and t['taskId'] == task['id']]
                values[variant] = sum(p for _, p in selected) / len(selected) if selected and all(r is not None and r['status'] == 'COMPLETED' for r, _ in selected) else None
            difference = values['original'] - values['without'] if values['original'] is not None and values['without'] is not None else None
            candidate = values.get('candidate') - values['original'] if values.get('candidate') is not None and values['original'] is not None else None
            if difference is not None:
                differences.append(difference)
            fmt = lambda v: 'missing' if v is None else f'{v:+.3f}'
            lines.append(f'| {escape(model)} | {escape(task["id"])} | {fmt(difference)} | {fmt(candidate) if "candidate" in variants else "n/a"} |')
        n = len(differences)
        conclusion = 'INCONCLUSIVE'
        if n:
            delta = sum(differences) / n
            radius = math.sqrt(2 * math.log(40) / n)
            lower, upper = max(-1, delta - radius), min(1, delta + radius)
            if not reasons and lower > 0:
                conclusion = 'KEEP_CANDIDATE (original instructions show benefit; review evidence)'
            lines += ['', f'{escape(model)}: paired holdout n={n}; mean original − without={delta:+.3f}; 95% Hoeffding interval=[{lower:+.3f}, {upper:+.3f}]; **{conclusion}**.', '']
        else:
            lines += ['', escape(model) + ': paired holdout n=0; **INCONCLUSIVE**.', '']
    lines += ['Intervals assume independent representative tasks and are pointwise, not corrected across models. Small convenience samples cannot establish general redundancy. Candidate differences are descriptive only.', '', '## Evidence limitations', '']
    lines += ['- ' + escape(reason) for reason in reasons] if reasons else ['- No recorded completeness, identity, or isolation problem. This does not establish general validity beyond these tasks.']
    lines += ['', '## Observed failures and incomplete trials', '', '| Trial | Status | Observation |', '|---|---|---|']
    for trial, response, passed in rows:
        if not passed:
            lines.append('| ' + trial['id'] + ' | ' + (response['status'] if response else 'MISSING') + ' | ' + escape(response.get('note', 'Exact-match assertion failed') if response else 'No response recorded') + ' |')
    lines += telemetry_report(rows, case['models'], variants)
    lines += ['', 'Retain useful failure examples for agent review. No automatic deletion or RETIRE recommendation is produced. No API credentials or monetary estimates are used.', '']
    return '\n'.join(lines)


def main(argv=None):
    # Reports and user instructions may contain Unicode on legacy Windows consoles.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    p = commands.add_parser('prepare'); p.add_argument('case'); p.add_argument('--out', required=True); p.add_argument('--target')
    p = commands.add_parser('record'); p.add_argument('directory'); p.add_argument('--trial', required=True); p.add_argument('--response', required=True)
    p = commands.add_parser('report'); p.add_argument('directory'); p.add_argument('--out')
    args = parser.parse_args(argv)
    try:
        if args.command == 'prepare':
            print(dump(prepare(args.case, args.out, target=args.target)), end='')
        elif args.command == 'record':
            print(dump(record(args.directory, args.trial, args.response)), end='')
        else:
            result = report(args.directory)
            if args.out:
                write_new(args.out, result)
            else:
                print(result, end='')
        return 0
    except (ValueError, OSError, KeyError, TypeError) as error:
        print('Error: ' + str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
