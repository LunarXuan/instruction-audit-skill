"""Read the explicitly selected instruction entry point, without executing package code."""
from pathlib import Path


def load_target(target):
    path = Path(target).absolute()
    if path.is_dir():
        path = path / 'SKILL.md'
    for item in (path, *path.parents):
        if item.is_symlink() or (hasattr(item, 'is_junction') and item.is_junction()):
            raise ValueError('Target must not follow symlinks or junctions')
    if path.name.lower() not in ('skill.md', 'agents.md'):
        raise ValueError('Select AGENTS.md, SKILL.md, or a Skill directory containing SKILL.md')
    with path.open('rb') as stream:
        raw = stream.read(1_000_001)
    if len(raw) > 1_000_000:
        raise ValueError('Target exceeds 1 MB')
    text = raw.decode('utf-8-sig')
    if not text.strip():
        raise ValueError('Target instructions are empty')
    return text, {'kind': 'skill' if path.name.lower() == 'skill.md' else 'agents',
                  'path': str(path), 'scope': 'instruction-text',
                  'resources': 'Coordinator must inspect referenced resources and keep required capabilities equal; no scripts were executed or copied by this loader.'}
