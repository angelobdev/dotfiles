#!/usr/bin/env python3
"""Coding-agent adapters, session watcher, hooks and status line for the desktop assistant.

probe:      JSON with the configured or detected agent (available, agent, name, command).
launch:     JSON with the full command line desktop-ai runs in the drop-down console.
watch:      watches session transcripts/settings for agents without Claude Code hooks (Antigravity, Codex, Gemini)
            while the console window is alive, and removes agent.json when stopped.
hook:       one hook event on stdin -> $XDG_RUNTIME_DIR/desktop-shell/agent.json. Silent and exit 0 for Claude Code.
statusline: status line JSON on stdin -> ~/.local/state/desktop-shell/agent-usage.json and one terminal line.
"""
from common import write_atomic
import ctypes
from datetime import datetime
from i18n import tr
import fcntl
import json
import os
from pathlib import Path
import re
import select
import shlex
import shutil
import signal
import sys
import time

RUNTIME = Path(os.environ.get('XDG_RUNTIME_DIR') or f'/run/user/{os.getuid()}') / 'desktop-shell'
STATE = RUNTIME / 'agent.json'
SESSION = RUNTIME / 'agent-session.json'
USAGE = Path(os.environ.get('XDG_STATE_HOME') or Path.home() / '.local/state') / 'desktop-shell/agent-usage.json'
CONFIG = Path(os.environ.get('XDG_CONFIG_HOME') or Path.home() / '.config') / 'desktop/shell.json'
ACCOUNT = Path.home() / '.claude.json'
AGY_DIR = Path.home() / '.gemini/antigravity-cli'
GEMINI_DIR = Path.home() / '.gemini'
CODEX_DIR = Path.home() / '.codex'
DETAIL = 160
# Harnesses whose interactive TUI attaches local files/images with the @/path syntax; others take the plain path.
IMAGE_AT_AGENTS = {'antigravity', 'gemini'}

AGENTS = (
    ('antigravity', 'Antigravity', ('antigravity', 'agy')),
    ('claude', 'Claude', ('claude',)),
    ('codex', 'Codex', ('codex',)),
    ('gemini', 'Gemini', ('gemini',)),
    ('opencode', 'OpenCode', ('opencode',)),
    ('pi', 'Pi', ('pi',)),
)
ALIASES = {
    'agy': 'antigravity',
    'antigravity-cli': 'antigravity',
    'claude-code': 'claude',
    'codex-cli': 'codex',
    'gemini-cli': 'gemini',
}
AGENT_NAMES = {agent_id: name for agent_id, name, _ in AGENTS}

# Hook event -> state; Notification and the tool events depend on their payload (see state_for).
STATES = {'SessionStart': 'ready', 'UserPromptSubmit': 'working', 'PermissionRequest': 'permission',
          'PostToolUse': 'working', 'PostToolUseFailure': 'working', 'PermissionDenied': 'working',
          'PreInvocation': 'working', 'PostInvocation': 'working', 'PreToolUse': 'working',
          'Stop': 'finished', 'StopFailure': 'error'}


def one_line(text, limit=DETAIL):
    text = ' '.join(str(text or '').split())
    return text if len(text) <= limit else text[:limit - 1].rstrip() + '…'


def read_json(path):
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def search_path():
    local_bin = str(Path.home() / '.local/bin')
    current = os.environ.get('PATH') or '/usr/local/bin:/usr/bin:/bin'
    parts = current.split(':')
    return current if local_bin in parts else f'{local_bin}:{current}'


def configured_agent():
    env = os.environ.get('DESKTOP_AI_AGENT', '').strip()
    if env:
        return env
    configured = read_json(CONFIG).get('aiAgent')
    return configured.strip() if isinstance(configured, str) else ''


def known_agent_for(token):
    lowered = token.lower()
    target = ALIASES.get(lowered, lowered)
    for agent_id, name, commands in AGENTS:
        if target == agent_id or lowered in commands:
            return agent_id, name, commands
    return None


def resolve_agent(spec=None):
    raw = configured_agent() if spec is None else str(spec).strip()
    path = search_path()
    if not raw:
        for agent_id, name, commands in AGENTS:
            for candidate in commands:
                found = shutil.which(candidate, path=path)
                if found:
                    return {'available': True, 'agent': agent_id, 'name': name, 'command': [found]}
        return {'available': False, 'agent': '', 'name': '', 'command': []}

    try:
        argv = shlex.split(raw)
    except ValueError:
        argv = [raw]
    if not argv:
        return resolve_agent('')

    head, tail = argv[0], argv[1:]
    base = Path(head).name
    known = known_agent_for(base)
    if known:
        agent_id, name, commands = known
        if '/' in head:
            found = shutil.which(head, path=path)
            return {'available': bool(found), 'agent': agent_id, 'name': name, 'command': [found or head, *tail]}
        candidates = [base] + [c for c in commands if c != base] if base in commands else list(commands)
        for candidate in candidates:
            found = shutil.which(candidate, path=path)
            if found:
                return {'available': True, 'agent': agent_id, 'name': name, 'command': [found, *tail]}
        return {'available': False, 'agent': agent_id, 'name': name, 'command': [commands[0], *tail]}

    found = shutil.which(head, path=path)
    display = re.sub(r'[-_]+', ' ', Path(base).stem).strip().title() or base
    return {'available': bool(found), 'agent': base.lower(), 'name': display, 'command': [found or head, *tail]}


