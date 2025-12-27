import os
import tempfile
import subprocess
import json
from pathlib import Path
import logging
import requests

logger = logging.getLogger(__name__)

GITHUB_OWNER = os.environ.get("GITHUB_OWNER")


def _get_token():
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN required. Set it in the environment or in a .env file.")
    return token


def _run(cmd, cwd=None):
    subprocess.check_call(cmd, cwd=cwd)


def create_repo_from_dir(source_dir, task_name):
    """Create a GitHub repo, push the source, enable Pages, and return (repo_url, commit_sha, pages_url).

    This function uses the REST API to create a repo under the authenticated user or under GITHUB_OWNER.
    It then pushes the local source using git commands.
    """
    GITHUB_TOKEN = _get_token()

    # Build remote repo name safe
    repo_name = task_name.replace(' ', '-').lower()

    # Create repo via API (or detect if already exists)
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github+json"}
    payload = {"name": repo_name, "private": False, "auto_init": False}
    if GITHUB_OWNER:
        create_url = f"https://api.github.com/orgs/{GITHUB_OWNER}/repos"
    else:
        create_url = "https://api.github.com/user/repos"

    repo = None
    repo_url = None
    try:
        r = requests.post(create_url, headers=headers, json=payload)
        r.raise_for_status()
        repo = r.json()
        repo_url = repo.get("html_url")
    except requests.HTTPError as e:
        # If repo already exists (HTTP 422), continue and treat as update
        resp = e.response
        if resp is not None and resp.status_code == 422:
            # repository exists — compute owner/login
            if GITHUB_OWNER:
                owner_login = GITHUB_OWNER
            else:
                owner_login = _get_authenticated_user(headers)
            # Construct repo JSON minimal shape
            repo = {
                'owner': {'login': owner_login},
                'name': repo_name,
                'html_url': f"https://github.com/{owner_login}/{repo_name}",
                'clone_url': f"https://github.com/{owner_login}/{repo_name}.git",
                'ssh_url': f"git@github.com:{owner_login}/{repo_name}.git",
            }
            repo_url = repo['html_url']
        else:
            # Log response body for easier diagnosis (403/401 often include a message)
            try:
                body = resp.text if resp is not None else '<no response>'
            except Exception:
                body = '<could not read response body>'
            logger.error("GitHub repo creation failed: %s %s", resp.status_code if resp is not None else 'N/A', body)
            raise

    # Log which authenticated user the token belongs to and which owner will be used
    try:
        token_user = _get_authenticated_user(headers)
    except Exception:
        token_user = None
    logger.info("Authenticated token user: %s, target owner env: %s", token_user, GITHUB_OWNER)

    # Init git, commit, push
    _run(["git", "init"], cwd=source_dir)
    _run(["git", "add", "-A"], cwd=source_dir)
    _run(["git", "-c", "user.name=student", "-c", "user.email=student@example.com", "commit", "-m", "Initial commit"], cwd=source_dir)
    _run(["git", "branch", "-M", "main"], cwd=source_dir)

    # Use HTTPS push with token; construct remote URL that includes token only for push
    owner = repo['owner']['login']
    https_url = repo.get('clone_url')
    if GITHUB_TOKEN and https_url:
        # insert token into https url: https://<token>@github.com/owner/repo.git
        token_url = https_url.replace('https://', f'https://{GITHUB_TOKEN}@')
        # If origin already exists (possible when reusing temp dirs), set-url instead of add
        try:
            existing = subprocess.check_output(["git", "remote"], cwd=source_dir).decode().split()
        except Exception:
            existing = []

        if 'origin' in existing:
            logger.info("Remote 'origin' exists, setting URL to token-authenticated HTTPS URL")
            _run(["git", "remote", "set-url", "origin", token_url], cwd=source_dir)
        else:
            _run(["git", "remote", "add", "origin", token_url], cwd=source_dir)

        # Try normal push; if it fails due to non-fast-forward or auth, try force push
        try:
            _run(["git", "push", "-u", "origin", "main"], cwd=source_dir)
        except Exception:
            logger.warning("Normal push failed, attempting force push")
            try:
                _run(["git", "push", "-u", "origin", "main", "--force"], cwd=source_dir)
            except Exception as e:
                logger.error("Force push also failed: %s", e)
                raise
        # replace remote to remove token (set back to non-token https)
        _run(["git", "remote", "set-url", "origin", https_url], cwd=source_dir)
    else:
        # fallback to ssh url
        _run(["git", "remote", "add", "origin", repo["ssh_url"]], cwd=source_dir)
        try:
            _run(["git", "push", "-u", "origin", "main"], cwd=source_dir)
        except Exception:
            _run(["git", "push", "-u", "origin", "main", "--force"], cwd=source_dir)

    # Get latest commit sha
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source_dir).decode().strip()

    # Enable GitHub Pages via API (use main branch / root) and wait for availability
    pages_url = f"https://{repo['owner']['login']}.github.io/{repo_name}/"
    enable_pages_and_wait(repo['owner']['login'], repo_name, headers, pages_url)

    return repo_url, sha, pages_url


