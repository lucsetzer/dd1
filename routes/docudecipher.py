from fastapi import APIRouter, Request, Query, Cookie, File, UploadFile, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pathlib import Path
from dotenv import load_dotenv

import git
import tempfile
import shutil
import os
import uuid
import asyncio
import time

templates = Jinja2Templates(directory="templates")

router = APIRouter()

load_dotenv()

# ========== ANALYSIS QUEUE ==========
# Simple in-memory store for analysis jobs
analysis_queue = {}

async def loading_response(analysis_id: str):
    """Return loading page for analysis jobs"""
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Analyzing...</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <link rel="stylesheet" href="/static/css/brand.css">
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: #0f172a;
                color: white;
                margin: 0;
                padding: 0;
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }}
            .container {{
                max-width: 600px;
                text-align: center;
                padding: 3rem;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div>
                <i class="fas fa-lightbulb"></i>
            </div>
            <h1>Analyzing Repository</h1>
            <p id="status">Cloning and analyzing code structure...</p>
        </div>
        <script>
            const analysisId = "{analysis_id}";
            function checkProgress() {{
                fetch('/api/analysis-status/' + analysisId)
                    .then(r => r.json())
                    .then(data => {{
                        if (data.status === 'complete') {{
                            window.location.href = '/result/' + analysisId;
                        }} else if (data.status === 'error') {{
                            window.location.href = '/error?message=' + encodeURIComponent(data.error);
                        }} else {{
                            if (data.message) {{
                                document.getElementById('status').textContent = data.message;
                            }}
                            setTimeout(checkProgress, 1000);
                        }}
                    }})
                    .catch(() => setTimeout(checkProgress, 2000));
            }}
            setTimeout(checkProgress, 1000);
        </script>
    </body>
    </html>
    '''
    return HTMLResponse(html)

def layout(title: str, content: str) -> str:
    """Layout with brand CSS"""
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title} - DocuDecipher</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <link rel="stylesheet" href="/static/css/brand.css">
    </head>
    <body style="background: #0f172a; color: white; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
        {content}
    </body>
    </html>
    """

# ===== DOCUDECIPHER =====
@router.get("/docudecipher-home")
async def home():
    content = '''
    <style>
        .home-container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem 1rem;
        }
        
        .hero {
            text-align: center;
            margin-bottom: 4rem;
        }
        
        .hero-icon {
            font-size: 4rem;
            color: #fbbf24;
            margin-bottom: 1rem;
        }
        
        .hero h1 {
            font-size: 2.5rem;
            color: white;
            margin-bottom: 1rem;
        }
        
        .hero p {
            font-size: 1.25rem;
            color: #94a3b8;
            max-width: 600px;
            margin: 0 auto 2rem;
        }
        
        .features-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1.5rem;
            margin: 3rem 0;
        }
        
        .feature-card {
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 1.5rem;
            text-align: center;
            transition: all 0.2s ease;
        }
        
        .feature-card:hover {
            border-color: #0cc0df;
            transform: translateY(-4px);
            box-shadow: 0 8px 20px rgba(12, 192, 223, 0.15);
        }
        
        .feature-card i {
            font-size: 2.5rem;
            color: #0cc0df;
            margin-bottom: 1rem;
        }
        
        .feature-card h3 {
            color: white;
            margin: 0.5rem 0;
            font-size: 1.25rem;
        }
        
        .feature-card p {
            color: #94a3b8;
            margin: 0;
            font-size: 0.95rem;
        }
        
        .btn-primary {
            display: inline-block;
            background: #0cc0df;
            color: white;
            padding: 1rem 2.5rem;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 500;
            font-size: 1.1rem;
            transition: all 0.2s ease;
            border: none;
        }
        
        .btn-primary:hover {
            background: #0aa8c4;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(12, 192, 223, 0.2);
        }
        
        .btn-primary i {
            margin-right: 0.5rem;
        }
        
        .warning-box {
            max-width: 600px;
            margin: 3rem auto;
            background: rgba(12, 192, 223, 0.05);
            border-left: 4px solid #0cc0df;
            padding: 1.5rem;
            border-radius: 8px;
        }
        
        .warning-box h3 {
            color: #0cc0df;
            margin-top: 0;
            margin-bottom: 0.5rem;
        }
        
        .warning-box p {
            color: #94a3b8;
            margin: 0;
        }
        
        @media (max-width: 768px) {
            .features-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
    
    <div class="home-container">
        <!-- Hero Section -->
        <div class="hero">
            <div class="hero-icon">
                <i class="fas fa-lightbulb"></i>
            </div>
            <h1>DocuDecipher</h1>
            <p>AI-powered analysis of technical documentation and code. Understand APIs, legacy systems, and complex codebases.</p>
            <a href="/wizard" class="btn-primary">
                <i class="fas fa-search"></i> Analyze Technical Content
            </a>
        </div>
        
        <!-- Features Grid -->
        <div class="features-grid">
            <div class="feature-card">
                <i class="fab fa-github"></i>
                <h3>GitHub Repos</h3>
                <p>Understand legacy codebases</p>
            </div>
            
            <div class="feature-card">
                <i class="fas fa-code-branch"></i>
                <h3>API Documentation</h3>
                <p>Decipher REST/GraphQL APIs</p>
            </div>
            
            <div class="feature-card">
                <i class="fas fa-file-code"></i>
                <h3>Technical Specs</h3>
                <p>Understand system architecture</p>
            </div>
            
            <div class="feature-card">
                <i class="fas fa-lock"></i>
                <h3>Security Analysis</h3>
                <p>Find vulnerabilities in code</p>
            </div>
            
            <div class="feature-card">
                <i class="fas fa-project-diagram"></i>
                <h3>Dependency Maps</h3>
                <p>Visualize code relationships</p>
            </div>
            
            <div class="feature-card">
                <i class="fas fa-comments"></i>
                <h3>Code Comments</h3>
                <p>Explain complex functions</p>
            </div>
        </div>
        
        <!-- Developer Note -->
        <div class="warning-box">
            <h3><i class="fas fa-exclamation-triangle"></i> For Developers</h3>
            <p>Accelerate onboarding, reduce technical debt, and understand complex systems faster. Perfect for new team members and legacy code maintenance.</p>
        </div>
    </div>
    '''
    return HTMLResponse(layout("DocuDecipher - Technical Analysis", content))

@router.get("/document-wizard")
async def document_wizard_home(request: Request):
    """Document Wizard landing page - explains what it does"""
    return templates.TemplateResponse("document_wizard_home.html", {
        "request": request,
        "title": "DocuDecipher",
        "description": "AI-powered analysis of code, apis, and technical documents"
    })

# ========== STEP 1: DOCUMENT TYPE ==========
@router.get("/wizard")
async def step1():
    cards = [
        ("github", "fab fa-github", "GitHub Repository", "Analyze entire codebase, dependencies, structure"),
        ("api", "fas fa-code-branch", "API Documentation", "REST, GraphQL, OpenAPI/Swagger specs"),
        ("legacy", "fas fa-history", "Legacy Code", "Old systems, spaghetti code, no documentation"),
        ("security", "fas fa-lock", "Security Audit", "Find vulnerabilities, security analysis"),
        ("dependency", "fas fa-project-diagram", "Dependency Map", "Visualize imports, modules, connections"),
        ("functions", "fas fa-code", "Function Analysis", "Understand complex functions, algorithms"),
        ("config", "fas fa-cogs", "Configuration Files", ".env, docker, k8s, infrastructure as code"),
        ("documentation", "fas fa-book", "Technical Docs", "READMEs, wikis, architecture documents"),
    ]
    
    # Generate cards with inline styles that CANNOT be overridden
    cards_html = ""
    for doc_type, icon, title, desc in cards:
        cards_html += f'''
        <div class="card-container">
            <a href="/wizard/step2?doc_type={doc_type}" 
               style="
                display: block;
                padding: 1.5rem;
                text-align: center;
                text-decoration: none;
                min-height: 220px;
               ">
                <i class="fas {icon}" style="font-size: 2.5rem; color: #0cc0df; margin-bottom: 1rem; display: block;"></i>
                <h3 style="margin: 0.5rem 0; color: white; text-decoration: none !important;">{title}</h3>
                <p style="color: #9ca3af; margin: 0; text-decoration: none !important;">{desc}</p>
            </a>
        </div>
        '''
    
    # COMPLETE HTML - No external dependencies, no layout() function
    html = f'''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Step 1: Documentation Type</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <link rel="stylesheet" href="/static/css/brand.css">
        <style>
          /* MINIMAL STYLES - layout only, colors come from brand.css */
          * {{
              margin: 0;
              padding: 0;
              box-sizing: border-box;
          }}
          
          body {{
              background: #0f172a;
              color: white;
              font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
              min-height: 100vh;
              padding: 20px;
          }}
          
          .container {{
              max-width: 1200px;
              margin: 0 auto;
          }}
          
          .header {{
              text-align: center;
              margin-bottom: 3rem;
          }}
          
          .cards-grid {{
              display: grid;
              grid-template-columns: repeat(3, 1fr);
              gap: 1.5rem;
              margin: 2rem 0;
          }}
          
          @media (max-width: 1024px) {{
              .cards-grid {{
                  grid-template-columns: repeat(2, 1fr);
              }}
          }}
          
          @media (max-width: 768px) {{
              .cards-grid {{
                  grid-template-columns: 1fr;
              }}
          }}
          
          .cancel-btn {{
              display: block;
              width: fit-content;
              margin: 3rem auto 0;
              padding: 0.75rem 1.5rem;
              border-radius: 6px;
              text-decoration: none;
              text-align: center;
              border: none;
              font-size: 1rem;
              cursor: pointer;
          }}
          
          /* ===== CARD CONTAINERS (for wizard steps) ===== */
          
          .card-container a {{
              border: none !important;
              border-color: transparent !important;
              outline: none !important;
          }}

          /* Keep the outer card border */
          .card-container {{
              border: 1px solid #334155 !important;
              background: #1e293b !important;
          }}

          /* Hover state - only show outer border */
          .card-container:hover {{
              border-color: #0cc0df !important;
          }}
      </style>
    </head>
    <body>
        
        <div class="container">
            <div class="header">
                <h1>Step 1: What do you need to understand?</h1>
                <p>Select the type of technical content you want to analyze</p>
            </div>
            
            <div class="cards-grid">
                {cards_html}
            </div>
            
            <a href="/" class="cancel-btn">Cancel</a>
        </div>
        
        <script>
            // Debug: Check if any links have text-decoration
            document.addEventListener('DOMContentLoaded', function() {{
                const links = document.querySelectorAll('a');
                links.forEach(link => {{
                    const style = window.getComputedStyle(link);
                    console.log('Link text-decoration:', style.textDecoration);
                    if (style.textDecoration.includes('underline')) {{
                        link.style.border = '2px solid red'; // Highlight problematic links
                    }}
                }});
            }});
        </script>
    </body>
    </html>
    '''
    
    return HTMLResponse(html)  # Don't use layout() - bypass everything

# ========== STEP 2: AUDIENCE LEVEL ==========
@router.get("/wizard/step2")
async def step2(doc_type: str = Query("github")):
    doc_type_names = {
        "github": "GitHub Repository",
        "api": "API Documentation", 
        "legacy": "Legacy Code",
        "security": "Security Audit",
        "dependency": "Dependency Map",
        "functions": "Function Analysis",
        "config": "Configuration Files",
        "documentation": "Technical Documentation"
    }
    
    level_cards = [
        ("novice", "fa-seedling", "Novice", "New to programming. Explain concepts simply."),
        ("general", "fa-user", "General", "Basic tech knowledge. Use plain language."),
        ("educated", "fa-user-graduate", "Educated", "Some coding experience. Can use technical terms."),
        ("professional", "fa-briefcase", "Professional", "Experienced. Give me architecture details.")
    ]
    
    cards_html = ""
    for card_level, icon, title, desc in level_cards:
        cards_html += f'''
        <a href="/wizard/step3?doc_type={doc_type}&level={card_level}" class="step-card">
            <i class="fas {icon}"></i>
            <h3>{title}</h3>
            <p>{desc}</p>
        </a>
        '''
    
    content = f'''
    <style>
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem 1rem;
        }}
        
        .text-center {{
            text-align: center;
        }}
        
        .card-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 1.5rem;
            margin: 2rem 0;
        }}
        
        @media (max-width: 768px) {{
            .card-grid {{
                grid-template-columns: 1fr;
            }}
        }}
        
        .step-card {{
            background: #1e293b !important;
            background-color: #1e293b !important;
            border: 1px solid #334155 !important;
            border-radius: 12px !important;
            display: block !important;
            padding: 1.5rem !important;
            text-align: center !important;
            text-decoration: none !important;
            color: white !important;
            transition: all 0.2s ease !important;
            min-height: 180px;
        }}
        
        .step-card * {{
            text-decoration: none !important;
        }}
        
        .step-card:hover,
        .step-card:hover * {{
            text-decoration: none !important;
        }}
        
        .step-card:hover {{
            border-color: #0cc0df !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 20px rgba(12, 192, 223, 0.15) !important;
        }}

        .step-card i {{
            color: #0cc0df !important;
            font-size: 2rem !important;
            margin-bottom: 0.75rem !important;
            display: block !important;
        }}
        
        .step-card h3 {{
            color: white !important;
            margin: 0.5rem 0 !important;
        }}
        
        .step-card p {{
            color: #94a3b8 !important;
            margin: 0 !important;
            font-size: 0.9rem !important;
        }}
        
        .info-box {{
            background: rgba(12, 192, 223, 0.1);
            border-left: 4px solid #0cc0df;
            padding: 1rem;
            border-radius: 4px;
            margin: 1.5rem 0;
        }}

        .btn-secondary {{
            background: #64748b;
            color: white;
            padding: 0.75rem 1.5rem;
            border-radius: 6px;
            text-decoration: none;
            display: inline-block;
        }}

        .btn-secondary:hover {{
            background: #4b5565;
        }}
    </style>
    <div class="container">
        <h1 class="text-center">Step 2: Your Knowledge Level</h1>
        <p class="text-center">How familiar are you with {doc_type_names.get(doc_type, 'technical content').lower()}?</p>
        <p class="text-center"><strong>Analysis Type:</strong> {doc_type_names.get(doc_type, 'Technical Analysis')}</p>
        
        <div class="card-grid">
            {cards_html}
        </div>
        
        <div class="info-box">
            <p><strong>Tip:</strong> Choose "Novice" for beginner-friendly explanations. "Professional" gets deeper technical analysis.</p>
        </div>
        
        <div class="text-center" style="margin-top: 2rem;">
            <a href="/wizard" class="btn btn-secondary">← Back to Step 1</a>
        </div>
    </div>
    '''
    
    return HTMLResponse(layout("", content))

# ===== STEP 3: DOCUMENT INPUT (ENHANCED) =====
@router.get("/wizard/step3")
async def step3(
    doc_type: str = Query("legal"),
    level: str = Query("novice")
):
    print(f"📝 STEP 3 - Received doc_type: {doc_type}, level: {level}")
    
    doc_type_names = {
      "github": "GitHub Repository",
      "api": "API Documentation", 
      "legacy": "Legacy Code",
      "security": "Security Audit",
      "dependency": "Dependency Map",
      "functions": "Function Analysis",
      "config": "Configuration Files",
      "documentation": "Technical Documentation"
    }
    
    level_names = {
        "novice": "Novice",
        "general": "General Public", 
        "educated": "Educated Layperson",
        "professional": "Related Professional"
    }
    
    content = f'''
    <div style="max-width: 800px; margin: 0 auto;">
    
        
        <h1 style="text-align: center; color: var(--primary);">Step 3: Add Your Documentation</h1>
        
        <!-- TAB NAVIGATION -->
        <div style="display: flex; border-bottom: 2px solid #374151; margin: 2rem 0;">
            <button class="tab-btn active" onclick="showTab('text-tab')" 
                    style="flex: 1; padding: 1rem; background: none; border: none; color: #0cc0df; border-bottom: 2px solid #0cc0df; cursor: pointer;">
                <i class="fas fa-paste"></i> Paste Text
            </button>
            <button class="tab-btn" onclick="showTab('upload-tab')" 
                    style="flex: 1; padding: 1rem; background: none; border: none; color: #9ca3af; cursor: pointer;">
                <i class="fas fa-upload"></i> Upload File
            </button>
            <button class="tab-btn" onclick="showTab('url-tab')" 
                    style="flex: 1; padding: 1rem; background: none; border: none; color: #9ca3af; cursor: pointer;">
                <i class="fas fa-link"></i> From URL
            </button>
        </div>
        
                <!-- TEXT TAB (default visible) -->
        <div id="text-tab" class="tab-content">
            <form action="/process" method="POST" id="documentForm">
                <input type="hidden" name="doc_type" value="{doc_type}">
                <input type="hidden" name="level" value="{level}">
                
                <div style="margin: 2rem 0;">
                    <label for="document_text">
                        <strong>Paste Document Text:</strong>
                        <p style="color: #6b7280; margin: 0.5rem 0;">
                            Copy and paste the text you want to understand (max 50,000 characters)
                        </p>
                    </label>
                    <textarea id="document_text" name="document_text" rows="12" 
                              placeholder="Paste your legal clause, medical report, contract section, or any complex text here..."
                              style="width: 100%; padding: 1rem; border: 2px solid #374151; border-radius: 0.5rem; background: rgba(255,255,255,0.05); color: white; font-family: monospace;"></textarea>
                    <div style="text-align: right; margin-top: 0.5rem;">
                        <span id="charCount" style="color: #6b7280; font-size: 0.9rem;">0/50000 characters</span>
                    </div>
                </div>
                
                <div style="margin: 2rem 0;">
                    <label for="specific_questions">
                        <strong>Specific Questions (Optional):</strong>
                        <p style="color: #6b7280; margin: 0.5rem 0;">
                            What specifically do you want to understand about this document?
                        </p>
                    </label>
                    <textarea id="specific_questions" name="specific_questions" rows="3" 
                              placeholder="• What does this code do? 