def claude_settings(language=None):
    chosen = (language or os.environ.get('DESKTOP_AI_LANGUAGE', '').strip() or tr('assistant.language')).strip()
    command = 'python3 ' + json.dumps(str(Path(__file__).resolve()))

    def entry(asynchronous=True, matcher=None):
        item = {'hooks': [dict({'type': 'command', 'command': command + ' hook', 'timeout': 5},
                               **({'async': True} if asynchronous else {}))]}
        return [dict(item, matcher=matcher) if matcher else item]

    hooks = {name: entry() for name in ('SessionStart', 'UserPromptSubmit', 'PermissionRequest', 'PostToolUse',
                                        'PostToolUseFailure', 'PermissionDenied', 'Stop', 'StopFailure')}
    hooks.update(Notification=entry(matcher='permission_prompt'), SessionEnd=entry(asynchronous=False))
    return json.dumps({
        'voice': {'enabled': True, 'mode': 'hold'},
        'language': chosen,
        'statusLine': {'type': 'command', 'command': command + ' statusline', 'padding': 0},
        'disableAllHooks': False,
        'hooks': hooks,
    })


def configured_directory():
    env = os.environ.get('DESKTOP_AI_DIRECTORY', '').strip()
    if env:
        return env
    configured = read_json(CONFIG).get('aiDirectory')
    return configured.strip() if isinstance(configured, str) else ''


def resolve_directory(explicit=None, repo_fallback=None):
    for candidate in (explicit, configured_directory()):
        if isinstance(candidate, str) and candidate.strip():
            expanded = Path(os.path.expanduser(candidate.strip()))
            if expanded.is_dir():
                return str(expanded)
    if repo_fallback:
        fallback = Path(repo_fallback)
        if fallback.is_dir():
            return str(fallback)
    return str(Path.home())


def installed_agents():
    path = search_path()
    found = []
    for agent_id, name, commands in AGENTS:
        if any(shutil.which(cmd, path=path) for cmd in commands):
            found.append({'agent': agent_id, 'name': name})
    return found


def antigravity_statusline_command():
    return f'python3 {shlex.quote(str(Path(__file__).resolve()))} statusline'


def antigravity_statusline_state(base_dir=None):
    """Inspect Antigravity's ~/.gemini/antigravity-cli/settings.json statusLine block without touching other agents."""
    settings = read_json((base_dir or AGY_DIR) / 'settings.json')
    sl = settings.get('statusLine') if isinstance(settings.get('statusLine'), dict) else {}
    cmd = str(sl.get('command') or '').strip()
    ours = 'agent.py' in cmd and 'statusline' in cmd
    enabled = bool(ours and sl.get('enabled', True) is not False and sl.get('type') in ('command', '', None))
    return {'enabled': enabled, 'custom': bool(cmd and not ours)}


def set_antigravity_statusline(enable, base_dir=None):
    """Enable or remove the desktop statusline hook in Antigravity's settings.json, preserving all user keys."""
    target_dir = base_dir or AGY_DIR
    path = target_dir / 'settings.json'
    settings = read_json(path)
    if enable:
        settings['statusLine'] = {
            'type': 'command',
            'command': antigravity_statusline_command(),
            'padding': 0,
            'enabled': True,
        }
    else:
        sl = settings.get('statusLine') if isinstance(settings.get('statusLine'), dict) else {}
        cmd = str(sl.get('command') or '').strip()
        if 'agent.py' in cmd and 'statusline' in cmd:
            settings['statusLine'] = {'type': '', 'command': '', 'enabled': True}
    target_dir.mkdir(parents=True, exist_ok=True)
    write_atomic(path, json.dumps(settings, indent=2, ensure_ascii=False) + '\n')
    return antigravity_statusline_state(target_dir)


def probe_info(spec=None, agy_dir=None):
    info = dict(resolve_agent(spec))
    installed = installed_agents()
    agy_sl = antigravity_statusline_state(agy_dir)
    info.update(
        installed=[item['agent'] for item in installed],
        autoAgent=installed[0]['agent'] if installed else '',
        autoName=installed[0]['name'] if installed else '',
        agyStatusline=agy_sl['enabled'],
        agyStatuslineCustom=agy_sl['custom'],
    )
    return info


def launch_info(spec=None, directory=None, repo_fallback=None):
    info = resolve_agent(spec)
    if info['available'] and info['agent'] == 'claude' and '--settings' not in info['command']:
        info = dict(info, command=[*info['command'], '--settings', claude_settings()])
    info = dict(info, directory=resolve_directory(directory, repo_fallback))
    return info


def format_image_arg(image_path, agent_id=None):
    """Format an image path for typing into the active harness prompt (@path for Antigravity/Gemini, plain path else)."""
    chosen = (agent_id or '').strip().lower()
    if not chosen:
        session_data = read_json(SESSION)
        chosen = str(session_data.get('agent') or '').strip().lower()
    if not chosen:
        chosen = str(resolve_agent().get('agent') or '').strip().lower()
    prefix = '@' if chosen in IMAGE_AT_AGENTS else ''
    return f'{prefix}{image_path} '


def active_window_cwd(root_pid):
    """Find the working directory of the foreground shell/editor process inside a Hyprland window PID."""
    try:
        root_pid = int(root_pid)
    except (TypeError, ValueError):
        return ''
    if root_pid <= 0:
        return ''
    proc = Path('/proc')
    if not proc.is_dir():
        return ''
    uid = os.getuid()
    children_map = {}
    for entry in proc.iterdir():
        if not entry.name.isdigit():
            continue
        pid = int(entry.name)
        try:
            if entry.stat().st_uid != uid:
                continue
            stat_text = (entry / 'stat').read_text(encoding='utf-8', errors='ignore')
            rparen = stat_text.rfind(')')
            if rparen != -1:
                fields = stat_text[rparen + 2:].split()
                if len(fields) >= 2 and fields[1].isdigit():
                    children_map.setdefault(int(fields[1]), []).append(pid)
        except OSError:
            continue
    # Depth-first walk: prefer the deepest child process that has a readable directory cwd.
    best_cwd = ''
    best_depth = -1
    stack = [(root_pid, 0)]
    visited = set()
    while stack:
        pid, depth = stack.pop()
        if pid in visited:
            continue
        visited.add(pid)
        try:
            cwd = os.readlink(f'/proc/{pid}/cwd')
            if Path(cwd).is_dir() and depth >= best_depth:
                best_cwd = cwd
                best_depth = depth
        except OSError:
            pass
        for child in children_map.get(pid, ()):
            stack.append((child, depth + 1))
    return best_cwd


