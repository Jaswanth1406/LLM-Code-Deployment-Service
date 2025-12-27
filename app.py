"""Entrypoint for hosting on Hugging Face Spaces or other platforms.

This imports the Flask app from `src.server` and runs it. Hugging Face Spaces
will run `python app.py` by default for generic Python apps.
"""
import os

from src import server


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    # Use 0.0.0.0 so it's reachable in containerized envs
    server.app.run(host="0.0.0.0", port=port)
