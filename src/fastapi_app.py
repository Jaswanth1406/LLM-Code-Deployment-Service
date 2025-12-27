from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Any
import threading
from src import server

app = FastAPI()

# Mount the static directory so the UI is available when running under uvicorn
BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", include_in_schema=False)
async def root():
    # Serve the static single-page app index
    return FileResponse(str(STATIC_DIR / "index.html"))


from fastapi.responses import JSONResponse, HTMLResponse


@app.get("/health")
async def health():
    status = {"ok": True}
    # check github token presence/validity
    try:
        user = server.get_authenticated_user()
        status["github_user"] = user
        status["github_token_valid"] = True
    except Exception:
        status["github_token_valid"] = False
    return JSONResponse(status)


class Attachment(BaseModel):
    name: str
    url: str


class TaskRequest(BaseModel):
    email: str = Field(..., example="student@example.com")
    secret: str = Field(..., example="mysharedsecret")
    task: str = Field(..., example="demo-task")
    round: int = Field(..., example=1)
    nonce: str = Field(..., example="n1")
    brief: str = Field(..., example="Create a single page showing Hello")
    checks: List[Any] = Field(default_factory=list)
    evaluation_url: str = Field(..., example="http://127.0.0.1:9000/eval")
    attachments: List[Attachment] = Field(default_factory=list)
    wait_for_result: bool = Field(False, example=False)


@app.post("/api-endpoint")
async def api_endpoint(body: TaskRequest):
    data = body.dict()

    # Basic validation copied from Flask server (Pydantic ensures types)
    required = ["email", "secret", "task", "round", "nonce", "brief", "evaluation_url"]
    for k in required:
        if k not in data or data.get(k) is None:
            raise HTTPException(status_code=400, detail={"error": f"missing {k}"})

    if server.SHARED_SECRET and data.get("secret") != server.SHARED_SECRET:
        raise HTTPException(status_code=403, detail={"error": "invalid secret"})

    # If caller requested synchronous result, run build and return evaluator payload
    if data.get("wait_for_result"):
        try:
            payload, eval_payload = server.build_repo_payload(data)
            # kick off notifier in background but don't wait for it here
            notify_thread = threading.Thread(target=server.notify_evaluation, args=(data["evaluation_url"], eval_payload))
            notify_thread.daemon = True
            notify_thread.start()
            return eval_payload
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # start background work using the same handler
    thread = threading.Thread(target=server.handle_build, args=(data,))
    thread.daemon = True
    thread.start()

    return {"status": "accepted"}


@app.get("/result")
async def get_result(email: str, task: str, nonce: str = None):
    """Query the server for the build result matching email/task[/nonce]."""
    try:
        res = server.get_result(email, task, nonce)
        if not res:
            return {"status": "pending"}
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
