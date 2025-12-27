import os
import json
import tempfile
import threading
from flask import Flask, request, jsonify
from .generator import generate_app
from .github_helper import create_repo_from_dir
from .notifier import notify_evaluation
from .github_helper import clone_repo_to_dir, commit_and_push, get_authenticated_user
import sys

# Optional startup check: if set to true, require a valid GitHub token at startup
REQUIRE_GITHUB_TOKEN_ON_STARTUP = os.environ.get("REQUIRE_GITHUB_TOKEN_ON_STARTUP", "false").lower() in ("1", "true", "yes")
if REQUIRE_GITHUB_TOKEN_ON_STARTUP:
    try:
        user = get_authenticated_user()
        print(f"GitHub token validated for user: {user}")
    except Exception as e:
        print("GITHUB token validation failed at startup:", e)
        sys.exit(1)
else:
    # Try a non-fatal check so logs show helpful info when token missing
    try:
        user = get_authenticated_user()
        print(f"GitHub token present for user: {user}")
    except Exception:
        print("GitHub token not validated at startup (set REQUIRE_GITHUB_TOKEN_ON_STARTUP=1 to fail fast)")
import subprocess

app = Flask(__name__, static_folder='../static', static_url_path='/static')


@app.route('/')
def index():
    return app.send_static_file('index.html')

SHARED_SECRET = os.environ.get("secret") 


@app.route("/api-endpoint", methods=["POST"])
def api_endpoint():
    body = request.get_json(force=True)
    # Basic validation
    required = ["email", "secret", "task", "round", "nonce", "brief", "evaluation_url"]
    for k in required:
        if k not in body:
            return jsonify({"error": f"missing {k}"}), 400

    if SHARED_SECRET and body.get("secret") != SHARED_SECRET:
        return jsonify({"error": "invalid secret"}), 403

    # If client requests to wait for the result (useful for testing), run build synchronously
    wait = bool(body.get("wait_for_result", False))
    if wait:
        try:
            payload, eval_payload = build_repo_payload(body)
            # store for polling
            try:
                key = f"{payload.get('email')}:{payload.get('task')}:{payload.get('nonce')}"
                RESULTS[key] = eval_payload
            except Exception:
                pass
            # kick off notifier in background but do not wait for it here
            notify_thread = threading.Thread(target=notify_evaluation, args=(body["evaluation_url"], eval_payload))
            notify_thread.daemon = True
            notify_thread.start()
            return jsonify(eval_payload), 200
        except Exception as e:
            app.logger.exception("synchronous build failed")
            return jsonify({"error": str(e)}), 500

    # immediate response for async mode
    resp = {"status": "accepted"}
    thread = threading.Thread(target=handle_build, args=(body,))
    thread.daemon = True
    thread.start()

    return jsonify(resp), 200


# In-memory store for last results. Key: "email:task:nonce" -> payload
RESULTS = {}


def handle_build(body):
    # Delegate to build_repo_payload and then notify
    try:
        payload, eval_payload = build_repo_payload(body)
        # store payload for UI polling
        key = f"{payload.get('email')}:{payload.get('task')}:{payload.get('nonce')}"
        RESULTS[key] = eval_payload
        notify_evaluation(body["evaluation_url"], eval_payload)
    except Exception:
        app.logger.exception("build failed")


def build_repo_payload(body):
    """Build the repo (create or update) and return the evaluation payload dict.

    This function performs the same operations as the previous handle_build but returns
    the payload instead of notifying. It does not block on notification.
    """
    # Create temp dir for repo source
    with tempfile.TemporaryDirectory() as tmpdir:
        task_name = body["task"]
        round_num = int(body.get("round", 1))

        if round_num == 1:
            # Generate app into tmpdir
            generate_app(body, tmpdir)

            # Create github repo and push
            repo_url, commit_sha, pages_url = create_repo_from_dir(tmpdir, task_name)
        else:
            # Round 2: attempt to update existing repo
            owner = get_authenticated_user()
            repo_name = task_name.replace(' ', '-').lower()
            try:
                # clone repo into tmpdir
                clone_repo_to_dir(owner, repo_name, tmpdir)
                # regenerate (this will overwrite files)
                generate_app(body, tmpdir)
                # commit and push
                commit_and_push(tmpdir, message=f"Round {round_num} update")
                # get new sha
                commit_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=tmpdir).decode().strip()
                repo_url = f"https://github.com/{owner}/{repo_name}"
                pages_url = f"https://{owner}.github.io/{repo_name}/"
            except Exception:
                # fallback: create a new repo if update failed
                generate_app(body, tmpdir)
                repo_url, commit_sha, pages_url = create_repo_from_dir(tmpdir, task_name)

        payload = {
            "email": body["email"],
            "task": body["task"],
            "round": body["round"],
            "nonce": body["nonce"],
            "repo_url": repo_url,
            "commit_sha": commit_sha,
            "pages_url": pages_url,
        }

        # evaluator-style payload (what graders expect)
        eval_payload = {
            "commit_sha": commit_sha,
            "message": "App built and deployed successfully",
            "pages_url": pages_url,
            "repo_url": repo_url,
            "round": body["round"],
            "task": body["task"],
        }

        # store result so UI can poll for it (store evaluator payload)
        try:
            key = f"{payload.get('email')}:{payload.get('task')}:{payload.get('nonce')}"
            RESULTS[key] = eval_payload
        except Exception:
            pass
        return payload, eval_payload


def get_result(email, task, nonce=None):
    """Return stored payload for the given identifiers or None."""
    if nonce:
        key = f"{email}:{task}:{nonce}"
        return RESULTS.get(key)
    # if nonce not provided, try to find most recent matching task/email
    prefix = f"{email}:{task}:"
    # find last inserted matching key
    for k in reversed(list(RESULTS.keys())):
        if k.startswith(prefix):
            return RESULTS.get(k)
    return None


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
