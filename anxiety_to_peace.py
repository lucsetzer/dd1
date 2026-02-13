# peace_of_mind_app.py
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import HTMLResponse
import json
import httpx

app = FastAPI()

DEEPSEEK_API_KEY = "sk-d4294fb0fbfc4a56af3050ac660252c2"
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"

async def call_deepseek(prompt: str):
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "You are a compassionate code therapist. You turn anxiety into understanding."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(DEEPSEEK_URL, json=data, headers=headers)
        return response.json()["choices"][0]["message"]["content"]

@app.post("/analyze")
async def analyze_codebase(
    code_files: list[UploadFile] = File(...),
    user_context: str = Form("I'm stressed about this code")
):
    # Read files
    files_content = []
    for file in code_files:
        content = await file.read()
        files_content.append({
            "name": file.filename,
            "content": content.decode()[:5000]  # Limit size
        })
    
    # Build the peace-of-mind prompt
    prompt = f"""
    USER'S EMOTIONAL STATE: {user_context}
    
    FILES TO ANALYZE:
    {json.dumps(files_content, indent=2)}
    
    ---
    CREATE A PEACE-OF-MIND REPORT:
    
    1. 🎯 ONE-SENTENCE SUMMARY
    [What this code DOES in plain English]
    
    2. 🗺️ THE LAYOUT (Don't overwhelm me)
    [Just the 3-5 most important files/folders and what they do]
    
    3. 🔗 MAIN CONNECTIONS
    [How the important parts talk to each other, like a simple story]
    
    4. 🚨 3 IMMEDIATE CONCERNS
    [Most urgent issues in simple terms]
    
    5. 🔐 SECURITY CHECK
    [Any obvious security issues? Keep it simple]
    
    6. 🏃 GET IT RUNNING
    [Copy-paste commands to make it work]
    
    7. 🧒 THE 10-YEAR-OLD EXPLANATION
    [Use an analogy. Make it comforting]
    
    8. 💡 YOUR FIRST 10 MINUTES
    [One small, achievable task to build confidence]
    """
    
    # Get the report
    report = await call_deepseek(prompt)
    
    # Return as beautiful HTML
    return HTMLResponse(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Your Peace Report</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@1/css/pico.min.css">
        <style>
            .peace-report {{ max-width: 800px; margin: 2rem auto; padding: 2rem; }}
            .section {{ margin: 2rem 0; padding: 1rem; background: #f8f9fa; border-radius: 8px; }}
            h2 {{ color: #2c3e50; }}
            .emoji {{ font-size: 1.5em; margin-right: 10px; }}
        </style>
    </head>
    <body>
        <main class="container peace-report">
            <h1>🧘 Your Code Peace Report</h1>
            <p><em>Generated for: {user_context}</em></p>
            
            <div class="section">
                <h2><span class="emoji">📄</span>Files Analyzed</h2>
                <ul>
                    {''.join(f'<li>{f["name"]}</li>' for f in files_content)}
                </ul>
            </div>
            
            <div class="section">
                <pre style="white-space: pre-wrap; font-family: sans-serif;">{report}</pre>
            </div>
            
            <div class="section">
                <h2><span class="emoji">🎯</span>Next Step</h2>
                <a href="/" class="button">Analyze Another Codebase</a>
            </div>
        </main>
    </body>
    </html>
    """)

@app.get("/")
async def home():
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Code Peace</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@1/css/pico.min.css">
        <style>
            .hero {{ text-align: center; padding: 4rem 1rem; }}
            .upload-box {{ border: 2px dashed #ccc; padding: 2rem; margin: 2rem 0; }}
        </style>
    </head>
    <body>
        <main class="container">
            <div class="hero">
                <h1>🧘 Code Peace</h1>
                <p class="lead"><strong>Anxiety-causing code → Peace-of-mind report</strong></p>
                <p>Upload your scary codebase. Get a calming, simple explanation.</p>
            </div>
            
            <form action="/analyze" method="post" enctype="multipart/form-data">
                <div class="upload-box">
                    <label for="context">
                        <strong>How are you feeling about this code?</strong>
                    </label>
                    <input type="text" id="context" name="user_context" 
                           placeholder="e.g., 'I inherited this and I'm overwhelmed'" required>
                    
                    <label for="files">
                        <strong>Upload your code files:</strong>
                    </label>
                    <input type="file" id="files" name="code_files" multiple required>
                    
                    <small>Select multiple files (Ctrl+click) or upload a ZIP</small>
                </div>
                
                <button type="submit" style="width: 100%; padding: 1rem; font-size: 1.2rem;">
                    🧘 Generate Peace Report
                </button>
            </form>
            
            <footer style="text-align: center; margin-top: 3rem; color: #666;">
                <p>No chat. No complexity. Just clarity.</p>
            </footer>
        </main>
    </body>
    </html>
    """)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)