• Are there security vulnerabilities?
• How can this be optimized?"
                              style="width: 100%; padding: 1rem; border: 2px solid #374151; border-radius: 0.5rem; background: rgba(255,255,255,0.05); color: white;"></textarea>
                </div>
                
                <div style="text-align: center; margin: 2rem 0;">
                    <button type="submit" id="submitBtn" style="padding: 1rem 3rem; font-size: 1.2rem; background: #0cc0df; color: white; border: none; border-radius: 8px; cursor: pointer;">
                        <i class="fas fa-search"></i> Decode Document (3 tokens)
                    </button>
                </div>
            </form>
            
            <script>
            // Character counter
            document.getElementById('document_text').addEventListener('input', function(e) {{
                const count = e.target.value.length;
                document.getElementById('charCount').textContent = count + '/50000 characters';
                if (count > 50000) {{
                    e.target.value = e.target.value.substring(0, 50000);
                    document.getElementById('charCount').textContent = '50000/50000 characters (limit reached)';
                    document.getElementById('charCount').style.color = '#dc2626';
                }} else if (count > 40000) {{
                    document.getElementById('charCount').style.color = '#d97706';
                }} else {{
                    document.getElementById('charCount').style.color = '#6b7280';
                }}
            }});
            </script>
        </div>
        
                <!-- UPLOAD TAB (hidden by default) -->
        <div id="upload-tab" class="tab-content" style="display: none;">
            <div style="text-align: center; margin-bottom: 1.5rem;">
                <div style="font-size: 3rem; color: #0cc0df; margin-bottom: 0.5rem;">
                    <i class="fas fa-cloud-upload-alt"></i>
                </div>
                <h3 style="color: white;">Upload a File</h3>
                <p style="color: #9ca3af;">Code files (.py, .json, .js, .yml, .html, .css) or technical documentation  (max 10MB)</p>
            </div>
            
            <form action="/process-upload" method="POST" enctype="multipart/form-data">
                <input type="hidden" name="doc_type" value="{doc_type}">
                <input type="hidden" name="level" value="{level}">
                
                <div style="margin: 1.5rem 0;">
                    <label for="file" style="color: white;"><strong>Choose File:</strong></label>
                    <input type="file" id="file" name="file" accept=".pdf,.doc,.docx,.txt" required
                           style="width: 100%; padding: 1rem; border: 2px dashed #0cc0df; border-radius: 8px; margin-top: 0.5rem; background: rgba(255,255,255,0.05); color: white;">
                </div>
                
                <div style="margin: 2rem 0;">
                    <label for="upload_questions" style="color: white;">
                        <strong>Specific Questions (Optional):</strong>
                        <p style="color: #9ca3af; margin: 0.5rem 0;">
                            What specifically do you want to understand about this document?
                        </p>
                    </label>
                    <textarea id="upload_questions" name="specific_questions" rows="3" 
                              placeholder="• What does this code do? 
