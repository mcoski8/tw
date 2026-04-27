"""
Flask app for the Taiwanese Poker trainer.

Run:
    cd taiwanese
    python3 trainer/app.py

Then open http://localhost:5000 in a browser.
"""
from __future__ import annotations

import sys
from dataclasses import asdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from flask import Flask, jsonify, request, send_from_directory  # noqa: E402

from trainer.src.buyout_eval import evaluate_buyout  # noqa: E402
from trainer.src.dealer import deal_hand  # noqa: E402
from trainer.src.engine import (  # noqa: E402
    DEFAULT_PROFILE_ID,
    PROFILE_BY_ID,
    PROFILES,
    evaluate_all_profiles,
    evaluate_hand_profile,
    find_setting_index,
)
from trainer.src.explain import build_feedback  # noqa: E402


app = Flask(__name__, static_folder=str(HERE / "static"), static_url_path="")

SAMPLES = 1000
SEED = 0xC0FFEE


def _resolve_profile(profile_id: str | None):
    pid = profile_id or DEFAULT_PROFILE_ID
    if pid not in PROFILE_BY_ID:
        return None, f"unknown profile_id: {pid!r}"
    return PROFILE_BY_ID[pid], None


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/profiles", methods=["GET"])
def api_profiles():
    return jsonify({
        "default": DEFAULT_PROFILE_ID,
        "profiles": [
            {"id": p.id, "label": p.label} for p in PROFILES
        ],
    })


@app.route("/api/deal", methods=["GET"])
def api_deal():
    hand = deal_hand()
    return jsonify({"hand": hand})


@app.route("/api/score", methods=["POST"])
def api_score():
    """
    Request body (JSON):
      {
        "hand":  [<7 card strings, same ones from /api/deal>],
        "setting": [top, mid1, mid2, bot1, bot2, bot3, bot4]
                   # the user's placement, order matters: index 0 = top,
                   # indices 1-2 = middle, indices 3-6 = bottom.
      }

    Response (JSON):
      {
        "user": {"ev": <float>, "cards": [...7 strings]},
        "best": {"ev": <float>, "cards": [...7 strings], "setting_index": <int>},
        "delta":    <float, best - user>,
        "severity": "trivial" | "minor" | "moderate" | "major",
        "severity_phrase": "...",
        "is_match": <bool>,
        "summary":  "plain-English one-paragraph",
        "findings": [{"title": "...", "detail": "..."}, ...]
      }
    """
    data = request.get_json(silent=True) or {}
    hand = data.get("hand")
    user_setting = data.get("setting")

    if not isinstance(hand, list) or len(hand) != 7:
        return jsonify({"error": "body.hand must be a 7-card list"}), 400
    if not isinstance(user_setting, list) or len(user_setting) != 7:
        return jsonify({"error": "body.setting must be a 7-card list"}), 400

    if sorted(hand) != sorted(user_setting):
        return jsonify({
            "error": (
                "body.setting cards don't match body.hand cards — every dealt "
                "card must appear exactly once in the placement."
            )
        }), 400

    profile, err = _resolve_profile(data.get("profile_id"))
    if err:
        return jsonify({"error": err}), 400

    try:
        mc = evaluate_hand_profile(hand, profile, samples=SAMPLES, seed=SEED)
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 500
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 500

    try:
        user_idx = find_setting_index(mc, user_setting)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    user_result = mc.settings[user_idx]
    best_result = mc.best()
    is_match = user_result.setting_index == best_result.setting_index

    feedback = build_feedback(
        user_cards=list(user_setting),
        best_cards=list(best_result.cards),
        user_ev=user_result.ev,
        best_ev=best_result.ev,
        is_match=is_match,
        profile_id=profile.id,
    )

    buyout = evaluate_buyout(list(hand), best_ev=best_result.ev)
    buyout["profile_label"] = profile.label

    return jsonify({
        "user": {
            "ev": user_result.ev,
            "cards": list(user_setting),
            "setting_index": user_result.setting_index,
        },
        "best": {
            "ev": best_result.ev,
            "cards": list(best_result.cards),
            "setting_index": best_result.setting_index,
        },
        "delta": feedback.delta,
        "severity": feedback.severity,
        "severity_phrase": feedback.severity_phrase,
        "is_match": feedback.is_match,
        "summary": feedback.summary,
        "findings": [asdict(f) for f in feedback.findings],
        "profile": {"id": profile.id, "label": profile.label},
        "samples": mc.samples,
        "buyout": buyout,
    })


