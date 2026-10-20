"""Bounded planner/executor/verifier coordination with persisted stopping conditions."""

from .browser import Browser
from .core import Error, collect, digest, verify_evidence
from .state import Store


def baseline_action(context):
    """Simpler literal-match/BFS baseline, deliberately no model inference."""
    snapshot = context["snapshot"]
    found = {e["criterion"] for e in context["evidence"]}
    choices = []
    for c in context["criteria"]:
        if c["id"] not in found:
            for p in snapshot["passages"]:
                if c["contains"].casefold() in p["text"].casefold():
                    choices.append({"criterion": c["id"], "passage": p["id"]})
                    break
    if choices:
        return {"action": "collect", "selections": choices}
    if all(c["id"] in found for c in context["criteria"]):
        return {"action": "finish"}
    for link in context["frontier"]:
        if link["url"] not in context["visited"]:
            return {"action": "visit", "link": link["id"]}
    return {"action": "finish"}


def _context(task, state):
    # IDs refer to a persisted navigation frontier; fresh snapshots never supply arbitrary URLs.
    frontier = state.get("frontier", [])
    found = {e["criterion"] for e in state["evidence"]}
    options = [
        {"criterion": criterion["id"], "passage": passage["id"]}
        for criterion in task.criteria
        if criterion["id"] not in found
        for passage in state["current"]["passages"]
        if criterion["contains"].casefold() in passage["text"].casefold()
    ]
    remaining = [c for c in task.criteria if c["id"] not in found]
    actions = []
    if options:
        actions.append({"action": "collect", "selections": options[:8]})
    if remaining:
        actions.extend(
            {"action": "visit", "link": link["id"]}
            for link in frontier
            if link["url"] not in state["visited"]
        )
    if not actions:
        actions.append({"action": "finish"})
    return {
        "objective": task.objective,
        "criteria": list(task.criteria),
        "snapshot": state["current"],
        "evidence": state["evidence"],
        "visited": state["visited"],
        "frontier": frontier,
        "remaining_steps": task.max_steps - state["steps"],
        "collect_options": options,
        "remaining_criteria": remaining,
        "action_options": [{"id": f"a{i}", "action": action} for i, action in enumerate(actions)],
    }


def _remember(state, snapshot):
    state["current"] = snapshot
    if snapshot["url"] not in state["visited"]:
        state["visited"].append(snapshot["url"])
    frontier = state.setdefault("frontier", [])
    for link in snapshot["links"]:
        if not any(item["url"] == link["url"] for item in frontier):
            frontier.append(dict(link, id=f"l{len(frontier)}"))
    # Planner must select frontier IDs, not page-local IDs.
    snapshot["links"] = [
        item for item in frontier if item["url"] in {p["url"] for p in snapshot["links"]}
    ]


def _ask(task, state, store, model, role, context):
    if state["calls"] >= task.max_calls:
        raise Error("Cumulative model-call budget exhausted")
    state["calls"] += 1
    store.save(state, {"type": "model_call_started", "role": role, "call": state["calls"]})
    before = dict(model.usage)
    result = model.ask(role, context)
    for k in state["model_usage"]:
        state["model_usage"][k] += model.usage[k] - before[k]
    store.save(state, {"type": "model_response", "role": role, "response": result})
    return result