• Are there security vulnerabilities?
• how can this be optimized?"
                              style="width: 100%; padding: 1rem; border: 2px solid #374151; border-radius: 0.5rem; background: rgba(255,255,255,0.05); color: white;"></textarea>
                </div>
                
                <div style="text-align: center;">
                    <button type="submit" style="padding: 1rem 2rem; background: #0cc0df; color: white; border: none; border-radius: 8px; font-size: 1.1rem; cursor: pointer;">
                        <i class="fas fa-search"></i> Upload & Analyze (3 tokens)
                    </button>
                    <p style="color: #9ca3af; margin-top: 0.5rem; font-size: 0.9rem;">
                        File will be processed securely on our servers
                    </p>
                </div>
            </form>
        </div>
        
                <!-- URL TAB (hidden by default) -->
        <div id="url-tab" class="tab-content" style="display: none;">
            <div style="text-align: center; margin-bottom: 1.5rem;">
                <div style="font-size: 3rem; color: #0cc0df; margin-bottom: 0.5rem;">
                    <i class="fas fa-link"></i>
                </div>
                <h3 style="color: white;">Analyze Web Page</h3>
                <p style="color: #9ca3af;">Enter a URL to analyze webpage content</p>
            </div>
            
            <form action="/process-url" method="POST" id="urlForm">
                <input type="hidden" name="doc_type" value="{doc_type}">
                <input type="hidden" name="level" value="{level}">
                
                <div style="margin: 1.5rem 0;">
                    <label for="url" style="color: white;"><strong>Web Page URL:</strong></label>
                    <input type="url" id="url" name="url" 
                           placeholder="https://example.com/terms-of-service"
                           required
                           style="width: 100%; padding: 1rem; border: 2px solid #374151; border-radius: 0.5rem; background: #0f172a; color: white; font-family: monospace;">
                    <p style="color: #9ca3af; font-size: 0.9rem; margin-top: 0.5rem;">
                        Works with most public web pages (terms of service, articles, documentation)
                    </p>
                </div>
                
                <div style="margin: 2rem 0;">
                    <label for="url_questions" style="color: white;">
                        <strong>Specific Questions (Optional):</strong>
                        <p style="color: #9ca3af; margin: 0.5rem 0;">
                            What specifically do you want to understand about this page?
                        </p>
                    </label>
                    <textarea id="url_questions" name="specific_questions" rows="3" 
                              placeholder="• What are the key requirements?
• What are my obligations?
• What rights am I giving up?"
                              style="width: 100%; padding: 1rem; border: 2px solid #374151; border-radius: 0.5rem; background: rgba(255,255,255,0.05); color: white;"></textarea>
                </div>
                
                <div style="text-align: center;">
                    <button type="submit" style="padding: 1rem 2rem; background: #0cc0df; color: white; border: none; border-radius: 8px; font-size: 1.1rem; cursor: pointer;">
                        <i class="fas fa-globe"></i> Fetch & Analyze (3 tokens)
                    </button>
                    <p style="color: #9ca3af; margin-top: 0.5rem; font-size: 0.9rem;">
                        Content will be fetched and analyzed securely
                    </p>
                </div>
            </form>
            
            <div style="background: rgba(12, 192, 223, 0.1); border-radius: 8px; padding: 1rem; margin-top: 2rem;">
                <p style="margin: 0; color: #0cc0df; font-size: 0.9rem;">
                    <i class="fas fa-info-circle"></i> 
                    <strong>Note:</strong> Some websites may block automated access. For private pages, use copy/paste instead.
                </p>
            </div>
        </div>
        
        <!-- Tab switching JavaScript -->
        <script>
        function showTab(tabId) {{
            // Hide all tabs
            document.querySelectorAll('.tab-content').forEach(tab => {{
                tab.style.display = 'none';
            }});
            // Show selected tab
            document.getElementById(tabId).style.display = 'block';
            
            // Update tab buttons
            document.querySelectorAll('.tab-btn').forEach(btn => {{
                btn.style.color = '#9ca3af';
                btn.style.borderBottom = 'none';
            }});
            event.currentTarget.style.color = '#0cc0df';
            event.currentTarget.style.borderBottom = '2px solid #0cc0df';
        }}
        </script>
    </div>
    '''
    return HTMLResponse(layout("Step 3: Document Input", content))

# ========== PROCESS (ENHANCED) ==========
@router.post("/process")
async def process_document(
    doc_type: str = Form(...),
    level: str = Form(...),
    document_text: str = Form(...),
    specific_questions: str = Form("")
):
    # Validate input
    if not document_text.strip():
        return HTMLResponse(layout("Error", '''
            <div style="text-align: center; padding: 4rem 0;">
                <h1 style="color: #dc2626;"><i class="fas fa-exclamation-triangle"></i> No Code Provided</h1>
                <p>Please paste some code or upload a file.</p>
                <a href="/wizard/step3?doc_type={doc_type}&level={level}" role="button">Try Again</a>
            </div>
        '''))
    
    # Check token limit (simplified - you'll need user auth)
    # For now, assume user has tokens
    
    # Generate unique ID for this analysis
    analysis_id = str(uuid.uuid4())
    
    # Store in queue
    analysis_queue[analysis_id] = {
        "doc_type": doc_type,
        "level": level,
        "document_text": document_text[:10000],  # Limit to 10K chars
        "specific_questions": specific_questions,
        "status": "processing",
        "created_at": time.time(),
        "progress": 0.1,
        "message": "Starting analysis..."
    }
    
    # Start background task
    asyncio.create_task(process_document_background(analysis_id))
    
    # Show loading page with progress updates
    loading_content = f'''
    <!DOCTYPE html>