@app.route("/api/compare", methods=["POST"])
def api_compare():
    """
    Evaluate the user's arrangement against EVERY production profile and
    return a per-profile comparison.

    Request body is the same as /api/score (hand + setting). No profile_id.

    Response:
      {
        "samples": <int>,
        "per_profile": [
          {
            "profile":     {"id": ..., "label": ...},
            "user":        {"ev": ..., "setting_index": ...},
            "best":        {"ev": ..., "cards": [...], "setting_index": ...},
            "delta":       <best_ev - user_ev>,
            "is_match":    <bool>
          }, ...
        ],
        "robustness": {
          "worst_delta": <float>,     # max delta across profiles
          "worst_label": <str>,       # which profile has the worst delta
          "mean_delta":  <float>,
          "matches":     <int>        # # of profiles user exactly matched
        }
      }
    """
    data = request.get_json(silent=True) or {}
    hand = data.get("hand")
    user_setting = data.get("setting")

    if not isinstance(hand, list) or len(hand) != 7:
        return jsonify({"error": "body.hand must be a 7-card list"}), 400
    if not isinstance(user_setting, list) or len(user_setting) != 7:
        return jsonify({"error": "body.setting must be a 7-card list"}), 400
    if sorted(hand) != sorted(user_setting):
        return jsonify({
            "error": (
                "body.setting cards don't match body.hand cards — every dealt "
                "card must appear exactly once in the placement."
            )
        }), 400

    try:
        results = evaluate_all_profiles(hand, samples=SAMPLES, seed=SEED)
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 500
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 500

    per_profile = []
    deltas = []
    matches = 0
    worst_delta = -1e9
    worst_label = ""
    soft_recommend_profiles = []
    best_evs = []
    for profile, mc in results:
        try:
            user_idx = find_setting_index(mc, user_setting)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        user_r = mc.settings[user_idx]
        best_r = mc.best()
        is_match = user_r.setting_index == best_r.setting_index
        delta = best_r.ev - user_r.ev
        if is_match:
            matches += 1
        deltas.append(delta)
        best_evs.append(best_r.ev)
        if delta > worst_delta:
            worst_delta = delta
            worst_label = profile.label
        # Per-profile soft buyout signal: best-EV here is below the buyout cost.
        per_profile_buyout = evaluate_buyout(list(hand), best_ev=best_r.ev)
        if per_profile_buyout["soft_recommend"]:
            soft_recommend_profiles.append(profile.label)
        per_profile.append({
            "profile": {"id": profile.id, "label": profile.label},
            "user": {"ev": user_r.ev, "setting_index": user_r.setting_index},
            "best": {
                "ev": best_r.ev,
                "cards": list(best_r.cards),
                "setting_index": best_r.setting_index,
            },
            "delta": delta,
            "is_match": is_match,
            "buyout_soft": per_profile_buyout["soft_recommend"],
        })

    # Hand-level buyout signature: doesn't depend on opponent. Use the worst
    # best-EV across the panel as the headline expected loss.
    worst_best_ev = min(best_evs) if best_evs else None
    buyout = evaluate_buyout(list(hand), best_ev=worst_best_ev)
    buyout["soft_profiles"] = soft_recommend_profiles

    return jsonify({
        "samples": SAMPLES,
        "per_profile": per_profile,
        "robustness": {
            "worst_delta": worst_delta,
            "worst_label": worst_label,
            "mean_delta":  sum(deltas) / len(deltas),
            "matches":     matches,
        },
        "buyout": buyout,
    })


if __name__ == "__main__":
    # Bind to 127.0.0.1 only — the trainer has no auth and should never be
    # exposed externally. Port 5050 rather than the Flask-default 5000
    # because macOS AirPlay Receiver claims port 5000 and returns a 403
    # "You don't have authorization to view this page" that looks like a
    # Flask permissions error but isn't.
    #
    # use_reloader=True watches Python source files and auto-restarts the
    # server when we edit them — so a trainer session stays in sync with
    # code changes without a manual Ctrl+C dance. Static files (HTML/JS/CSS)
    # are served live and only need a browser refresh.
    import os
    port = int(os.environ.get("TRAINER_PORT", "5050"))
    print(f"Trainer running at http://127.0.0.1:{port}  (auto-reload on .py changes)")
    app.run(host="127.0.0.1", port=port, debug=False, use_reloader=True)
