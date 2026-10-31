"""ADK session persistence using stdlib SQLite, without async database extras.

Intended for a single application instance. State is session-scoped; this suite
does not use ADK app:/user: shared state. Optimistic revisions reject stale writes.
"""

import sqlite3
import time
import uuid
from contextlib import closing
from pathlib import Path

from google.adk.sessions.base_session_service import BaseSessionService, ListSessionsResponse
from google.adk.sessions.session import Session


class SQLiteSessionService(BaseSessionService):
    def __init__(self, path: Path):
        self.path = str(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as conn, conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS sessions (
                app TEXT NOT NULL, user_id TEXT NOT NULL, id TEXT NOT NULL,
                body TEXT NOT NULL, revision TEXT NOT NULL,
                PRIMARY KEY(app, user_id, id))""")

    def _connect(self):
        return sqlite3.connect(self.path, timeout=30)

    async def create_session(self, *, app_name, user_id, state=None, session_id=None):
        session = Session(
            id=session_id or str(uuid.uuid4()),
            app_name=app_name,
            user_id=user_id,
            state=state or {},
            last_update_time=time.time(),
        )
        revision = str(uuid.uuid4())
        with closing(self._connect()) as conn, conn:
            conn.execute(
                "INSERT INTO sessions VALUES (?, ?, ?, ?, ?)",
                (app_name, user_id, session.id, session.model_dump_json(), revision),
            )
        session._storage_update_marker = revision
        return session

    async def get_session(self, *, app_name, user_id, session_id, config=None):
        with closing(self._connect()) as conn:
            row = conn.execute(
                "SELECT body, revision FROM sessions WHERE app=? AND user_id=? AND id=?",
                (app_name, user_id, session_id),
            ).fetchone()
        if row is None:
            return None
        session = Session.model_validate_json(row[0])
        session._storage_update_marker = row[1]
        if config:
            if config.after_timestamp is not None:
                session.events = [
                    event for event in session.events if event.timestamp >= config.after_timestamp
                ]
            if config.num_recent_events is not None:
                count = config.num_recent_events
                session.events = session.events[-count:] if count > 0 else []
        return session

    async def list_sessions(self, *, app_name, user_id=None):
        with closing(self._connect()) as conn:
            rows = conn.execute(
                "SELECT body FROM sessions WHERE app=?"
                + (" AND user_id=?" if user_id is not None else ""),
                (app_name, user_id) if user_id is not None else (app_name,),
            ).fetchall()
        sessions = [Session.model_validate_json(row[0]) for row in rows]
        for session in sessions:
            session.state = {}
            session.events = []
        return ListSessionsResponse(sessions=sessions)

    async def delete_session(self, *, app_name, user_id, session_id):
        with closing(self._connect()) as conn, conn:
            conn.execute(
                "DELETE FROM sessions WHERE app=? AND user_id=? AND id=?",
                (app_name, user_id, session_id),
            )

    async def append_event(self, session, event):
        if event.partial:
            return event
        # Read full stored history so callers using GetSessionConfig cannot erase it.
        stored = await self.get_session(
            app_name=session.app_name, user_id=session.user_id, session_id=session.id
        )
        if stored is None or stored._storage_update_marker != session._storage_update_marker:
            raise ValueError("Session changed during this run; reload before retrying")
        if any(existing.id == event.id for existing in stored.events):
            return event
        event = await super().append_event(session, event)
        stored.events.append(event)
        stored.state = {
            key: value for key, value in session.state.items() if not key.startswith("temp:")
        }
        stored.last_update_time = time.time()
        revision = str(uuid.uuid4())
        with closing(self._connect()) as conn, conn:
            changed = conn.execute(
                "UPDATE sessions SET body=?, revision=? WHERE app=? AND user_id=? AND id=? AND revision=?",
                (
                    stored.model_dump_json(),
                    revision,
                    session.app_name,
                    session.user_id,
                    session.id,
                    session._storage_update_marker,
                ),
            )
            if changed.rowcount != 1:
                raise ValueError("Concurrent session update rejected")
        session._storage_update_marker = revision
        session.last_update_time = stored.last_update_time
        return event

    async def close(self):
        pass  # Every operation owns and closes its connection.