def unquote_arg(value):
    if not isinstance(value, str):
        return str(value or '')
    text = value.strip()
    if len(text) >= 2 and text[0] == '"' and text[-1] == '"':
        try:
            loaded = json.loads(text)
            if isinstance(loaded, str):
                return loaded
        except ValueError:
            return text[1:-1]
    return text


# What the permission or active tool is for: the command, the file, or the tool name.
def tool_detail(event):
    if isinstance(event.get('toolCall'), dict):
        call = event['toolCall']
        tool = call.get('name') or ''
        args = call.get('args') if isinstance(call.get('args'), dict) else {}
        target = (unquote_arg(args.get('toolSummary')) or unquote_arg(args.get('CommandLine'))
                  or unquote_arg(args.get('Path')) or unquote_arg(args.get('query')))
        return one_line(f'{tool}: {target}' if target else tool)
    tool = event.get('tool_name') or ''
    data = event.get('tool_input') if isinstance(event.get('tool_input'), dict) else {}
    target = data.get('command') or data.get('file_path') or data.get('url') or data.get('pattern') or ''
    return one_line(f'{tool}: {target}' if target else tool)


def state_for(event, current):
    name = event.get('hook_event_name')
    if name == 'Notification':
        # The permission prompt has waited a few seconds; PermissionRequest usually came first.
        if event.get('notification_type') == 'permission_prompt' and current.get('state') != 'permission':
            return 'permission', one_line(event.get('message'))
        return None
    state = STATES.get(name)
    if state is None:
        return None
    if name == 'PermissionRequest':
        return state, tool_detail(event)
    if name == 'PreToolUse':
        return state, tool_detail(event)
    if name in ('PostToolUse', 'PostToolUseFailure', 'PermissionDenied', 'PostInvocation'):
        # Tools of a subagent or after a permission: still working, the reply is not done.
        return state, ''
    if name == 'Stop':
        if event.get('terminationReason') == 'ERROR':
            return 'error', one_line(event.get('error'))
        if event.get('terminationReason') == 'USER_CANCELED':
            return 'ready', ''
        return state, one_line(event.get('last_assistant_message'))
    if name == 'StopFailure':
        return state, one_line(event.get('error'))
    return state, ''


