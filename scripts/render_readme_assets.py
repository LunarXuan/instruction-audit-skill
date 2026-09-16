"""Render new bilingual documentation diagrams (Pillow is optional, docs-only)."""
from pathlib import Path
import json
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets'
OUT.mkdir(exist_ok=True)
BG, PANEL, WHITE, DIM, MINT, AMBER = '#101923', '#1b2a36', '#f3f2e9', '#b2c0ca', '#8fe1c1', '#f2ba76'
FONT = next((p for p in ['C:/Windows/Fonts/msyh.ttc', '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', '/System/Library/Fonts/PingFang.ttc'] if Path(p).exists()), None)
if FONT is None:
    raise SystemExit('Install a CJK font and add its path to FONT candidates to render bilingual assets.')

def text(d, xy, value, size=26, color=WHITE):
    d.text(xy, value, font=ImageFont.truetype(FONT, size), fill=color)

def frame(label, title, subtitle):
    im = Image.new('RGB', (1440, 900), BG)
    d = ImageDraw.Draw(im)
    text(d, (64, 35), 'instruction-audit  /  ' + label, 22, MINT)
    text(d, (64, 95), title, 43)
    text(d, (64, 166), subtitle, 23, DIM)
    return im, d

def box(d, bounds, title, lines, accent=MINT):
    x,y,_,_ = bounds
    d.rounded_rectangle(bounds, radius=16, fill=PANEL, outline=accent, width=2)
    text(d, (x+24,y+19), title, 29, accent)
    for i,line in enumerate(lines):
        text(d, (x+24,y+69+i*37), line, 23)

def arrow(d, start, end):
    d.line([start,end], fill=MINT, width=3)
    x,y = end
    d.polygon([(x,y),(x-10,y-16),(x+10,y-16)],fill=MINT)

responses = json.loads((ROOT / 'examples/host-smoke-responses.json').read_text(encoding='utf-8'))['responses']
assert len(responses) == 2 and all(r['response']['identitySource']=='unknown' for r in responses)
assert all(r['response']['answer']=='10' and not r['response']['synthetic'] for r in responses)
for zh in (False,True):
    lang = 'zh' if zh else 'en'
    im,d = frame('WORKFLOW', '指定两个模型，让指令接受测试' if zh else 'Two models. Instructions put to the test.',
                 '流程示意 · 主模型调度，宿主执行；无需额外 API Key' if zh else 'Conceptual workflow · coordinated by your agent, executed by your host')
    box(d,(64,235,1376,395),'01  选择对象与任务' if zh else '01  Choose the target and tasks',
        ['AGENTS.md / SKILL.md / 用户指定的 Skill', '提取共同必要约束，准备原版、移除可选说明、精简候选。'] if zh else
        ['AGENTS.md / SKILL.md / a selected Skill', 'Preserve required rules; prepare original, without-optional, and candidate text.'])
    arrow(d,(385,395),(385,438)); arrow(d,(1055,395),(1055,438))
    box(d,(64,440,704,636),'02A  模型 A 子智能体' if zh else '02A  Model A subagents',
        ['相同任务与条件，每次使用全新上下文。','标准答案由主模型保管。','宿主必须支持模型选择与独立会话。'] if zh else
        ['Same tasks and conditions; fresh context.','Expected answers stay with the coordinator.','Requires model-selectable host sessions.'])
    box(d,(736,440,1376,636),'02B  模型 B 子智能体' if zh else '02B  Model B subagents',
        ['与模型 A 分开执行，记录真实结果。','不通过提示词假扮另一个模型。','调用消耗宿主正常额度。'] if zh else
        ['Separate execution and actual observations.','No role-played model identities.','Calls consume normal host allowance.'])
    arrow(d,(385,636),(385,676)); arrow(d,(1055,636),(1055,676))
    box(d,(64,678,1376,823),'03  主模型综合评审 → recommendation.md' if zh else '03  Main-model review → recommendation.md',
        ['质量优先，再看有来源的时间、用量和公开执行轨迹；未知就明确标注。'] if zh else
        ['Quality first, then sourced timing, usage and public execution evidence.'])
    text(d,(64,847),'不自动删除指令 · 文本评估不等于整包兼容性测试' if zh else 'No automatic deletion · text evaluation is not whole-package compatibility',21,DIM)
    im.save(OUT / f'workflow-{lang}.png')

    im,d = frame('EVIDENCE EXAMPLE', '保留建议必须来自可核查的证据' if zh else 'Recommendations need observable evidence.',
                 '真实宿主微型试跑 · 单一宿主模型标签 · 非双模型能力测试' if zh else 'Real host smoke · one host-model label · not a two-model benchmark')
    box(d,(64,237,704,493),'实际观察' if zh else 'Observed',
        ['2 次全新子智能体调用','原版回答：10；移除可选说明：10','均通过同一个算术题的精确答案检查。','仅 1 个任务，不代表真实项目效果。'] if zh else
        ['2 fresh child calls','Original: 10  /  Without optional: 10','Both match the arithmetic answer.','Only 1 task; not representative evidence.'])
    box(d,(736,237,1376,493),'不可用的数据' if zh else 'Unavailable',
        ['实际模型身份：未知','思考时长与总耗时：未记录','token 与订阅额度：未记录','不填零，也不推测隐藏思维链。'] if zh else
        ['Resolved model identity: unknown','Thinking and elapsed time: unrecorded','Tokens and quota: unrecorded','No invented zeros or private reasoning.'],AMBER)
    box(d,(64,536,1376,725),'INCONCLUSIVE  /  证据不足' if zh else 'INCONCLUSIVE  /  insufficient evidence',
        ['可证明调用与记录流程能走通；不能证明旧说明已经无用。','主模型保留限制，针对真实 Skill 设计任务后再比较。'] if zh else
        ['This checks dispatch and recording; it does not prove instructions are redundant.','The main model retains uncertainty and proposes representative follow-up tasks.'],AMBER)
    text(d,(64,773),'来源 / Source: examples/host-smoke-responses.json + host-smoke-report.md',23,DIM)
    text(d,(64,820),'设计化证据摘要，不是产品界面截图。' if zh else 'Designed evidence summary, not an application screenshot.',23,DIM)
    im.save(OUT / f'evidence-{lang}.png')
print('Rendered four bilingual README images from workflow definitions and recorded evidence.')
