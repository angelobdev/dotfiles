#!/usr/bin/env python3
"""Claude Code hooks and status line for the desktop assistant (desktop-ai passes them with --settings).

hook: one hook event on stdin -> the assistant state in $XDG_RUNTIME_DIR/desktop-shell/agent.json, which
services/Agent.qml watches. It never prints and always exits 0: Claude Code adds the output of some hooks
to the conversation, and exit code 2 changes what it does (keeps working after Stop, denies a permission).
statusline: the status line JSON on stdin -> ~/.local/state/desktop-shell/agent-usage.json (the 5-hour and
7-day limits, model, context) and one line for the terminal.
"""
from common import write_atomic
from i18n import tr
import fcntl
import json
import os
from pathlib import Path
import sys
import time

RUNTIME = Path(os.environ.get('XDG_RUNTIME_DIR') or f'/run/user/{os.getuid()}') / 'desktop-shell'
STATE = RUNTIME / 'agent.json'
USAGE = Path(os.environ.get('XDG_STATE_HOME') or Path.home() / '.local/state') / 'desktop-shell/agent-usage.json'
ACCOUNT = Path.home() / '.claude.json'
DETAIL = 160
# Hook event -> state; Notification and the tool events depend on their payload (see state_for).
STATES = {'SessionStart': 'ready', 'UserPromptSubmit': 'working', 'PermissionRequest': 'permission',
          'PostToolUse': 'working', 'PostToolUseFailure': 'working', 'PermissionDenied': 'working',
          'Stop': 'finished', 'StopFailure': 'error'}


def one_line(text, limit=DETAIL):
    text = ' '.join(str(text or '').split())
    return text if len(text) <= limit else text[:limit - 1].rstrip() + '…'


# What the permission is for: the command, the file, or the tool name.
def tool_detail(event):
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
    if name in ('PostToolUse', 'PostToolUseFailure', 'PermissionDenied'):
        # Tools of a subagent or of Claude after a permission: still working, the reply is not done.
        return state, ''
    if name == 'Stop':
        return state, one_line(event.get('last_assistant_message'))
    if name == 'StopFailure':
        return state, one_line(event.get('error'))
    return state, ''


def read_json(path):
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def hook(event, at):
    RUNTIME.mkdir(parents=True, exist_ok=True)
    # Hooks run async and in parallel (subagents too): the newest event wins, by the time it started.
    with (RUNTIME / '.agent.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        current = read_json(STATE)
        if current.get('at', 0) > at:
            return
        if event.get('hook_event_name') == 'SessionEnd':
            if current.get('session') in (None, event.get('session_id')):
                STATE.unlink(missing_ok=True)
            return
        result = state_for(event, current)
        if result is None:
            return
        state, detail = result
        same = current.get('state') == state and current.get('session') == event.get('session_id')
        since = current.get('since') if same else None
        write_atomic(STATE, json.dumps({'session': event.get('session_id') or '', 'state': state, 'detail': detail,
                                        'since': since or round(at / 1e9, 3), 'at': at}, ensure_ascii=False) + '\n')


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


def statusline(data):
    previous = read_json(USAGE)
    model = data.get('model') if isinstance(data.get('model'), dict) else {}
    context = data.get('context_window') if isinstance(data.get('context_window'), dict) else {}
    usage = {
        'model': model.get('display_name') or model.get('id') or '',
        'context': context.get('used_percentage') if isinstance(context.get('used_percentage'), (int, float)) else None,
        'tier': tier() or previous.get('tier', ''),
        'updated': round(time.time(), 3),
    }
    # Limits arrive only after the first reply of a session: until then the last ones stay, with their time.
    if isinstance(data.get('rate_limits'), dict):
        usage.update(fiveHour=window(data['rate_limits'], 'five_hour'), sevenDay=window(data['rate_limits'], 'seven_day'),
                     limitsUpdated=usage['updated'])
    else:
        usage.update({key: previous.get(key) for key in ('fiveHour', 'sevenDay', 'limitsUpdated')})
    write_atomic(USAGE, json.dumps(usage, ensure_ascii=False) + '\n')
    parts = [usage['model']] if usage['model'] else []
    if usage['context'] is not None:
        parts.append(tr('assistant.statusLine.context', [round(usage['context'])]))
    for key, label in (('fiveHour', '5h'), ('sevenDay', '7d')):
        if usage.get(key):
            parts.append(f'{label} {round(usage[key]["used"])}%')
    return ' · '.join(parts)


def main():
    at = time.time_ns()
    command = sys.argv[1:2]
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
