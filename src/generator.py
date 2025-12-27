import os
import base64
from datetime import datetime
import json

from . import llm_generator


def generate_app(request_json, out_dir):
    """Generate a minimal static app based on brief and attachments.

    This is a simple placeholder generator. Replace with LLM-driven generation
    as needed. Creates an index.html, README.md, LICENSE, and assets.
    Returns the path where files were written.
    """
    brief = request_json.get("brief", "")
    attachments = request_json.get("attachments", [])

    # If OPENAI_API_KEY present, ask LLM to generate files; otherwise use placeholder
    try:
        files = llm_generator.generate_with_openai(brief, attachments) if llm_generator.OPENAI_API_KEY else None
    except Exception:
        files = None

    os.makedirs(out_dir, exist_ok=True)

    if files:
        # files should be dict filename -> content
        for name, content in files.items():
            path = os.path.join(out_dir, name)
            d = os.path.dirname(path)
            if d:
                os.makedirs(d, exist_ok=True)
            # write as text
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
    else:
        # Write index.html that renders the brief and any ?url param
        index_html_template = """
<!doctype html>
<html>
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width,initial-scale=1" />
    <title>Student App</title>
    <style>body{font-family:sans-serif;padding:1rem}#output{white-space:pre-wrap}</style>
</head>
<body>
    <h1>Student App</h1>
    <p id="brief">{BRIEF}</p>
    <div id="output">Loading...</div>

    <script>
    function getParam(name){const u=new URL(location.href);return u.searchParams.get(name)}
    const url = getParam('url');
    const out = document.getElementById('output');
    if(url){
        out.textContent = 'Provided URL: ' + url;
        // try to show image if possible
        const img = document.createElement('img'); img.src = url; img.style.maxWidth='90%'; img.alt='provided';
        out.innerHTML=''; out.appendChild(img);
    } else {
        out.textContent = 'No URL provided — using attachment if present.';
    }
    </script>
</body>
</html>
"""

        index_html = index_html_template.replace('{BRIEF}', brief)
        with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(index_html)

    # Save attachments to assets/
    assets_dir = os.path.join(out_dir, "assets")
    os.makedirs(assets_dir, exist_ok=True)
    for a in attachments:
        name = a.get("name")
        url = a.get("url")
        if not name or not url:
            continue
        if url.startswith("data:"):
            # data URI
            comma = url.find(',')
            data = url[comma+1:]
            try:
                b = base64.b64decode(data)
            except Exception:
                b = data.encode('utf-8')
            with open(os.path.join(assets_dir, name), "wb") as af:
                af.write(b)

    # README
    readme = f"""
# Student-generated app

Generated from brief:

```
{brief}
```

Generated at {datetime.utcnow().isoformat()} UTC.

License: MIT
"""
    with open(os.path.join(out_dir, "README.md"), "w", encoding="utf-8") as f:
        f.write(readme)

    # MIT LICENSE
    mit = """MIT License

Copyright (c) %d

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
""" % (datetime.utcnow().year)
    with open(os.path.join(out_dir, "LICENSE"), "w", encoding="utf-8") as f:
        f.write(mit)

    return out_dir
