const form = document.getElementById('deploy-form');
const status = document.getElementById('status');
const preview = document.getElementById('preview');

function setStatus(msg){ status.textContent = msg }

form.addEventListener('submit', async (e)=>{
  e.preventDefault();
  setStatus('Submitting...')
  const payload = {
    email: document.getElementById('email').value,
    secret: document.getElementById('secret').value,
    task: document.getElementById('task').value,
    round: Number(document.getElementById('round').value),
    nonce: 'n-' + Math.random().toString(36).slice(2,9),
    brief: document.getElementById('brief').value,
    checks: JSON.parse(document.getElementById('checks').value || '[]'),
    evaluation_url: document.getElementById('evaluation_url').value,
    attachments: JSON.parse(document.getElementById('attachments').value || '[]'),
    wait_for_result: document.getElementById('wait_for_result').checked
  }

  try{
    const res = await fetch('/api-endpoint',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)})
    const data = await res.json()
    if(payload.wait_for_result){
      setStatus('Done — repo: ' + data.repo_url)
      showPreview(data.pages_url)
    } else {
      setStatus('Accepted — build running in background')
      // start polling for result every 3s
      pollForResult(payload.email, payload.task, payload.nonce)
    }
  }catch(err){
    setStatus('Error: ' + err.message)
  }
})

function showPreview(url){
  if(!url) return;
  preview.innerHTML = `<iframe src="${url}"></iframe>`
}

let _pollHandle = null
function pollForResult(email, task, nonce){
  if(_pollHandle) clearInterval(_pollHandle)
  _pollHandle = setInterval(async ()=>{
    try{
      const q = new URLSearchParams({email, task, nonce})
      const r = await fetch('/result?'+q.toString())
      const j = await r.json()
      if(j && j.repo_url){
        setStatus('Build complete — ' + j.repo_url)
        showPreview(j.pages_url)
        clearInterval(_pollHandle)
        _pollHandle = null
      }
    }catch(e){
      // ignore transient errors
    }
  }, 3000)
}

document.getElementById('clear').addEventListener('click',(e)=>{form.reset(); setStatus('')})