def write_state(session, state, detail='', at=None, agent_id='claude', name=''):
    at = time.time_ns() if at is None else at
    RUNTIME.mkdir(parents=True, exist_ok=True)
    with (RUNTIME / '.agent.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        current = read_json(STATE)
        if current.get('at', 0) > at:
            return
        same = current.get('state') == state and current.get('session') == (session or '')
        since = current.get('since') if same else None
        payload = {
            'agent': agent_id,
            'name': name or AGENT_NAMES.get(agent_id, ''),
            'session': session or '',
            'state': state,
            'detail': detail,
            'since': since or round(at / 1e9, 3),
            'at': at,
        }
        write_atomic(STATE, json.dumps(payload, ensure_ascii=False) + '\n')


def clear_state(session=None):
    if not RUNTIME.exists():
        return
    with (RUNTIME / '.agent.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        current = read_json(STATE)
        if session is None or current.get('session') in (None, '', session):
            STATE.unlink(missing_ok=True)


def hook(event, at):
    agent_id = 'antigravity' if 'conversationId' in event else 'claude'
    session = event.get('session_id') or event.get('conversationId') or ''
    if event.get('hook_event_name') == 'SessionEnd':
        RUNTIME.mkdir(parents=True, exist_ok=True)
        with (RUNTIME / '.agent.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            current = read_json(STATE)
            if current.get('at', 0) <= at and current.get('session') in (None, session):
                STATE.unlink(missing_ok=True)
        return
    RUNTIME.mkdir(parents=True, exist_ok=True)
    # Hooks run async and in parallel (subagents too): the newest event wins, by the time it started.
    with (RUNTIME / '.agent.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        current = read_json(STATE)
        if current.get('at', 0) > at:
            return
        result = state_for(event, current)
        if result is None:
            return
        state, detail = result
        same = current.get('state') == state and current.get('session') == session
        since = current.get('since') if same else None
        payload = {
            'agent': agent_id,
            'name': AGENT_NAMES.get(agent_id, ''),
            'session': session,
            'state': state,
            'detail': detail,
            'since': since or round(at / 1e9, 3),
            'at': at,
        }
        write_atomic(STATE, json.dumps(payload, ensure_ascii=False) + '\n')


def tier():
    account = read_json(ACCOUNT).get('oauthAccount')
    account = account if isinstance(account, dict) else {}
    return account.get('organizationRateLimitTier') or account.get('organizationType') or ''


def window(limits, name):
    data = limits.get(name) if isinstance(limits, dict) else None
    if not isinstance(data, dict) or not isinstance(data.get('used_percentage'), (int, float)):
        return None
    reset = data.get('resets_at')
    return {'used': round(float(data['used_percentage']), 1), 'resets': reset if isinstance(reset, (int, float)) else None}


def parse_iso_seconds(value):
    if isinstance(value, (int, float)):
        return float(value)
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return datetime.fromisoformat(value.strip().replace('Z', '+00:00')).timestamp()
    except ValueError:
        return None


def quota_buckets(quota, now):
    if not isinstance(quota, dict):
        return None
    source = quota.get('buckets') if isinstance(quota.get('buckets'), (dict, list)) else quota
    items = source.items() if isinstance(source, dict) else enumerate(source)
    buckets = []
    for key, entry in items:
        if not isinstance(entry, dict) or entry.get('disabled'):
            continue
        used = None
        if isinstance(entry.get('used_percentage'), (int, float)):
            used = float(entry['used_percentage'])
        elif isinstance(entry.get('remaining_fraction'), (int, float)):
            used = (1.0 - float(entry['remaining_fraction'])) * 100.0
        elif entry.get('reset_time') or isinstance(entry.get('reset_in_seconds'), (int, float)):
            # Go protojson/encoding-json omits remaining_fraction: 0.0 when a bucket is exhausted.
            used = 100.0
        if used is None:
            continue
        resets = parse_iso_seconds(entry.get('reset_time'))
        if resets is None and isinstance(entry.get('reset_in_seconds'), (int, float)):
            resets = now + float(entry['reset_in_seconds'])
        label = entry.get('display_name') or entry.get('name') or (str(key) if isinstance(key, str) else '')
        buckets.append({'label': label, 'used': round(max(0.0, min(100.0, used)), 1), 'resets': resets})
    return buckets


def is_antigravity_statusline(data):
    return any(key in data for key in ('quota', 'agent_state', 'plan_tier', 'tool_confirmation_pending')) or (
        str(data.get('product') or '').lower() == 'antigravity'
    )


def statusline(data):
    previous = read_json(USAGE)
    now = round(time.time(), 3)
    agy = is_antigravity_statusline(data)
    agent_id = 'antigravity' if agy else 'claude'
    same_agent = previous.get('agent') in (None, '', agent_id) if agent_id == 'claude' else previous.get('agent') == agent_id
    prior = previous if same_agent else {}

    model = data.get('model') if isinstance(data.get('model'), dict) else {}
    model_name = model.get('display_name') or model.get('id') or (data.get('model') if isinstance(data.get('model'), str) else '') or ''
    if agy and model.get('effort') and f"({model['effort']})" not in model_name.lower():
        effort = str(model['effort']).capitalize()
        if effort not in model_name:
            model_name = f'{model_name} ({effort})' if model_name else effort
    context = data.get('context_window') if isinstance(data.get('context_window'), dict) else {}
    usage = {
        'agent': agent_id,
        'model': model_name,
        'context': context.get('used_percentage') if isinstance(context.get('used_percentage'), (int, float)) else None,
        'tier': (data.get('plan_tier') or prior.get('tier', '')) if agy else (tier() or prior.get('tier', '')),
        'statuslineUpdated': now,
        'updated': now,
    }
    if agy:
        buckets = quota_buckets(data.get('quota'), now)
        if buckets is not None:
            usage.update(fiveHour=None, sevenDay=None, buckets=buckets, limitsUpdated=now if buckets else None)
        else:
            usage.update(fiveHour=None, sevenDay=None, buckets=prior.get('buckets') or [], limitsUpdated=prior.get('limitsUpdated'))
    elif isinstance(data.get('rate_limits'), dict):
        # Limits arrive only after the first reply of a session: until then the last ones stay, with their time.
        usage.update(fiveHour=window(data['rate_limits'], 'five_hour'), sevenDay=window(data['rate_limits'], 'seven_day'),
                     limitsUpdated=now)
    else:
        usage.update({key: prior.get(key) for key in ('fiveHour', 'sevenDay', 'limitsUpdated')})

    write_atomic(USAGE, json.dumps(usage, ensure_ascii=False) + '\n')
    parts = [usage['model']] if usage['model'] else []
    if usage['context'] is not None:
        parts.append(tr('assistant.statusLine.context', [round(usage['context'])]))
    for key, label in (('fiveHour', '5h'), ('sevenDay', '7d')):
        if usage.get(key):
            parts.append(f'{label} {round(usage[key]["used"])}%')
    for bucket in usage.get('buckets') or []:
        prefix = f"{bucket['label']} " if bucket.get('label') else ''
        parts.append(f"{prefix}{round(bucket['used'])}%")
    return ' · '.join(parts)


def write_usage(agent_id, model='', context=None, plan_tier='', buckets=None):
    previous = read_json(USAGE)
    same_agent = previous.get('agent') == agent_id
    prior = previous if same_agent else {}
    now = round(time.time(), 3)
    sl_at = prior.get('statuslineUpdated')
    sl_fresh = isinstance(sl_at, (int, float)) and (now - sl_at) < 120.0
    resolved_context = round(float(context), 1) if isinstance(context, (int, float)) else None
    if sl_fresh and buckets is None:
        resolved_model = prior.get('model') or model or ''
        if prior.get('context') is not None:
            resolved_context = prior.get('context')
    else:
        resolved_model = model or prior.get('model') or ''
    usage = {
        'agent': agent_id,
        'model': resolved_model,
        'context': resolved_context,
        'tier': plan_tier or prior.get('tier') or '',
        'fiveHour': None,
        'sevenDay': None,
        'buckets': buckets if buckets is not None else (prior.get('buckets') or []),
        'limitsUpdated': now if buckets else prior.get('limitsUpdated'),
        'statuslineUpdated': sl_at if same_agent and isinstance(sl_at, (int, float)) else None,
        'updated': now,
    }
    write_atomic(USAGE, json.dumps(usage, ensure_ascii=False) + '\n')


def console_session_info():
    """Return (start_time, descendant_pids) of the desktop-ai Kitty window when readable in /proc."""
    uid = os.getuid()
    kitty_pids = []
    children_map = {}
    proc = Path('/proc')
    if not proc.is_dir():
        return time.time() - 2.0, set()
    for entry in proc.iterdir():
        if not entry.name.isdigit():
            continue
        pid = int(entry.name)
        try:
            st = entry.stat()
            if st.st_uid != uid:
                continue
            cmdline = (entry / 'cmdline').read_bytes().split(b'\x00')
            if b'desktop-ai' in cmdline and any(b'kitty' in part for part in cmdline[:2]):
                kitty_pids.append((pid, st.st_mtime))
            stat_text = (entry / 'stat').read_text(encoding='utf-8', errors='ignore')
            rparen = stat_text.rfind(')')
            if rparen != -1:
                fields = stat_text[rparen + 2:].split()
                if len(fields) >= 2 and fields[1].isdigit():
                    children_map.setdefault(int(fields[1]), []).append(pid)
        except OSError:
            continue
    if not kitty_pids:
        return time.time() - 2.0, set()
    root_pid, started = min(kitty_pids, key=lambda item: item[1])
    descendants = set()
    stack = [root_pid]
    while stack:
        current = stack.pop()
        if current in descendants:
            continue
        descendants.add(current)
        stack.extend(children_map.get(current, ()))
    return started - 2.0, descendants


def context_limit_for(model_name, configured_window=None):
    if isinstance(configured_window, (int, float)) and configured_window > 0:
        return int(configured_window)
    if isinstance(configured_window, str):
        lowered = configured_window.strip().lower()
        if lowered.endswith('k') and lowered[:-1].isdigit():
            return int(lowered[:-1]) * 1000
        if lowered.endswith('m') and lowered[:-1].isdigit():
            return int(lowered[:-1]) * 1_000_000
    if 'claude' in (model_name or '').lower():
        return 200_000
    return 1_000_000


class AntigravityTailer:
    """Incremental reader for Antigravity settings.json and brain/<id>/.system_generated/logs/transcript.jsonl."""

    MODEL_CHANGE = re.compile(r'`Model Selection`.*? to ([^.\n<]+)')

    def __init__(self, base_dir=None, started=0.0):
        self.base_dir = base_dir or AGY_DIR
        self.started = started
        self.transcript = None
        self.offset = 0
        self.settings_mtime = None
        self.settings = {}
        self.model = ''
        self.context = None
        self.kind = 'ready'
        self.detail = ''
        self.pending = None

    def refresh_settings(self):
        path = self.base_dir / 'settings.json'
        try:
            mtime = path.stat().st_mtime_ns
        except OSError:
            return
        if mtime == self.settings_mtime:
            return
        self.settings_mtime = mtime
        self.settings = read_json(path)
        configured = self.settings.get('model')
        if isinstance(configured, str) and configured.strip():
            self.model = configured.strip()

    def find_transcript(self, pids=()):
        brain = self.base_dir / 'brain'
        if not brain.is_dir():
            return None
        for pid in pids:
            fd_dir = Path(f'/proc/{pid}/fd')
            try:
                for fd in fd_dir.iterdir():
                    target = str(os.readlink(fd))
                    if '/brain/' in target:
                        conv = target.split('/brain/', 1)[1].split('/', 1)[0]
                        candidate = brain / conv / '.system_generated/logs/transcript.jsonl'
                        if candidate.is_file():
                            return candidate
            except OSError:
                continue
        newest = None
        newest_mtime = self.started
        try:
            for conv_dir in brain.iterdir():
                candidate = conv_dir / '.system_generated/logs/transcript.jsonl'
                try:
                    mtime = candidate.stat().st_mtime
                except OSError:
                    continue
                if mtime >= newest_mtime:
                    newest_mtime = mtime
                    newest = candidate
        except OSError:
            return None
        return newest

    def switch_transcript(self, path):
        self.transcript = path
        self.offset = 0
        self.context = None
        self.kind = 'ready'
        self.detail = ''
        self.pending = None

    def confirm_mode(self, call):
        name = call.get('name') or ''
        args = call.get('args') if isinstance(call.get('args'), dict) else {}
        if name == 'ask_question':
            return 'immediate'
        if name == 'run_command' and unquote_arg(args.get('BypassSandbox')).lower() == 'true':
            return 'immediate'
        if self.settings.get('toolPermission') in ('ask', 'always-ask'):
            return 'delayed'
        if name in ('edit_file', 'write_file') and self.settings.get('agentMode') in (None, '', 'default', 'request-review'):
            return 'delayed'
        return None

    def apply_step(self, step, initial=False, now=None):
        now = time.time() if now is None else now
        step_type = step.get('type')
        status = step.get('status')
        content = step.get('content') if isinstance(step.get('content'), str) else ''

        if step_type == 'USER_INPUT':
            match = self.MODEL_CHANGE.search(content)
            if match:
                self.model = match.group(1).strip()
            if step.get('source') == 'USER_EXPLICIT':
                self.kind = 'working'
                self.detail = ''
                self.pending = None
            return

        if step_type == 'PLANNER_RESPONSE':
            tokens = sum(int(step.get(k) or 0) for k in ('input_tokens', 'cache_read_tokens', 'output_tokens')
                         if isinstance(step.get(k), (int, float)))
            if tokens > 0:
                limit = context_limit_for(self.model, self.settings.get('contextWindow'))
                self.context = round(min(100.0, tokens * 100.0 / limit), 1)
            calls = step.get('tool_calls') if isinstance(step.get('tool_calls'), list) else []
            if status == 'ERROR':
                self.kind = 'ready' if initial else 'error'
                self.detail = '' if initial else one_line(step.get('error') or content)
                self.pending = None
            elif calls:
                first = calls[0] if isinstance(calls[0], dict) else {}
                detail = tool_detail({'toolCall': first})
                confirm = None
                for call in calls:
                    if isinstance(call, dict):
                        mode = self.confirm_mode(call)
                        if mode == 'immediate':
                            confirm = 'immediate'
                            detail = tool_detail({'toolCall': call})
                            break
                        confirm = confirm or mode
                at = parse_iso_seconds(step.get('created_at')) or now
                self.kind = 'tool'
                self.detail = detail
                self.pending = {'detail': detail, 'confirm': confirm, 'at': at}
            elif status == 'DONE':
                if initial and (now - (parse_iso_seconds(step.get('created_at')) or 0)) > 3.0:
                    self.kind = 'ready'
                    self.detail = ''
                else:
                    self.kind = 'finished'
                    self.detail = one_line(content)
                self.pending = None
            return

        if step_type == 'GENERIC':
            self.kind = 'working'
            self.pending = None
            return

        if step_type == 'SYSTEM_MESSAGE' and 'priority=MESSAGE_PRIORITY_HIGH' in content:
            self.kind = 'working'
            self.pending = None

    def watch_paths(self):
        paths = [self.base_dir, self.base_dir / 'brain']
        if self.transcript is not None:
            paths.extend([self.transcript.parent, self.transcript])
        else:
            brain = self.base_dir / 'brain'
            if brain.is_dir():
                try:
                    for conv_dir in brain.iterdir():
                        logs = conv_dir / '.system_generated/logs'
                        if logs.is_dir():
                            paths.append(logs)
                except OSError:
                    pass
        return [p for p in paths if p.exists()]

    def next_timeout(self, now=None):
        now = time.time() if now is None else now
        if self.kind == 'tool' and self.pending and self.pending['confirm'] == 'delayed':
            elapsed = now - self.pending['at']
            if elapsed < 1.5:
                return max(0.05, 1.5 - elapsed)
        return 1.0 if self.transcript is None else None

    def poll(self, pids=(), now=None):
        now = time.time() if now is None else now
        self.refresh_settings()
        candidate = self.find_transcript(pids)
        initial = False
        if candidate is not None and candidate != self.transcript:
            self.switch_transcript(candidate)
            initial = True
        if self.transcript is not None:
            try:
                size = self.transcript.stat().st_size
                if size < self.offset:
                    self.offset = 0
                if size > self.offset:
                    with self.transcript.open('rb') as handle:
                        handle.seek(self.offset)
                        chunk = handle.read()
                        self.offset = handle.tell()
                    lines = chunk.splitlines()
                    for raw_line in lines:
                        try:
                            step = json.loads(raw_line.decode('utf-8', errors='replace'))
                        except ValueError:
                            continue
                        if isinstance(step, dict):
                            self.apply_step(step, initial=initial, now=now)
            except OSError:
                pass

        if self.kind == 'tool' and self.pending:
            mode = self.pending['confirm']
            if mode == 'immediate' or (mode == 'delayed' and now - self.pending['at'] >= 1.5):
                return 'permission', self.pending['detail'], self.model, self.context
            return 'working', self.pending['detail'], self.model, self.context
        return self.kind, self.detail, self.model, self.context


class CodexTailer:
    """Incremental reader for Codex ~/.codex/config.toml and ~/.codex/sessions rollout JSONL files."""

    MODEL_RE = re.compile(r'^\s*model\s*=\s*["\']([^"\']+)["\']', re.M)

    def __init__(self, base_dir=None, started=0.0):
        self.base_dir = base_dir or CODEX_DIR
        self.started = started
        self.rollout = None
        self.offset = 0
        self.model = ''
        self.context = None
        self.state = 'ready'
        self.detail = ''
        self.last_reply = ''

    def refresh_config(self):
        try:
            text = (self.base_dir / 'config.toml').read_text(encoding='utf-8')
        except OSError:
            return
        match = self.MODEL_RE.search(text)
        if match and not self.model:
            self.model = match.group(1).strip()

    def find_rollout(self):
        sessions = self.base_dir / 'sessions'
        if not sessions.is_dir():
            return None
        newest = None
        newest_mtime = self.started
        for path in sessions.rglob('rollout-*.jsonl'):
            try:
                mtime = path.stat().st_mtime
            except OSError:
                continue
            if mtime >= newest_mtime:
                newest_mtime = mtime
                newest = path
        return newest

    def apply_record(self, record, initial=False):
        rtype = record.get('type')
        payload = record.get('payload') if isinstance(record.get('payload'), dict) else {}
        if rtype in ('session_meta', 'turn_context') and isinstance(payload.get('model'), str):
            self.model = payload['model']
        elif rtype == 'event_msg':
            mtype = payload.get('type')
            if mtype in ('user_message', 'task_started'):
                self.state = 'working'
                self.detail = ''
            elif mtype in ('exec_approval_request', 'apply_patch_approval_request'):
                cmd = payload.get('command')
                if isinstance(cmd, list):
                    cmd = ' '.join(str(part) for part in cmd)
                self.state = 'permission'
                self.detail = one_line(cmd or payload.get('reason') or '')
            elif mtype == 'token_count':
                info = payload.get('info') if isinstance(payload.get('info'), dict) else {}
                usage = info.get('last_token_usage') if isinstance(info.get('last_token_usage'), dict) else {}
                total = usage.get('total_tokens') or info.get('total_tokens')
                window_size = info.get('model_context_window') or 200_000
                if isinstance(total, (int, float)) and isinstance(window_size, (int, float)) and window_size > 0:
                    self.context = round(min(100.0, float(total) * 100.0 / float(window_size)), 1)
            elif mtype == 'agent_message':
                self.last_reply = payload.get('message') or ''
            elif mtype == 'task_complete':
                self.state = 'ready' if initial else 'finished'
                self.detail = '' if initial else one_line(payload.get('last_agent_message') or self.last_reply)
            elif mtype in ('error', 'stream_error'):
                self.state = 'ready' if initial else 'error'
                self.detail = '' if initial else one_line(payload.get('message'))

    def watch_paths(self):
        sessions = self.base_dir / 'sessions'
        paths = [self.base_dir, sessions]
        if self.rollout is not None:
            paths.extend([self.rollout.parent, self.rollout])
        elif sessions.is_dir():
            today = datetime.now()
            paths.extend([
                sessions / f'{today.year:04d}',
                sessions / f'{today.year:04d}/{today.month:02d}',
                sessions / f'{today.year:04d}/{today.month:02d}/{today.day:02d}',
            ])
        return [p for p in paths if p.exists()]

    def next_timeout(self, _now=None):
        return 1.5 if self.rollout is None else None

    def poll(self, _pids=(), _now=None):
        self.refresh_config()
        candidate = self.find_rollout()
        initial = False
        if candidate is not None and candidate != self.rollout:
            self.rollout = candidate
            self.offset = 0
            initial = True
        if self.rollout is not None:
            try:
                size = self.rollout.stat().st_size
                if size > self.offset:
                    with self.rollout.open('rb') as handle:
                        handle.seek(self.offset)
                        chunk = handle.read()
                        self.offset = handle.tell()
                    lines = chunk.splitlines()
                    for raw_line in lines:
                        try:
                            record = json.loads(raw_line.decode('utf-8', errors='replace'))
                        except ValueError:
                            continue
                        if isinstance(record, dict):
                            self.apply_record(record, initial=initial)
            except OSError:
                pass
        return self.state, self.detail, self.model, self.context


class GeminiTailer:
    """Reader for Gemini CLI ~/.gemini/settings.json and ~/.gemini/tmp/*/chats/session-*.json."""

    def __init__(self, base_dir=None, started=0.0):
        self.base_dir = base_dir or GEMINI_DIR
        self.started = started
        self.session_file = None
        self.mtime = None
        self.model = ''
        self.context = None
        self.state = 'ready'
        self.detail = ''

    def refresh_settings(self):
        settings = read_json(self.base_dir / 'settings.json')
        model = settings.get('model')
        if isinstance(model, dict) and isinstance(model.get('name'), str):
            self.model = self.model or model['name']
        elif isinstance(model, str) and model.strip():
            self.model = self.model or model.strip()

    def find_session(self):
        tmp = self.base_dir / 'tmp'
        if not tmp.is_dir():
            return None
        newest = None
        newest_mtime = self.started
        for path in tmp.glob('*/chats/session-*.json'):
            try:
                mtime = path.stat().st_mtime
            except OSError:
                continue
            if mtime >= newest_mtime:
                newest_mtime = mtime
                newest = path
        return newest

    def watch_paths(self):
        tmp = self.base_dir / 'tmp'
        paths = [self.base_dir, tmp]
        if self.session_file is not None:
            paths.extend([self.session_file.parent, self.session_file])
        elif tmp.is_dir():
            try:
                for sub in tmp.iterdir():
                    chats = sub / 'chats'
                    if chats.is_dir():
                        paths.append(chats)
            except OSError:
                pass
        return [p for p in paths if p.exists()]

    def next_timeout(self, _now=None):
        return 1.5 if self.session_file is None else None

    def poll(self, _pids=(), _now=None):
        self.refresh_settings()
        candidate = self.find_session()
        initial = False
        if candidate is not None and candidate != self.session_file:
            self.session_file = candidate
            self.mtime = None
            initial = True
        if self.session_file is not None:
            try:
                mtime = self.session_file.stat().st_mtime_ns
            except OSError:
                mtime = None
            if mtime is not None and mtime != self.mtime:
                self.mtime = mtime
                data = read_json(self.session_file)
                messages = data.get('messages') if isinstance(data.get('messages'), list) else []
                for message in messages:
                    if not isinstance(message, dict):
                        continue
                    if isinstance(message.get('model'), str) and message['model']:
                        self.model = message['model']
                    tokens = message.get('tokens') if isinstance(message.get('tokens'), dict) else {}
                    if isinstance(tokens.get('total'), (int, float)) and tokens['total'] > 0:
                        self.context = round(min(100.0, float(tokens['total']) * 100.0 / 1_000_000), 1)
                if messages and isinstance(messages[-1], dict):
                    last = messages[-1]
                    mtype = last.get('type')
                    if mtype == 'user':
                        self.state, self.detail = 'working', ''
                    elif mtype == 'error':
                        self.state = 'ready' if initial else 'error'
                        self.detail = '' if initial else one_line(last.get('content'))
                    elif mtype == 'gemini':
                        calls = last.get('toolCalls') if isinstance(last.get('toolCalls'), list) else []
                        asking = next((c for c in calls if isinstance(c, dict) and c.get('status') in ('awaiting_approval', 'confirming')), None)
                        running = next((c for c in calls if isinstance(c, dict) and c.get('status') in ('executing', 'scheduled', 'pending')), None)
                        if asking:
                            self.state, self.detail = 'permission', one_line(asking.get('name'))
                        elif running:
                            self.state, self.detail = 'working', one_line(running.get('name'))
                        else:
                            self.state = 'ready' if initial else 'finished'
                            self.detail = '' if initial else one_line(last.get('content'))
        return self.state, self.detail, self.model, self.context


class InotifyWatcher:
    """Zero-idle-CPU Linux inotify wait helper with a self-pipe for clean signal wakeup."""

    MASK = 0x0000058e  # IN_MODIFY | IN_ATTRIB | IN_CLOSE_WRITE | IN_MOVED_TO | IN_CREATE | IN_DELETE_SELF

    def __init__(self):
        self.rfd, self.wfd = os.pipe()
        os.set_blocking(self.rfd, False)
        os.set_blocking(self.wfd, False)
        self.stopped = False
        self.poller = select.poll()
        self.poller.register(self.rfd, select.POLLIN)
        self.ifd = -1
        self.libc = None
        self.watches = {}
        try:
            libc = ctypes.CDLL('libc.so.6', use_errno=True)
            ifd = libc.inotify_init1(os.O_NONBLOCK | os.O_CLOEXEC)
            if ifd >= 0:
                self.libc = libc
                self.ifd = ifd
                self.poller.register(ifd, select.POLLIN)
        except OSError:
            pass

    @property
    def has_inotify(self):
        return self.ifd >= 0

    def wake(self):
        self.stopped = True
        try:
            os.write(self.wfd, b'\x01')
        except OSError:
            pass

    def sync(self, paths):
        if self.ifd < 0:
            return
        wanted = {str(p) for p in paths}
        for existing in list(self.watches):
            if existing not in wanted:
                wd = self.watches.pop(existing)
                self.libc.inotify_rm_watch(self.ifd, wd)
        for path in wanted:
            if path not in self.watches:
                wd = self.libc.inotify_add_watch(self.ifd, os.fsencode(path), self.MASK)
                if wd >= 0:
                    self.watches[path] = wd

    def wait(self, timeout=None):
        if self.stopped:
            return
        ms = None if timeout is None else max(20, int(timeout * 1000))
        try:
            events = self.poller.poll(ms)
        except InterruptedError:
            return
        for fd, _ in events:
            if fd == self.ifd:
                while True:
                    try:
                        if not os.read(self.ifd, 8192):
                            break
                    except BlockingIOError:
                        break
                    except OSError:
                        break

    def close(self):
        for fd in (self.ifd, self.rfd, self.wfd):
            if fd >= 0:
                try:
                    os.close(fd)
                except OSError:
                    pass


def watch(agent_id):
    info = resolve_agent(agent_id)
    canonical = info['agent'] or agent_id or 'assistant'
    display = info['name'] or AGENT_NAMES.get(canonical, canonical.title())
    session = f'{canonical}-{os.getpid()}'
    waiter = InotifyWatcher()

    def handle_stop(_signum, _frame):
        waiter.wake()

    signal.signal(signal.SIGTERM, handle_stop)
    signal.signal(signal.SIGINT, handle_stop)

    started, pids = console_session_info()
    tailers = {
        'antigravity': AntigravityTailer,
        'codex': CodexTailer,
        'gemini': GeminiTailer,
    }
    tailer = tailers[canonical](started=started) if canonical in tailers else None
    last_state = None
    last_usage = None

    try:
        if tailer is None:
            write_state(session, 'ready', '', agent_id=canonical, name=display)
            write_usage(canonical)
            while not waiter.stopped:
                waiter.wait(None)
            return 0

        while not waiter.stopped:
            if not pids:
                _, pids = console_session_info()
            now = time.time()
            state, detail, model, context = tailer.poll(pids, now=now)
            if (state, detail) != last_state:
                write_state(session, state, detail, agent_id=canonical, name=display)
                last_state = (state, detail)
            if (model, context) != last_usage:
                write_usage(canonical, model=model, context=context)
                last_usage = (model, context)
            if waiter.has_inotify:
                waiter.sync(tailer.watch_paths())
                waiter.wait(tailer.next_timeout(now))
            else:
                fallback = 0.5 if state in ('working', 'permission') else 2.5
                extra = tailer.next_timeout(now)
                waiter.wait(min(fallback, extra) if extra is not None else fallback)
    finally:
        waiter.close()
        SESSION.unlink(missing_ok=True)
        clear_state(session)
    return 0


def main():
    at = time.time_ns()
    command = sys.argv[1:2]
    if command == ['probe']:
        print(json.dumps(probe_info(), ensure_ascii=False))
        return 0
    if command == ['launch']:
        explicit_dir = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] else None
        repo_dir = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] else None
        print(json.dumps(launch_info(directory=explicit_dir, repo_fallback=repo_dir), ensure_ascii=False))
        return 0
    if command == ['agy-statusline']:
        action = sys.argv[2] if len(sys.argv) > 2 else 'status'
        if action == 'on':
            print(json.dumps(set_antigravity_statusline(True), ensure_ascii=False))
            return 0
        if action == 'off':
            print(json.dumps(set_antigravity_statusline(False), ensure_ascii=False))
            return 0
        print(json.dumps(antigravity_statusline_state(), ensure_ascii=False))
        return 0
    if command == ['image-arg']:
        image_path = sys.argv[2] if len(sys.argv) > 2 else ''
        agent_override = sys.argv[3] if len(sys.argv) > 3 else None
        sys.stdout.write(format_image_arg(image_path, agent_override))
        return 0
    if command == ['cwd']:
        pid = sys.argv[2] if len(sys.argv) > 2 else ''
        sys.stdout.write(active_window_cwd(pid))
        return 0
    if command == ['watch']:
        target = sys.argv[2] if len(sys.argv) > 2 else ''
        return watch(target)
    try:
        data = json.load(sys.stdin)
    except ValueError:
        data = {}
    data = data if isinstance(data, dict) else {}
    if command == ['hook']:
        # Whatever goes wrong here must not reach Claude Code (see the module docstring).
        try:
            hook(data, at)
        except Exception:
            pass
        return 0
    if command == ['statusline']:
        try:
            print(statusline(data))
        except OSError as error:
            print(error, file=sys.stderr)
        return 0
    print(tr('assistant.errors.usage'), file=sys.stderr)
    return 2


if __name__ == '__main__':
    sys.exit(main())
