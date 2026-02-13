# routes/auth.py - HTTP ROUTES ONLY

from fastapi import Form, Request
from fastapi.responses import RedirectResponse
from auth.magic_links import generate_magic_link
from shared.auth import store_magic_token
from fastapi import APIRouter
from fastapi.templating import Jinja2Templates
from shared.auth import verify_magic_link

import urllib.parse

templates = Jinja2Templates(directory="templates")
router = APIRouter()

# ====== Login =====
@router.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
async def login_request(email: str = Form(...)):
    """Clean route - delegates to business logic."""
    
    # Generate magic link
    token = generate_magic_link(email)
    
    # Store token
    print(f"\n2️⃣ ATTEMPTING TO STORE TOKEN...")
    if token:
        try:
            stored = store_magic_token(email, token)
            print(f"   Storage result: {stored}")
        except Exception as e:
            print(f"   ❌ Storage failed: {e}")
    else:
        print(f"   ⚠️ No token to store")
    
    print(f"\n3️⃣ REDIRECTING TO CHECK-EMAIL PAGE")
    print("=" * 60)
    return RedirectResponse(f"/check-email?email={email}", status_code=303)

# ===== Logout ======
@router.get("/logout")
async def logout():
    response = RedirectResponse("/")
    response.delete_cookie(key="session")
    return response

# ===== Check Email =====
@router.get("/check-email")
async def check_email(request: Request, email: str):
    return templates.TemplateResponse("check_email.html", {
        "request": request,
        "email": email
    })

# ===== Auth =====
@router.get("/auth")
async def auth_callback(token: str):
    print(f"🔐 AUTH ROUTE - Raw token param: {repr(token)}...")
    print(f"🔐 Token length: {len(token)}")
    print(f"🔐 Token hex part: {token[6:]}")
    
    try:
        
        # Use mark_used=False so dashboard can also verify it
        email = verify_magic_link(token)
        print(f"🔐 verify_magic_link returned: {repr(email)}")

        if email:
            print(f"🔐 SUCCESS! Logging in: {email}")

            encoded_token = urllib.parse.quote(token)
            print(f"🔐 Encoded cookie token: {repr(encoded_token)}")
            print(f"🔐 Encoded length: {len(encoded_token)}")

            response = RedirectResponse("/dashboard")
            response.set_cookie(key="session", value=encoded_token, httponly=True, secure=False, max_age=86400, path="/")
            return response
        else:
            print(f"🔐 Token invalid or already used")
            return RedirectResponse("/login?error=invalid_token")
            
    except Exception as e:
        print(f"🔐 ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return RedirectResponse("/login?error=exception")