def run(task, checkpoint, *, model=None, pause_after=None):
    if pause_after is not None and (type(pause_after) is not int or pause_after < 1):
        raise Error("pause_after must be a positive integer")
    with Store(checkpoint, task) as store:
        state = store.load()
        mode = "model" if model else "baseline"
        if state.get("mode", mode) != mode:
            raise Error("Resume must use the original planner mode")
        state["mode"] = mode
        if state["status"] not in {"running", "paused", "verifying"}:
            return state
        state["status"] = "running" if state["status"] == "paused" else state["status"]
        executed = 0
        try:
            with Browser(task) as browser:
                # Always refresh after resumption; stale IDs cannot operate a changed page.
                url = state["current"]["url"] if state["current"] else task.start_url
                _remember(state, browser.read(url))
                store.save(state, {"type": "observation", "snapshot": state["current"]})
                while state["status"] == "running":
                    if state["steps"] >= task.max_steps:
                        state["status"] = "incomplete"
                        state["reason"] = "Cumulative step budget exhausted"
                        break
                    context = _context(task, state)
                    action = (
                        _ask(task, state, store, model, "planner", context)
                        if model
                        else baseline_action(context)
                    )
                    if isinstance(action, dict) and set(action) == {"choice"}:
                        choices = {item["id"]: item["action"] for item in context["action_options"]}
                        choice = action["choice"]
                        if not isinstance(choice, str) or choice not in choices:
                            raise Error("Unknown planner action choice")
                        action = choices[choice]
                    if not isinstance(action, dict) or not isinstance(action.get("action"), str):
                        raise Error("Planner returned an invalid action")
                    state["steps"] += 1
                    state["pending"] = action
                    store.save(state, {"type": "action_started", "action": action})
                    name = action["action"]
                    if name in {"submit", "purchase", "fill", "click", "write"}:
                        state["status"] = "needs_approval"
                        request = {
                            "task": task.fingerprint,
                            "action": action,
                            "execution_supported": False,
                        }
                        state["approval_request"] = dict(
                            request,
                            digest=digest(request),
                            notice="No external write occurred. Write execution is not implemented; approval alone cannot execute it.",
                        )
                    elif name == "visit" and set(action) == {"action", "link"}:
                        links = {item["id"]: item["url"] for item in state.get("frontier", [])}
                        link = action["link"]
                        if not isinstance(link, str) or link not in links:
                            raise Error("Unknown navigation link ID")
                        _remember(state, browser.read(links[link]))
                    elif name == "collect" and set(action) == {"action", "selections"}:
                        evidence = collect(task, state["current"], action["selections"])
                        for e in evidence:
                            if e not in state["evidence"]:
                                state["evidence"].append(e)
                        if len(state["evidence"]) > 64:
                            raise Error("Evidence budget exhausted")
                    elif name == "finish" and set(action) == {"action"}:
                        state["status"] = "verifying"
                    else:
                        raise Error("Unsupported or malformed planner action")
                    state["pending"] = None
                    store.save(
                        state,
                        {
                            "type": "action_completed",
                            "action": action,
                            "snapshot": state["current"] if name == "visit" else None,
                        },
                    )
                    executed += 1
                    if pause_after and executed >= pause_after and state["status"] == "running":
                        state["status"] = "paused"
                        break
            if state["status"] == "verifying":
                # Deliberately separate browser context; no planner conclusions in this check.
                with Browser(task) as verifier_browser:
                    fresh = {
                        u: verifier_browser.read(u)
                        for u in sorted({e["url"] for e in state["evidence"]})
                    }
                verification = verify_evidence(task, state["evidence"], fresh)
                verification["fresh_sources"] = fresh
                state["verification"] = verification
                if model and verification["passed"]:
                    verdict = _ask(
                        task,
                        state,
                        store,
                        model,
                        "verifier",
                        {
                            "objective": task.objective,
                            "criteria": list(task.criteria),
                            "checks": verification["checks"],
                        },
                    )
                    if (
                        set(verdict) != {"accepted", "reason"}
                        or type(verdict["accepted"]) is not bool
                        or not isinstance(verdict["reason"], str)
                        or len(verdict["reason"]) > 1000
                    ):
                        raise Error("Invalid independent verifier response")
                    verification["model_review"] = verdict
                    verification["passed"] = verification["passed"] and verdict["accepted"]
                state["status"] = "verified" if verification["passed"] else "incomplete"
                state["reason"] = (
                    "All literal criteria rechecked"
                    if verification["passed"]
                    else "Fresh evidence or semantic review did not satisfy the task"
                )
        except Error as exc:
            state["status"] = "failed"
            state["reason"] = str(exc)
        store.save(
            state, {"type": "stopped", "status": state["status"], "reason": state.get("reason")}
        )
        return state
