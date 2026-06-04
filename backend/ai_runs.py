"""AI/SSE 任务生命周期记录工具。"""

import json
from datetime import datetime
from types import SimpleNamespace

from extensions import db
from models import AiRun


def _json_text(payload):
    if payload is None:
        return ''
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def start_ai_run(kind, user_id=None, request_json=None):
    run = AiRun(
        kind=kind,
        user_id=user_id,
        status='pending',
        request_json=_json_text(request_json),
        created_at=datetime.utcnow(),
    )
    db.session.add(run)
    db.session.flush()
    run_id = run.id
    db.session.commit()
    return SimpleNamespace(id=run_id)


def mark_ai_run_running(run_id):
    run = db.session.get(AiRun, run_id)
    if not run:
        return None
    run.status = 'running'
    run.started_at = datetime.utcnow()
    db.session.commit()
    return run


def mark_ai_run_done(run_id, response_json=None):
    run = db.session.get(AiRun, run_id)
    if not run:
        return None
    run.status = 'done'
    run.response_json = _json_text(response_json)
    run.finished_at = datetime.utcnow()
    db.session.commit()
    return run


def mark_ai_run_failed(run_id, error, response_json=None):
    run = db.session.get(AiRun, run_id)
    if not run:
        return None
    run.status = 'failed'
    run.error = str(error or '')[:2000]
    run.response_json = _json_text(response_json)
    run.finished_at = datetime.utcnow()
    db.session.commit()
    return run
