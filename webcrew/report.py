"""Inert, escaped local report. Never silently overwrite a prior delivery."""

import html
import json
from pathlib import Path

from .core import Error


def export(state, events, directory):
    directory = Path(directory)
    try:
        directory.mkdir(parents=True, exist_ok=False)
        data = {
            "schema": 1,
            "state": state,
            "events": events,
            "limitations": "Rendered text rechecked at observation time; not proof of truth or general task correctness. No external writes were executed.",
        }
        (directory / "report.json").write_text(
            json.dumps(data, ensure_ascii=True, indent=2) + "\n", encoding="utf-8"
        )

        def esc(v):
            return html.escape(str(v), quote=True)

        rows = "".join(
            f"<tr><td>{esc(e['criterion'])}</td><td>{esc(e['text'])}</td><td>{esc(e['url'])}</td><td><code>{esc(e['text_sha256'])}</code></td></tr>"
            for e in state["evidence"]
        )
        content = f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'"><title>WebCrew task evidence</title><style>body{{font:16px system-ui;max-width:1100px;margin:3rem auto;padding:1rem;color:#202820;background:#f6f4ed}}table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #b9c2b7;padding:.7rem;text-align:left;overflow-wrap:anywhere}}code{{font-size:11px}}h1{{font-size:2rem}}</style></head><body><h1>WebCrew task evidence</h1><p>Status: <strong>{esc(state["status"])}</strong> · Steps: {state["steps"]} · Model calls: {state["calls"]}</p><p>{esc(state.get("reason", ""))}</p><table><thead><tr><th>Criterion</th><th>Exact passage</th><th>Source</th><th>Text digest</th></tr></thead><tbody>{rows}</tbody></table><p>{esc(data["limitations"])}</p></body></html>'
        (directory / "report.html").write_text(content, encoding="utf-8")
    except (OSError, UnicodeError):
        raise Error("Cannot create report directory; choose a new writable path") from None