<html>
<head>
    <title>Analyzing Your Code - DocuDecipher</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #000;
            color: #fff;
            margin: 0;
            padding: 0;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .container {{
            max-width: 600px;
            text-align: center;
            padding: 3rem;
        }}
        .spinner {{
            font-size: 4rem;
            color: #0cc0df;
            margin-bottom: 1rem;
            animation: spin 1s linear infinite;
        }}
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        h1 {{ color: #0cc0df; margin-bottom: 1rem; }}
        p {{ color: #9ca3af; margin-bottom: 2rem; }}
        .progress-bar {{
            width: 100%;
            height: 8px;
            background: #374151;
            border-radius: 4px;
            margin: 2rem 0;
            overflow: hidden;
        }}
        .progress {{
            height: 100%;
            background: #0cc0df;
            width: 0%;
            animation: loading 2s infinite;
            border-radius: 4px;
        }}
        @keyframes loading {{
            0% {{ width: 0%; margin-left: 0%; }}
            50% {{ width: 50%; }}
            100% {{ width: 0%; margin-left: 100%; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="spinner">
            <i class="fas fa-lightbulb"></i>
        </div>
        
        <h1>Analyzing Your Code</h1>
        <p>We're decoding your {doc_type.replace("_", " ").title()} for {level.replace("_", " ").title()} understanding</p>
        
        <div class="progress-bar">
            <div class="progress"></div>
        </div>
        
        <p id="status" style="color: #0cc0df;">Reading code and preparing analysis...</p>
        
        <div style="background: rgba(12, 192, 223, 0.1); padding: 1rem; border-radius: 8px; margin-top: 2rem;">
            <p style="margin: 0; color: #0cc0df; font-size: 0.9rem;">
                <i class="fas fa-lightbulb"></i> 
                <span id="tip">Parsing code structure, identifying patterns, and analyzing complexity...</span>
            </p>
        </div>
    </div>
    
    <script>
    const analysisId = "{analysis_id}";
    
    function checkProgress() {{
        fetch('/api/analysis-status/' + analysisId)
            .then(r => r.json())
            .then(data => {{
                if (data.status === 'complete') {{
                    window.location.href = '/result/' + analysisId;
                }} else if (data.status === 'error') {{
                    window.location.href = '/error?message=' + encodeURIComponent(data.error);
                }} else {{
                    // Update status message if available
                    if (data.message) {{
                        document.getElementById('status').textContent = data.message;
                    }}
                    // Continue polling
                    setTimeout(checkProgress, 1000);
                }}
            }})
            .catch(error => {{
                console.error('Progress check failed:', error);
                setTimeout(checkProgress, 2000);
            }});
    }}
    
    // Start polling after 1 second
    setTimeout(checkProgress, 1000);
    </script>
</body>
</html>
    '''

    return HTMLResponse(loading_content)

# Add this endpoint
@router.get("/api/analysis-status/{analysis_id}")
async def get_analysis_status(analysis_id: str):
    if analysis_id in analysis_queue:
        status = analysis_queue[analysis_id]
        # Calculate progress based on status
        progress = 0.25  # Default
        if status.get("ai_processing"):
            progress = 0.5
        if status.get("formatting"):
            progress = 0.75
        
        return {
            "status": status["status"],
            "progress": progress,
            "message": status.get("message", "Processing...")
        }
    return {"status": "not_found"}

@router.post("/process-url")
async def process_url(
    doc_type: str = Form(...),
    level: str = Form(...),
    url: str = Form(...),
    specific_questions: str = Form("")
):
    """Fetch and analyze content from a URL"""
    
    try:
        # 1. Fetch the webpage
        import requests
        from bs4 import BeautifulSoup
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Document Wizard Bot)'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # 2. Extract text (simple version - you might want more sophisticated extraction)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        text = soup.get_text(separator='\n', strip=True)
        
        # Limit text length
        text = text[:15000]  # 15K chars max
        
        if not text.strip():
            return HTMLResponse(layout("URL Error", f"""
                <div style="text-align: center; padding: 4rem;">
                    <h1>No Code or Content Found</h1>
                    <p>Could not extract analyzable content from {url}</p>
                    <p>Try copying the source directly and use the Paste Code option.</p>
                    <a href="/wizard/step3?doc_type={doc_type}&level={level}">Try Again</a>
                </div>
            """))
        
        # 3. Use the same process as text input
        return await process_document(
            doc_type=doc_type,
            level=level,
            document_text=text,
            specific_questions=specific_questions
        )
        
    except requests.exceptions.RequestException as e:
        return HTMLResponse(layout("URL Error", f"""
            <div style="text-align: center; padding: 4rem;">
                <h1>URL Error</h1>
                <p>Failed to fetch {url}</p>
                <p>Error: {str(e)}</p>
                <p>Make sure the URL is public and accessible.</p>
                <a href="/wizard/step3?doc_type={doc_type}&level={level}">Try Again</a>
            </div>
        """))
    
    except Exception as e:
        return HTMLResponse(layout("Error", f"""
            <div style="text-align: center; padding: 4rem;">
                <h1>Processing Error</h1>
                <p>Error: {str(e)}</p>
                <a href="/wizard/step3?doc_type={doc_type}&level={level}">Try Again</a>
            </div>
        """))

# ========== RESULT BY ID ==========
@router.get("/result/{analysis_id}")
async def show_result_by_id(analysis_id: str, request: Request):
    if analysis_id not in analysis_queue:
        return HTMLResponse(layout("Result Not Found", '''
            <div style="text-align: center; padding: 4rem 0;">
                <div style="font-size: 4rem; color: #fbbf24; margin-bottom: 1rem;">
                    <i class="fas fa-lightbulb"></i>
                </div>
                <h1 style="color: #0cc0df;">Result Expired</h1>
                <p style="color: #94a3b8; margin-bottom: 2rem;">This analysis result has expired or wasn't found.</p>
                <a href="/" class="btn" style="background: #0f172a; color: white; padding: 1rem 2rem; border-radius: 8px; text-decoration: none;">
                    <i class="fas fa-home"></i> Return Home
                </a>
            </div>
        '''))
    
    data = analysis_queue[analysis_id]
    
    if data["status"] != "complete":
        return HTMLResponse(layout("Processing", f'''
            <div style="text-align: center; padding: 4rem 0;">
                <div style="font-size: 4rem; color: #fbbf24; margin-bottom: 1rem;">
                    <i class="fas fa-lightbulb" style="background: #fbbf24;"></i>
                </div>
                <h1 style="color: #0cc0df;">Still Analyzing</h1>
                <p style="color: #94a3b8;">Your {get_analysis_type(data)} is being processed...</p>
                <div style="width: 100%; max-width: 400px; margin: 2rem auto;">
                    <div style="background: #1e293b; height: 8px; border-radius: 4px; overflow: hidden;">
                        <div style="background: #fbbf24; width: {data.get('progress', 0.5)*100}%; height: 100%; transition: width 0.5s;"></div>
                    </div>
                </div>
                <p style="color: #64748b;" id="status-message">{data.get('message', 'Working...')}</p>
                <meta http-equiv="refresh" content="2;url=/result/{analysis_id}">
            </div>
        '''))
    
    # Get the result text
    ai_text = data.get("result", "No result generated")
    is_mock = data.get("is_mock", False)
    
    # Determine analysis type for display
    if "repo_url" in data:
        # GitHub repository analysis
        return await show_github_result(data, ai_text, is_mock)
    elif "scan_type" in data:
        # Security analysis
        return await show_security_result(data, ai_text, is_mock)
    else:
        # Standard code/document analysis
        return await show_code_result(data, ai_text, is_mock)

def get_analysis_type(data: dict) -> str:
    """Return human-readable analysis type"""
    if "repo_url" in data:
        return "GitHub repository"
    elif "scan_type" in data:
        return f"Security scan ({data['scan_type']})"
    else:
        return data.get("doc_type", "Code").replace("_", " ").title()

async def show_github_result(data: dict, ai_text: str, is_mock: bool):
    """Display GitHub repository analysis results"""
    repo_url = data.get("repo_url", "")
    repo_name = repo_url.split("/")[-1] if repo_url else "Repository"
    file_count = data.get("file_count", 0)
    
    mock_badge = '''
    <div style="background: rgba(251, 191, 36, 0.1); border: 1px solid #fbbf24; border-radius: 8px; padding: 0.75rem; margin-bottom: 1.5rem; display: inline-block;">
        <span style="color: #fbbf24;"><i class="fas fa-flask"></i> Mock Mode - Add DEEPSEEK_API_KEY for real analysis</span>
    </div>
    ''' if is_mock else ''
    
    content = f'''
    <div style="max-width: 900px; margin: 0 auto;">
        <div style="text-align: center; margin-bottom: 2rem;">
            <div style="font-size: 3rem; color: #fbbf24; margin-bottom: 1rem;">
                <i class="fab fa-github"></i>
            </div>
            <h1 style="color: #fbbf24;">Repository Analysis Complete</h1>
            <p style="color: #94a3b8;">
                <strong>{repo_name}</strong> • {file_count} files analyzed
            </p>
            {mock_badge}
        </div>
        
        <div style="background: rgba(255,255,255,0.05); border-radius: 12px; padding: 2rem; margin-bottom: 2rem;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
                <h2 style="color: white; margin: 0;">Analysis Results</h2>
                <button onclick="copyText()" 
                        style="background: #fbbf24; color: #0f172a; border: none; padding: 0.5rem 1rem; border-radius: 6px; cursor: pointer; font-weight: bold;"
                        id="copy-btn">
                    <i class="fas fa-copy"></i> Copy
                </button>
            </div>
            
            <div id="ai-output" style="line-height: 1.6; color: #e2e8f0; white-space: pre-wrap; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;">
                {ai_text.replace(chr(10), '<br>')}
            </div>
        </div>
        
        <div style="display: flex; justify-content: center; gap: 1rem; margin-top: 2rem;">
            <a href="/analyze/github" class="btn" style="background: #0f172a; color: white; padding: 0.75rem 1.5rem; border-radius: 6px; text-decoration: none;">
                <i class="fab fa-github"></i> Analyze Another Repo
            </a>
            <a href="/" class="btn" style="background: #64748b; color: white; padding: 0.75rem 1.5rem; border-radius: 6px; text-decoration: none;">
                <i class="fas fa-home"></i> Dashboard
            </a>
        </div>
        
        <script>
        function copyText() {{
            const output = document.getElementById('ai-output');
            const text = output.innerText;
            
            navigator.clipboard.writeText(text).then(() => {{
                const btn = document.getElementById('copy-btn');
                btn.innerHTML = '<i class="fas fa-check"></i> Copied!';
                btn.style.background = '#10b981';
                btn.style.color = 'white';
                
                setTimeout(() => {{
                    btn.innerHTML = '<i class="fas fa-copy"></i> Copy';
                    btn.style.background = '#fbbf24';
                    btn.style.color = '#0f172a';
                }}, 2000);
            }});
        }}
        </script>
    </div>
    '''
    
    return HTMLResponse(layout(f"GitHub Analysis: {repo_name}", content))

async def show_security_result(data: dict, ai_text: str, is_mock: bool):
    """Display security scan results"""
    scan_type = data.get("scan_type", "full").title()
    threshold = data.get("threshold", "medium")
    
    mock_badge = '''
    <div style="background: rgba(251, 191, 36, 0.1); border: 1px solid #fbbf24; border-radius: 8px; padding: 0.75rem; margin-bottom: 1.5rem; display: inline-block;">
        <span style="color: #fbbf24;"><i class="fas fa-flask"></i> Mock Mode - Add DEEPSEEK_API_KEY for real security scanning</span>
    </div>
    ''' if is_mock else ''
    
    content = f'''
    <div style="max-width: 900px; margin: 0 auto;">
        <div style="text-align: center; margin-bottom: 2rem;">
            <div style="font-size: 3rem; color: #fbbf24; margin-bottom: 1rem;">
                <i class="fas fa-shield-alt"></i>
            </div>
            <h1 style="color: #fbbf24;">Security Scan Complete</h1>
            <p style="color: #94a3b8;">
                <strong>{scan_type} Audit</strong> • Threshold: {threshold}
            </p>
            {mock_badge}
        </div>
        
        <div style="background: rgba(255,255,255,0.05); border-radius: 12px; padding: 2rem; margin-bottom: 2rem;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
                <h2 style="color: white; margin: 0;">Vulnerability Report</h2>
                <button onclick="copyText()" 
                        style="background: #fbbf24; color: #0f172a; border: none; padding: 0.5rem 1rem; border-radius: 6px; cursor: pointer; font-weight: bold;"
                        id="copy-btn">
                    <i class="fas fa-copy"></i> Copy
                </button>
            </div>
            
            <div id="ai-output" style="line-height: 1.6; color: #e2e8f0; white-space: pre-wrap; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;">
                {ai_text.replace(chr(10), '<br>')}
            </div>
        </div>
        
        <div style="display: flex; justify-content: center; gap: 1rem; margin-top: 2rem;">
            <a href="/analyze/security" class="btn" style="background: #0f172a; color: white; padding: 0.75rem 1.5rem; border-radius: 6px; text-decoration: none;">
                <i class="fas fa-shield-alt"></i> New Security Scan
            </a>
            <a href="/" class="btn" style="background: #64748b; color: white; padding: 0.75rem 1.5rem; border-radius: 6px; text-decoration: none;">
                <i class="fas fa-home"></i> Dashboard
            </a>
        </div>
        
        <script>
        function copyText() {{
            const output = document.getElementById('ai-output');
            const text = output.innerText;
            
            navigator.clipboard.writeText(text).then(() => {{
                const btn = document.getElementById('copy-btn');
                btn.innerHTML = '<i class="fas fa-check"></i> Copied!';
                btn.style.background = '#10b981';
                btn.style.color = 'white';
                
                setTimeout(() => {{
                    btn.innerHTML = '<i class="fas fa-copy"></i> Copy';
                    btn.style.background = '#fbbf24';
                    btn.style.color = '#0f172a';
                }}, 2000);
            }});
        }}
        </script>
    </div>
    '''
    
    return HTMLResponse(layout(f"Security Audit Results", content))

async def show_code_result(data: dict, ai_text: str, is_mock: bool):
    """Display standard code/document analysis results"""
    doc_type = data.get("doc_type", "code").replace("_", " ").title()
    level = data.get("level", "professional").replace("_", " ").title()
    
    mock_badge = '''
    <div style="background: rgba(251, 191, 36, 0.1); border: 1px solid #fbbf24; border-radius: 8px; padding: 0.75rem; margin-bottom: 1.5rem; display: inline-block;">
        <span style="color: #fbbf24;"><i class="fas fa-flask"></i> Mock Mode - Add DEEPSEEK_API_KEY for real analysis</span>
    </div>
    ''' if is_mock else ''
    
    content = f'''
    <div style="max-width: 900px; margin: 0 auto;">
        <div style="text-align: center; margin-bottom: 2rem;">
            <div style="font-size: 3rem; color: #fbbf24; margin-bottom: 1rem;">
                <i class="fas fa-lightbulb"></i>
            </div>
            <h1 style="color: #0cc0df;">Code Analysis Complete</h1>
            <p style="color: #94a3b8;">
                <strong>{doc_type}</strong> • {level} level
            </p>
            {mock_badge}
        </div>
        
        <div style="background: rgba(255,255,255,0.05); border-radius: 12px; padding: 2rem; margin-bottom: 2rem;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
                <h2 style="color: white; margin: 0;">Analysis Results</h2>
                <button onclick="copyText()" 
                        style="background: #0cc0df; color: #0f172a; border: none; padding: 0.5rem 1rem; border-radius: 6px; cursor: pointer; font-weight: bold;"
                        id="copy-btn">
                    <i class="fas fa-copy"></i> Copy
                </button>
            </div>
            
            <div id="ai-output" style="line-height: 1.6; color: #e2e8f0; white-space: pre-wrap; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;">
                {ai_text.replace(chr(10), '<br>')}
            </div>
        </div>
        
        <div style="display: flex; justify-content: center; gap: 1rem; margin-top: 2rem;">
            <a href="/wizard" class="btn" style="background: #0f172a; color: white; padding: 0.75rem 1.5rem; border-radius: 6px; text-decoration: none;">
                <i class="fas fa-magic"></i> New Analysis
            </a>
            <a href="/" class="btn" style="background: #64748b; color: white; padding: 0.75rem 1.5rem; border-radius: 6px; text-decoration: none;">
                <i class="fas fa-home"></i> Dashboard
            </a>
        </div>
        
        <script>
        function copyText() {{
            const output = document.getElementById('ai-output');
            const text = output.innerText;
            
            navigator.clipboard.writeText(text).then(() => {{
                const btn = document.getElementById('copy-btn');
                btn.innerHTML = '<i class="fas fa-check"></i> Copied!';
                btn.style.background = '#10b981';
                btn.style.color = 'white';
                
                setTimeout(() => {{
                    btn.innerHTML = '<i class="fas fa-copy"></i> Copy';
                    btn.style.background = '#fbbf24';
                    btn.style.color = '#0f172a';
                }}, 2000);
            }});
        }}
        </script>
    </div>
    '''
    
    return HTMLResponse(layout(f"{doc_type} Analysis", content))

@router.post("/api/extract-text")
async def extract_text(file: UploadFile = File(...)):
    # Simple text extraction - expand based on file type
    if file.filename.endswith('.txt'):
        content = await file.read()
        return {"text": content.decode('utf-8', errors='ignore')}
    
    elif file.filename.endswith('.pdf'):
        # Use PyPDF2 or pdfplumber
        try:
            import PyPDF2
            import io
            content = await file.read()
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return {"text": text[:20000]}  # Limit to 20K chars
        except:
            return {"error": "PDF processing failed. Try converting to text first."}
    
    elif file.filename.endswith(('.doc', '.docx')):
        # For DOCX, you might need python-docx
        return {"error": "DOC/DOCX support coming soon. Save as PDF or text first."}
    
    return {"error": "Unsupported file type"}

async def process_document_background(analysis_id: str):
    data = analysis_queue[analysis_id]
    
    client = AsyncOpenAI(
        api_key=DEEPSEEK_API_KEY,  
        base_url="https://api.deepseek.com"
    )

    try:
        # 1. Pre-process document (limit size, clean)
        text = data["document_text"][:20000]  # 20K char limit for speed
        
        # 2. Smart prompt based on doc_type and level
        prompt_templates = {
            "legal": """Analyze this legal document for a {level}. Focus on:
1. Plain English translation
2. Hidden risks or unfair clauses
3. Rights vs responsibilities
4. Actionable next steps

Keep analysis under 500 words. No markdown.""",
            
            "medical": """Analyze this medical document for a {level}. Focus on:
1. Plain English explanation
2. Medical terms translated
3. Treatment implications
4. Questions to ask doctor

Keep analysis under 500 words. No markdown."""
        }
        
        prompt = prompt_templates.get(
            data["doc_type"], 
            "Analyze this document in plain English for a {level} audience."
        ).format(level=data["level"])
        
        # 3. Call DeepSeek with timeout
        import asyncio
        try:
            # Your DeepSeek API call here
            # Add timeout
            response = await asyncio.wait_for(
                deepseek.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": "You are a document analysis expert."},
                        {"role": "user", "content": f"{prompt}\n\nDOCUMENT:\n{text}"}
                    ],
                    max_tokens=1000
                ),
                timeout=30.0  # 30 second timeout
            )
            
            ai_text = response.choices[0].message.content
            
        except asyncio.TimeoutError:
            ai_text = "Analysis timed out. Document may be too complex or service busy. Try a shorter section."
        
        # 4. Store result
        data["result"] = ai_text
        data["status"] = "complete"
        
    except Exception as e:
        data["status"] = "error"
        data["error"] = str(e)

# Instead of complex parsing, use simple sections
def format_ai_response(ai_text: str, doc_type: str, level: str):
    # Just wrap in a clean div - parsing can fail
    return f'''
    <div style="background: rgba(255,255,255,0.05); border-radius: 12px; padding: 2rem; margin: 2rem 0;">
        <h3 style="color: #0cc0df; margin-top: 0;">
            <i class="fas fa-file-alt"></i> Analysis for {level.replace("_", " ").title()}
        </h3>
        <div style="line-height: 1.6; color: #f0f0f0; white-space: pre-wrap;">
            {ai_text}
        </div>
    </div>
    '''

# ========== FILE EXTRACTION API ==========
@router.post("/api/extract-code")
async def extract_code(file: UploadFile):
    """Extract code and technical content from uploaded files."""
    try:
        content = await file.read()
        filename = file.filename.lower()
        
        # ===== CODE FILES =====
        code_extensions = {
            '.py': 'Python',
            '.js': 'JavaScript', 
            '.ts': 'TypeScript',
            '.jsx': 'React JSX',
            '.tsx': 'React TSX',
            '.html': 'HTML',
            '.css': 'CSS',
            '.json': 'JSON',
            '.yaml': 'YAML',
            '.yml': 'YAML',
            '.md': 'Markdown',
            '.rst': 'reStructuredText',
            '.sql': 'SQL',
            '.sh': 'Shell Script',
            '.bash': 'Bash Script',
            '.rb': 'Ruby',
            '.go': 'Go',
            '.rs': 'Rust',
            '.php': 'PHP',
            '.java': 'Java',
            '.cpp': 'C++',
            '.c': 'C',
            '.h': 'C Header',
            '.cs': 'C#',
            '.swift': 'Swift',
            '.kt': 'Kotlin',
            '.tf': 'Terraform',
            '.dockerfile': 'Dockerfile',
            '.env': 'Environment Config',
            '.gitignore': 'Git Ignore',
            '.toml': 'TOML'
        }
        
        for ext, lang in code_extensions.items():
            if filename.endswith(ext) or ext in filename:
                try:
                    text = content.decode('utf-8', errors='ignore')
                    # Limit to reasonable size
                    if len(text) > 50000:
                        return {"text": text[:50000], "warning": f"File truncated (50K char limit)", "language": lang}
                    return {"text": text, "language": lang}
                except:
                    return {"error": f"Could not read {lang} file. Ensure UTF-8 encoding."}
        
        # ===== CONFIG / ENV FILES =====
        if filename.endswith(('.env', '.ini', '.cfg', '.conf')):
            try:
                text = content.decode('utf-8', errors='ignore')
                return {"text": text[:20000], "language": "Configuration"}
            except:
                return {"error": "Could not read config file."}
        
        # ===== PDF DOCUMENTATION =====
        if filename.endswith('.pdf') or file.content_type == 'application/pdf':
            try:
                import PyPDF2
                import io
                
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
                
                if pdf_reader.is_encrypted:
                    return {"error": "PDF is encrypted. Please provide unencrypted technical documentation."}
                
                if len(pdf_reader.pages) > 20:
                    return {"error": f"PDF has {len(pdf_reader.pages)} pages. Please extract the relevant section (1-5 pages)."}
                
                text = ""
                for i, page in enumerate(pdf_reader.pages):
                    if i >= 5:  # Limit to first 5 pages
                        text += f"\n[Documentation truncated after page 5. Total: {len(pdf_reader.pages)} pages]"
                        break
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n\n"
                
                if not text.strip():
                    return {"error": "PDF appears to be scanned/image-based. Please provide text-based technical documentation."}
                
                return {"text": text[:30000], "language": "Technical Documentation"}
                
            except ImportError:
                return {"error": "PDF library not installed. Run: pip install PyPDF2"}
            except Exception as e:
                return {"error": f"PDF processing failed: {str(e)}"}
        
        # ===== TEXT FILES =====
        if filename.endswith('.txt') or file.content_type == 'text/plain':
            try:
                text = content.decode('utf-8', errors='ignore')
                # Detect if it might be code
                code_indicators = ['def ', 'function(', 'import ', 'class ', '<?php', '#include', 'package ']
                language = "Plain Text"
                for indicator in code_indicators:
                    if indicator in text[:1000]:
                        language = "Code (detected)"
                        break
                return {"text": text[:50000], "language": language}
            except:
                return {"error": "Could not read text file. Ensure UTF-8 encoding."}
        
        return {"error": f"Unsupported file type: {file.filename}. Supported: code files (.py, .js, .json, etc.), PDF docs, config files."}
            
    except Exception as e:
        return {"error": f"File processing error: {str(e)}"}

# ========== ANALYSIS STATUS API ==========
@router.get("/api/analysis-status/{analysis_id}")
async def get_analysis_status(analysis_id: str):
    if analysis_id in analysis_queue:
        data = analysis_queue[analysis_id]
        return {
            "status": data["status"],
            "progress": data.get("progress", 0.1),
            "message": data.get("message", "Analyzing code..."),
            "error": data.get("error"),
            "doc_type": data.get("doc_type"),
            "level": data.get("level")
        }
    return {"status": "not_found", "error": "Analysis not found"}

# ========== BACKGROUND PROCESSING ==========
async def process_document_background(analysis_id: str):
    data = analysis_queue[analysis_id]
    
    try:
        # Update progress
        data["progress"] = 0.2
        data["message"] = "Parsing code structure..."
        await asyncio.sleep(0.5)
        
        # Extract and clean code/content
        text = data["document_text"][:12000]  # Larger limit for code
        line_count = len(text.split('\n'))
        
        # Update progress
        data["progress"] = 0.4
        data["message"] = f"Analyzing {line_count} lines with AI..."
        
        # Prepare prompt based on technical analysis type
        prompt_templates = {
            "github": """Analyze this CODEBASE for a {level} audience. Focus on:
1. PURPOSE: What does this codebase do? (High-level summary)
2. ARCHITECTURE: Key components and how they connect
3. TECH STACK: Languages, frameworks, dependencies
4. COMPLEXITY: Areas that need attention
5. ONBOARDING: What a new developer needs to know

Keep analysis under 500 words. Use bullet points. No markdown.""",
            
            "api": """Analyze this API documentation/code for a {level} audience. Focus on:
1. PURPOSE: What does this API do?
2. ENDPOINTS: Key operations and their purpose
3. AUTH: How authentication works
4. DATA FORMATS: Request/response structure
5. USAGE: Common implementation patterns

Keep analysis under 500 words. Use bullet points. No markdown.""",
            
            "legacy": """Analyze this LEGACY CODE for a {level} audience. Focus on:
1. PURPOSE: What was this code intended to do?
2. MODERNIZATION: How to approach rewriting
3. TECHNICAL DEBT: Specific problems to address
4. DEPENDENCIES: What it relies on
5. RISKS: Potential issues when modifying

Keep analysis under 500 words. Use bullet points. No markdown.""",
            
            "security": """Perform a SECURITY REVIEW of this code for a {level} audience. Focus on:
1. VULNERABILITIES: Specific security issues found
2. INPUT VALIDATION: How user input is handled
3. AUTH/PERMISSIONS: Access control concerns
4. SECURE CODING: Best practices to implement
5. PRIORITY: What to fix immediately

Keep analysis under 500 words. Use bullet points. No markdown.""",
            
            "dependency": """Analyze these DEPENDENCIES for a {level} audience. Focus on:
1. PURPOSE: Why each major dependency is used
2. VERSIONS: Outdated or vulnerable packages
3. ALTERNATIVES: Modern replacement options
4. CONFLICTS: Potential version conflicts
5. SIZE: Impact on bundle/project size

Keep analysis under 500 words. Use bullet points. No markdown.""",
            
            "functions": """Analyze this FUNCTION/CODE for a {level} audience. Focus on:
1. PURPOSE: Input → Output transformation
2. COMPLEXITY: Cyclomatic complexity, nesting depth
3. EDGE CASES: Missing error handling
4. PERFORMANCE: Potential bottlenecks
5. REFACTORING: How to improve readability

Keep analysis under 500 words. Use bullet points. No markdown.""",
            
            "config": """Analyze this CONFIGURATION for a {level} audience. Focus on:
1. SYSTEM: What this configures (deployment, CI/CD, app settings)
2. KEY SETTINGS: Critical parameters and their effects
3. SECURITY: Exposed secrets, permissions issues
4. OPTIMIZATION: Recommended changes
5. ENVIRONMENT: Dev vs prod differences

Keep analysis under 500 words. Use bullet points. No markdown.""",
            
            "documentation": """Analyze this TECHNICAL DOCUMENTATION for a {level} audience. Focus on:
1. TOPIC: What this document describes
2. CLARITY: Well-explained vs confusing sections
3. COMPLETENESS: What's missing or outdated
4. EXAMPLES: Quality of code examples
5. IMPLEMENTATION: How to use this documentation

Keep analysis under 500 words. Use bullet points. No markdown."""
        }
        
        prompt = prompt_templates.get(
            data["doc_type"],
            """Analyze this TECHNICAL CONTENT for a {level} audience. Provide:
1. Clear summary of what this does
2. Key technical concepts explained simply
3. Actionable insights or recommendations

Keep analysis under 500 words. Use bullet points. No markdown."""
        ).format(level=data["level"])
        
        # Add specific questions if provided
        if data["specific_questions"]:
            prompt += f"\n\nUSER-SPECIFIC QUESTIONS:\n{data['specific_questions']}"
        
        # Add content
        prompt += f"\n\nCONTENT TO ANALYZE:\n{text}"
        
        # Update progress
        data["progress"] = 0.6
        data["message"] = "Processing with AI engine..."
        
        # ========== API CALL SECTION ==========
        try:
            # Check for API key first
            api_key = os.getenv("DEEPSEEK_API_KEY", "")
            
            if not api_key or api_key.startswith("your-"):
                # Provide mock response for technical content
                ai_text = f"""🔧 TECHNICAL ANALYSIS (API Key Required)

**Analysis Type:** {data['doc_type'].title()}
**Audience Level:** {data['level'].title()}

📋 **KEY FINDINGS:**
• Code structure appears complex - consider modularization
• Dependencies need version audit
• Error handling could be improved
• Documentation gaps identified

🎯 **RECOMMENDATIONS:**
1. Add DeepSeek API key to .env file
2. Get key from platform.deepseek.com
3. Restart for full AI-powered analysis

*This is a placeholder. Real AI analysis requires an API key.*"""
                data["is_mock"] = True
                
            else:
                # Real API call with technical system prompt
                from openai import AsyncOpenAI
                
                client = AsyncOpenAI(
                    api_key=api_key,
                    base_url="https://api.deepseek.com"
                )
                
                response = await asyncio.wait_for(
                    client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[
                            {"role": "system", "content": "You are a senior software engineer and technical architect. Analyze code and technical documentation clearly and practically."},
                            {"role": "user", "content": prompt}
                        ],
                        max_tokens=1000,
                        temperature=0.3
                    ),
                    timeout=35.0
                )
                
                ai_text = response.choices[0].message.content
                data["is_mock"] = False
                
        except asyncio.TimeoutError:
            ai_text = """⏱️ **ANALYSIS TIMED OUT**

The code analysis took too long. 

**TRY THESE INSTEAD:**
1. Analyze a single file instead of multiple
2. Select a smaller function or module
3. Use a more specific question

**TECHNICAL LIMIT:** Complex codebases may need chunking."""
            data["is_error"] = True
            data["error_type"] = "timeout"
            
        except Exception as api_error:
            error_msg = str(api_error)
            if "401" in error_msg or "authentication" in error_msg.lower():
                ai_text = f"""🔑 **API KEY ERROR**

{error_msg}

**ACTION REQUIRED:**
1. Get your DeepSeek API key
2. Add it to .env file as DEEPSEEK_API_KEY=your_key
3. Restart the application"""
            else:
                ai_text = f"""⚠️ **AI SERVICE ERROR**

{error_msg}

**TROUBLESHOOTING:**
1. Check internet connection
2. Verify API key is valid
3. Try again in a few minutes"""
            data["is_error"] = True
            data["error_type"] = "api_error"
        
        # Update progress
        data["progress"] = 0.8
        data["message"] = "Formatting technical insights..."
        await asyncio.sleep(0.5)
        
        # Store result
        data["result"] = ai_text
        data["status"] = "complete"
        data["progress"] = 1.0
        data["message"] = "Analysis complete!"
        
        # Clean up old analyses (keep last 100)
        if len(analysis_queue) > 100:
            oldest_ids = sorted(analysis_queue.keys(), 
                              key=lambda k: analysis_queue[k].get("created_at", 0))[:50]
            for old_id in oldest_ids:
                if old_id != analysis_id:
                    analysis_queue.pop(old_id, None)
        
    except Exception as e:
        data["status"] = "error"
        data["error"] = str(e)
        data["message"] = f"System Error: {str(e)}"
        data["result"] = f"""❌ **SYSTEM ERROR**

**Error Details:**
{str(e)}

**Suggested Fixes:**
1. Refresh the page
2. Try analyzing different content
3. Check application logs
4. Restart the server if issue persists"""

@router.post("/process-upload")
async def process_upload(
    doc_type: str = Form(...),
    level: str = Form(...),
    file: UploadFile = File(...),
    specific_questions: str = Form("")
):
    """Process uploaded code/technical file"""
    # 1. Extract code/content from file
    result = await extract_code(file)  # Changed to extract_code
    
    if "error" in result:
        return HTMLResponse(layout("Upload Error", f"""
            <div style="text-align: center; padding: 4rem;">
                <h1>⚠️ File Processing Error</h1>
                <p style="color: #dc2626;">{result['error']}</p>
                <div style="background: #1f222a; padding: 1rem; border-radius: 8px; margin: 2rem auto; max-width: 600px;">
                    <p style="margin: 0; color: #9ca3af;"><strong>Supported formats:</strong></p>
                    <p style="color: #9ca3af;">Code files (.py, .js, .json, .yml, .go, .rs, .java, .cpp, etc.)</p>
                    <p style="color: #9ca3af;">Technical documentation (PDF, .txt, .md)</p>
                    <p style="color: #9ca3af;">Configuration files (.env, .conf, .ini)</p>
                </div>
                <a href="/wizard/step3?doc_type={doc_type}&level={level}" role="button">← Try Again</a>
            </div>
        """))
    
    text = result.get("text", "")
    language = result.get("language", "Unknown")
    
    if not text:
        return HTMLResponse(layout("Upload Error", f"""
            <div style="text-align: center; padding: 4rem;">
                <h1>📄 No Content Extracted</h1>
                <p>The file appears to be empty or in an unsupported format.</p>
                <p style="color: #6b7280;">Detected type: {language}</p>
                <a href="/wizard/step3?doc_type={doc_type}&level={level}" role="button">← Try Again</a>
            </div>
        """))
    
    # 2. Call process_document directly with extracted code
    return await process_document(
        doc_type=doc_type,
        level=level,
        document_text=text,
        specific_questions=specific_questions
    )

# ===== Analyze GitHub =====
@router.get("/analyze/github")
async def github_analyzer_page(request: Request):
    """GitHub repository analysis input page"""
    return templates.TemplateResponse("github_analyzer.html", {
        "request": request,
        "title": "Analyze GitHub Repository"
    })

# ===== Process GitHub =====
@router.post("/process-github")
async def process_github(
    repo_url: str = Form(...),
    branch: str = Form("main"),
    include_patterns: str = Form("*.py,*.js,*.json,*.md,*.yml"),
    specific_questions: str = Form(""),
    level: str = Form("professional"),
    doc_type: str = Form("github")  # Keep for compatibility
):
    """Clone and analyze a GitHub repository"""
    analysis_id = str(uuid.uuid4())
    
    # Store in queue
    analysis_queue[analysis_id] = {
        "repo_url": repo_url,
        "branch": branch,
        "include_patterns": include_patterns,
        "specific_questions": specific_questions,
        "level": level,
        "status": "processing",
        "progress": 0.1,
        "message": "Cloning repository...",
        "created_at": time.time()
    }
    
    # Start background task
    asyncio.create_task(analyze_github_background(analysis_id))
    
    # Return loading page (reuse your existing loading template)
    return await loading_response(analysis_id)

# ========== SECURITY ANALYSIS ==========
@router.get("/analyze/security")
async def security_analyzer_page(request: Request):
    """Security-focused code analysis"""
    return templates.TemplateResponse("security_analyzer.html", {
        "request": request,
        "title": "Security Audit"
    })

@router.post("/process-security")
async def process_security(
    code: str = Form(...),
    scan_type: str = Form("full"),
    threshold: str = Form("medium"),
    specific_questions: str = Form("")
):
    """Analyze code for security vulnerabilities"""
    analysis_id = str(uuid.uuid4())
    
    # Store in queue
    analysis_queue[analysis_id] = {
        "code": code[:20000],  # Limit size
        "scan_type": scan_type,
        "threshold": threshold,
        "specific_questions": specific_questions,
        "status": "processing",
        "progress": 0.1,
        "message": "Initializing security scan...",
        "created_at": time.time()
    }
    
    # Start background task
    asyncio.create_task(analyze_security_background(analysis_id))
    
    # Return loading page
    return await security_loading_response(analysis_id)

@router.post("/process-security-upload")
async def process_security_upload(
    file: UploadFile = File(...),
    scan_type: str = Form("full"),
    threshold: str = Form("medium"),
    specific_questions: str = Form("")
):
    """Upload and scan file for security issues"""
    # Extract code from file
    result = await extract_code(file)
    
    if "error" in result:
        return HTMLResponse(layout("Upload Error", f"""
            <div style="text-align: center; padding: 4rem;">
                <h1 style="color: #dc2626;">⚠️ Upload Error</h1>
                <p>{result['error']}</p>
                <a href="/analyze/security">← Try Again</a>
            </div>
        """))
    
    code = result.get("text", "")
    language = result.get("language", "Unknown")
    
    if not code:
        return HTMLResponse(layout("Upload Error", f"""
            <div style="text-align: center; padding: 4rem;">
                <h1 style="color: #dc2626;">📄 No Code Found</h1>
                <p>The file appears to be empty or unreadable.</p>
                <a href="/analyze/security">← Try Again</a>
            </div>
        """))
    
    # Process the extracted code
    return await process_security(
        code=code,
        scan_type=scan_type,
        threshold=threshold,
        specific_questions=specific_questions
    )

@router.post("/process-github-security")
async def process_github_security(
    repo_url: str = Form(...),
    scan_type: str = Form("full"),
    threshold: str = Form("medium"),
    branch: str = Form("main"),
    specific_questions: str = Form("")
):
    """Clone and scan a GitHub repository for security issues"""
    analysis_id = str(uuid.uuid4())
    
    analysis_queue[analysis_id] = {
        "repo_url": repo_url,
        "scan_type": scan_type,
        "threshold": threshold,
        "branch": branch,
        "specific_questions": specific_questions,
        "status": "processing",
        "progress": 0.1,
        "message": "Cloning repository for security scan...",
        "created_at": time.time()
    }
    
    asyncio.create_task(analyze_github_security_background(analysis_id))
    
    return await security_loading_response(analysis_id)

async def analyze_security_background(analysis_id: str):
    """Background task for security analysis of code snippets"""
    data = analysis_queue[analysis_id]
    
    try:
        data["progress"] = 0.3
        data["message"] = "Analyzing code patterns..."
        
        code = data["code"]
        scan_type = data["scan_type"]
        threshold = data["threshold"]
        
        # Build security-focused prompt
        security_prompts = {
            "full": """Perform a comprehensive security audit of this code. Focus on:
1. HARDCODED SECRETS: API keys, passwords, tokens, credentials
2. INJECTION VULNERABILITIES: SQL, NoSQL, command injection
3. AUTHENTICATION ISSUES: Weak password handling, session management
4. INPUT VALIDATION: Missing sanitization, unsafe deserialization
5. DEPENDENCY RISKS: Outdated or vulnerable libraries
6. CRYPTOGRAPHY: Weak algorithms, improper implementation
7. ERROR HANDLING: Information disclosure in error messages
8. ACCESS CONTROL: Missing permission checks

For each finding, include:
- SEVERITY: Critical/High/Medium/Low
- LOCATION: Line number or code snippet
- DESCRIPTION: What's the issue?
- FIX: How to remediate

Threshold: Show {threshold} severity and above.""",
            
            "secrets": """Scan this code for HARDCODED SECRETS and SENSITIVE DATA:
- API keys, tokens, passwords
- AWS/GCP/Azure credentials
- Database connection strings
- Private keys (RSA, SSH)
- JWT secrets, OAuth tokens
- Encryption keys

Report each finding with severity and remediation.""",
            
            "dependencies": """Analyze dependencies for SECURITY VULNERABILITIES:
- Outdated packages with known CVEs
- Deprecated or unmaintained libraries
- Version conflicts with security implications
- Risky import patterns

Focus on high and critical severity issues."""
        }
        
        prompt = security_prompts.get(scan_type, security_prompts["full"])
        prompt = prompt.format(threshold=threshold)
        
        if data["specific_questions"]:
            prompt += f"\n\nSPECIFIC QUESTIONS:\n{data['specific_questions']}"
        
        prompt += f"\n\nCODE TO ANALYZE:\n```\n{code[:15000]}\n```"
        
        data["progress"] = 0.6
        data["message"] = "Running security scans..."
        
        # Call AI
        api_key = os.getenv("DEEPSEEK_API_KEY")
        
        if not api_key or api_key.startswith("your-"):
            # Mock security response
            ai_text = f"""🔒 **Security Scan Results** (Mock Mode)

**Scan Type:** {scan_type.title()}
**Threshold:** {threshold.title()}

⚠️ **CRITICAL FINDINGS:**
1. Hardcoded API key detected (line ~12)
   - `sk_test_4eC39HqLyjWDarjtT1zdp7dc`
   - **Fix:** Use environment variables
   - **Severity:** Critical

2. SQL injection vulnerability (line ~45)
   - Raw string interpolation in query
   - **Fix:** Use parameterized queries
   - **Severity:** Critical

🔴 **HIGH SEVERITY:**
• Weak password policy detected
• Missing input validation on user form

🟠 **MEDIUM SEVERITY:**
• Outdated dependency: requests v2.25.1 (CVE-2023-1234)
• Verbose error messages exposing path

📋 **RECOMMENDATIONS:**
1. Add .env file for secrets
2. Implement prepared statements
3. Update dependencies
4. Add input sanitization

*Add DEEPSEEK_API_KEY to .env for real security scanning.*
"""
            data["is_mock"] = True
        else:
            from openai import AsyncOpenAI
            
            client = AsyncOpenAI(api_key=api_key, base_url="https://api.deepseek.com")
            
            response = await asyncio.wait_for(
                client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": "You are a senior application security engineer. Identify real vulnerabilities with practical fixes."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1500,
                    temperature=0.2
                ),
                timeout=45.0
            )
            
            ai_text = response.choices[0].message.content
            data["is_mock"] = False
        
        data["result"] = ai_text
        data["status"] = "complete"
        data["progress"] = 1.0
        data["message"] = "Security scan complete!"
        
    except Exception as e:
        data["status"] = "error"
        data["error"] = str(e)
        data["message"] = f"Security scan failed: {str(e)}"

async def analyze_github_security_background(analysis_id: str):
    """Background task for security scanning GitHub repos"""
    data = analysis_queue[analysis_id]
    
    temp_dir = None
    try:
        data["progress"] = 0.2
        data["message"] = f"Cloning {data['repo_url'].split('/')[-1]}..."
        
        temp_dir = tempfile.mkdtemp()
        
        # Shallow clone for speed
        repo = git.Repo.clone_from(
            data['repo_url'],
            temp_dir,
            branch=data['branch'],
            depth=1
        )
        
        data["progress"] = 0.4
        data["message"] = "Scanning for sensitive files and secrets..."
        
        # Collect all relevant files
        files = []
        secret_patterns = [
            '*.key', '*.pem', '*.p12', '*.pfx',
            '.env', '.env.*', 'secrets.*',
            'id_rsa', 'id_dsa', '*.keystore',
            'credentials.json', 'service-account.json'
        ]
        
        code_extensions = ['.py', '.js', '.php', '.go', '.rs', '.java', '.cpp', '.c', '.rb']
        
        for root, dirs, filenames in os.walk(temp_dir):
            if '.git' in dirs:
                dirs.remove('.git')
            
            for file in filenames:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, temp_dir)
                
                # Check if it's a secret file
                is_secret = any(Path(file_path).match(p) for p in secret_patterns)
                
                # Check if it's code
                is_code = any(file.endswith(ext) for ext in code_extensions)
                
                if is_secret or is_code:
                    try:
                        with open(file_path, 'r', errors='ignore') as f:
                            content = f.read(5000)  # First 5000 chars
                        
                        files.append({
                            "path": rel_path,
                            "content": content,
                            "is_secret": is_secret,
                            "size": os.path.getsize(file_path)
                        })
                    except:
                        pass
        
        data["progress"] = 0.6
        data["message"] = f"Analyzing {len(files)} files for vulnerabilities..."
        
        # Sort by secret files first, then code files
        files.sort(key=lambda x: (not x['is_secret'], x.get('size', 0)))
        files = files[:30]  # Limit
        
        # Build prompt with file samples
        file_samples = []
        for f in files[:10]:
            file_samples.append(f"File: {f['path']}\n{f['content'][:800]}...")
        
        prompt = f"""Perform a security audit of this GitHub repository.

Repository: {data['repo_url']}
Branch: {data['branch']}
Scan Type: {data['scan_type']}
Severity Threshold: {data['threshold']}

FILES ANALYZED:
{chr(10).join(file_samples)}

Focus on:
1. Hardcoded secrets and credentials
2. Security misconfigurations
3. Vulnerable code patterns
4. Dependency issues (if package files found)
5. Exposure of sensitive information

For each finding, include severity and remediation.

{data['specific_questions']}
"""
        
        data["progress"] = 0.8
        data["message"] = "Generating security report..."
        
        # Call AI (same pattern as above)
        api_key = os.getenv("DEEPSEEK_API_KEY")
        
        if not api_key or api_key.startswith("your-"):
            ai_text = f"""🔐 **GitHub Security Audit** (Mock Mode)

**Repository:** {data['repo_url'].split('/')[-1]}
**Files Scanned:** {len(files)}
**Scan Type:** {data['scan_type']}

🚨 **CRITICAL ISSUES FOUND:**
1. **Exposed .env file** - Contains database credentials
   - File: `.env.example`
   - Risk: Credential template shows structure
   - Fix: Remove from public repo, add to .gitignore

2. **Hardcoded test API key**
   - Found in 3 files
   - Pattern: `sk_test_`, `pk_test_`
   - Fix: Use environment variables

🔴 **HIGH RISK:**
• Outdated dependencies with known CVEs
• Missing CSRF protection in forms
• SQL query string concatenation

📊 **SUMMARY:**
- Critical: 2
- High: 4  
- Medium: 7
- Low: 12

**Next Steps:** Add DEEPSEEK_API_KEY for detailed vulnerability analysis.
"""
            data["is_mock"] = True
        else:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=api_key, base_url="https://api.deepseek.com")
            
            response = await asyncio.wait_for(
                client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": "You are a DevSecOps engineer. Find real security issues in code."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1800,
                    temperature=0.2
                ),
                timeout=60.0
            )
            
            ai_text = response.choices[0].message.content
            data["is_mock"] = False
        
        data["result"] = ai_text
        data["status"] = "complete"
        data["progress"] = 1.0
        data["message"] = "Security audit complete!"
        data["file_count"] = len(files)
        
    except Exception as e:
        data["status"] = "error"
        data["error"] = str(e)
        data["message"] = f"Security audit failed: {str(e)}"
    finally:
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)

async def security_loading_response(analysis_id: str):
    """Return loading page for security scans"""
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Security Scan in Progress</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: #000;
                color: #fff;
                margin: 0;
                padding: 0;
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }}
            .container {{
                max-width: 600px;
                text-align: center;
                padding: 3rem;
            }}
            .shield {{
                font-size: 4rem;
                color: #dc2626;
                margin-bottom: 1rem;
                animation: pulse 2s infinite;
            }}
            @keyframes pulse {{
                0% {{ opacity: 1; }}
                50% {{ opacity: 0.6; }}
                100% {{ opacity: 1; }}
            }}
            .spinner {{
                width: 50px;
                height: 50px;
                border: 3px solid #374151;
                border-top-color: #dc2626;
                border-radius: 50%;
                animation: spin 1s linear infinite;
                margin: 2rem auto;
            }}
            @keyframes spin {{
                to {{ transform: rotate(360deg); }}
            }}
            h1 {{ color: #dc2626; margin-bottom: 1rem; }}
            p {{ color: #9ca3af; margin-bottom: 2rem; }}
            .status-box {{
                background: rgba(220, 38, 38, 0.1);
                border-left: 4px solid #dc2626;
                padding: 1rem;
                border-radius: 4px;
                margin-top: 2rem;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="shield">
                <i class="fas fa-shield-alt"></i>
            </div>
            
            <h1>Security Scan in Progress</h1>
            <p id="status">Initializing security scanner...</p>
            
            <div class="spinner"></div>
            
            <div class="status-box">
                <p style="margin: 0; color: #dc2626;">
                    <i class="fas fa-info-circle"></i>
                    <span id="tip">Scanning for hardcoded secrets and vulnerabilities...</span>
                </p>
            </div>
        </div>
        
        <script>
            const analysisId = "{analysis_id}";
            
            function checkProgress() {{
                fetch('/api/analysis-status/' + analysisId)
                    .then(r => r.json())
                    .then(data => {{
                        if (data.status === 'complete') {{
                            window.location.href = '/result/' + analysisId;
                        }} else if (data.status === 'error') {{
                            window.location.href = '/error?message=' + encodeURIComponent(data.error);
                        }} else {{
                            if (data.message) {{
                                document.getElementById('status').textContent = data.message;
                            }}
                            setTimeout(checkProgress, 1000);
                        }}
                    }})
                    .catch(() => setTimeout(checkProgress, 2000));
            }}
            
            setTimeout(checkProgress, 1000);
        </script>
    </body>
    </html>
    '''
    return HTMLResponse(html)

@router.get("/document-wizard-home")
async def docudecipher_home(request: Request):
    """DocuDecipher landing page (temporary route name)"""
    return templates.TemplateResponse("document_wizard_home.html", {
        "request": request,
        "title": "DocuDecipher - Code Analysis Platform"
    })

# ===== Functions ======
async def analyze_github_background(analysis_id: str):
    """Background task for GitHub analysis"""
    data = analysis_queue[analysis_id]
    
    temp_dir = None
    try:
        # Update progress
        data["progress"] = 0.2
        data["message"] = f"Cloning {data['repo_url'].split('/')[-1]}..."
        
        # Create temp directory
        temp_dir = tempfile.mkdtemp()
        
        # Clone repository
        repo = git.Repo.clone_from(
            data['repo_url'], 
            temp_dir,
            branch=data['branch'],
            depth=1  # Shallow clone for speed
        )
        
        data["progress"] = 0.4
        data["message"] = "Analyzing repository structure..."
        
        # Parse include patterns
        patterns = [p.strip() for p in data['include_patterns'].split(',')]
        
        # Collect files
        files = []
        total_size = 0
        
        for root, dirs, filenames in os.walk(temp_dir):
            # Skip .git directory
            if '.git' in dirs:
                dirs.remove('.git')
            
            for file in filenames:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, temp_dir)
                
                # Check if file matches patterns
                if any(Path(file_path).match(p) for p in patterns):
                    try:
                        size = os.path.getsize(file_path)
                        total_size += size
                        
                        # Read first 3000 chars of each file
                        with open(file_path, 'r', errors='ignore') as f:
                            content = f.read(3000)
                        
                        files.append({
                            "path": rel_path,
                            "content": content,
                            "size": size,
                            "extension": os.path.splitext(file)[1]
                        })
                    except Exception as e:
                        files.append({
                            "path": rel_path,
                            "error": str(e)
                        })
        
        # Sort by size (smallest first) and limit
        files.sort(key=lambda x: x.get('size', 0))
        files = files[:30]  # Analyze top 30 files
        
        data["progress"] = 0.6
        data["message"] = f"Analyzing {len(files)} files with AI..."
        
        # Build prompt for repository analysis
        file_summaries = []
        for f in files[:15]:  # Limit for token usage
            file_summaries.append(f"File: {f['path']}\n{f['content'][:1000]}...")
        
        file_context = "\n\n".join(file_summaries)
        
        prompt = f"""Analyze this GitHub repository for a {data['level']} audience.

Repository: {data['repo_url']}
Branch: {data['branch']}
Files analyzed: {len(files)} key files

Please provide:
1. PROJECT OVERVIEW: What does this codebase do?
2. TECH STACK: Languages, frameworks, key dependencies
3. ARCHITECTURE: Main components and how they connect
4. COMPLEXITY: Areas that need attention
5. ONBOARDING: What a new developer needs to know

{data['specific_questions']}

FILE SAMPLES:
{file_context}

Keep analysis under 800 words. Use bullet points."""
        
        # Call AI (reuse your existing DeepSeek logic)
        api_key = os.getenv("DEEPSEEK_API_KEY")
        
        if not api_key or api_key.startswith("your-"):
            ai_text = f"""📦 **Repository Analysis (Mock)**

**Repository:** {data['repo_url'].split('/')[-1]}
**Files Analyzed:** {len(files)} files
**Total Size:** {total_size // 1024} KB

**🔧 Tech Stack Detected:**
• Python (primary)
• FastAPI/Flask likely
• JavaScript for frontend

**🏗️ Architecture:**
• Modular structure observed
• API routes in dedicated files
• Templates separated from logic

**🎯 Recommendations:**
1. Add DeepSeek API key for full analysis
2. Repository cloned successfully
3. {len(files)} files ready for deep inspection

*This is a placeholder. Add DEEPSEEK_API_KEY to .env for real AI analysis.*
"""
            data["is_mock"] = True
        else:
            # Your existing DeepSeek API call here
            from openai import AsyncOpenAI
            
            client = AsyncOpenAI(api_key=api_key, base_url="https://api.deepseek.com")
            
            response = await asyncio.wait_for(
                client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": "You are a senior software engineer analyzing codebases."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1500,
                    temperature=0.3
                ),
                timeout=45.0
            )
            
            ai_text = response.choices[0].message.content
            data["is_mock"] = False
        
        # Store result
        data["result"] = ai_text
        data["status"] = "complete"
        data["progress"] = 1.0
        data["message"] = "Analysis complete!"
        data["file_count"] = len(files)
        
    except git.exc.GitCommandError as e:
        data["status"] = "error"
        data["error"] = f"Git error: {str(e)}"
        data["message"] = "Failed to clone repository. Check URL and visibility."
    except Exception as e:
        data["status"] = "error"
        data["error"] = str(e)
        data["message"] = f"Analysis failed: {str(e)}"
    finally:
        # Clean up temp directory
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)

async def process_document_internal(doc_type, level, text, specific_questions):
    """Process code/technical content with AI analysis"""
    
    analysis_id = str(uuid.uuid4())
    
    analysis_queue[analysis_id] = {
        "doc_type": doc_type,
        "level": level,
        "document_text": text[:15000],
        "specific_questions": specific_questions,
        "status": "processing",
        "created_at": time.time(),
        "progress": 0.1,
        "message": "Initializing code analysis..."
    }
    
    asyncio.create_task(process_document_background(analysis_id))
    
    max_wait = 60
    wait_interval = 0.5
    
    for _ in range(int(max_wait / wait_interval)):
        await asyncio.sleep(wait_interval)
        
        if analysis_id in analysis_queue:
            data = analysis_queue[analysis_id]
            
            if data["status"] == "complete":
                return {
                    "status": "complete",
                    "summary": data.get("result", "No analysis generated"),
                    "analysis_id": analysis_id,
                    "is_mock": data.get("is_mock", False),
                    "is_error": data.get("is_error", False)
                }
            elif data["status"] == "error":
                return {
                    "status": "error",
                    "summary": f"Analysis failed: {data.get('error', 'Unknown error')}"
                }
    
    return {
        "status": "timeout",
        "summary": "Analysis timed out. Try a smaller code sample or more specific question."
    }