def _get_authenticated_user(headers):
    """Return the login of the authenticated user."""
    r = requests.get('https://api.github.com/user', headers=headers)
    r.raise_for_status()
    return r.json().get('login')


def get_authenticated_user():
    token = _get_token()
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}
    return _get_authenticated_user(headers)


def clone_repo_to_dir(owner, repo_name, dest_dir):
    """Clone an existing repo into dest_dir using token-authenticated HTTPS clone.

    Returns the https_url used (without token).
    """
    token = _get_token()
    https_url = f"https://github.com/{owner}/{repo_name}.git"
    token_url = https_url.replace('https://', f'https://{token}@')
    _run(["git", "clone", token_url, dest_dir])
    # remove token from remote
    _run(["git", "remote", "set-url", "origin", https_url], cwd=dest_dir)
    return https_url


def commit_and_push(dest_dir, message="Update commit"):
    # stage changes
    _run(["git", "add", "-A"], cwd=dest_dir)
    # commit if there are changes
    try:
        _run(["git", "-c", "user.name=student", "-c", "user.email=student@example.com", "commit", "-m", message], cwd=dest_dir)
    except Exception:
        # no changes to commit
        pass
    # push (try normal, then force if necessary)
    try:
        # attempt push using whatever remote is set
        _run(["git", "push", "origin", "main"], cwd=dest_dir)
    except Exception:
        logger.warning("Push failed, attempting token-authenticated push")
        # try to push using token-authenticated URL in case origin points to SSH/other account
        try:
            token = _get_token()
            # get origin https url
            try:
                https_url = subprocess.check_output(["git", "config", "--get", "remote.origin.url"], cwd=dest_dir).decode().strip()
            except Exception:
                https_url = None

            if https_url and https_url.startswith('https://'):
                token_url = https_url.replace('https://', f'https://{token}@')
                _run(["git", "remote", "set-url", "origin", token_url], cwd=dest_dir)
                try:
                    _run(["git", "push", "origin", "main", "--force"], cwd=dest_dir)
                finally:
                    # restore non-token url
                    if https_url:
                        _run(["git", "remote", "set-url", "origin", https_url], cwd=dest_dir)
            else:
                # no https origin to rewrite; re-raise original error
                raise
        except Exception:
            # final fallback: force push with existing remote
            _run(["git", "push", "origin", "main", "--force"], cwd=dest_dir)


def enable_pages_and_wait(owner, repo_name, headers, pages_url, timeout_seconds=300, poll_interval=5):
    """Enable GitHub Pages for repository and poll pages_url until it returns HTTP 200 or timeout.

    Returns True if pages_url returned 200 within timeout, otherwise False.
    """
    pages_api = f"https://api.github.com/repos/{owner}/{repo_name}/pages"
    pages_payload = {"source": {"branch": "main", "path": "/"}}

    try:
        r = requests.post(pages_api, headers=headers, json=pages_payload)
        # Accept 201, 202 or 204 depending on API; continue to poll regardless
        r.raise_for_status()
    except Exception:
        # non-fatal here; sometimes API responds slowly or with 422 if already configured
        pass

    import time
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            pr = requests.get(pages_url, timeout=5)
            if pr.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(poll_interval)

    return False
