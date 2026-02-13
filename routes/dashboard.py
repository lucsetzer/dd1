from fastapi import Request, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from shared.auth import verify_magic_link
from fastapi import APIRouter
from datetime import datetime

import urllib.parse
import sqlite3

templates = Jinja2Templates(directory="templates")

router = APIRouter()

# ===== Frontpage =====
@router.get("/")
async def root(request: Request):
    return templates.TemplateResponse("frontpage.html", {"request": request})

# ===== Dashboard =====
@router.get("/dashboard")
async def dashboard(request: Request, session: str = Cookie(default=None)):
    print("=" * 60)
    print("🚪 DASHBOARD ROUTE ENTERED")
    
    if not session:
        return RedirectResponse("/login")
    
    # Get user email from session
    email = verify_magic_link(session, mark_used=False)
    
    if not email:
        return RedirectResponse("/login")
    
    # ===== MONTHLY CREDIT RESET =====
    # This runs every time user visits dashboard
    try:
        conn = sqlite3.connect('bank.db')
        cursor = conn.cursor()
        
        # Check if user exists in user_usage table
        cursor.execute("SELECT email FROM user_usage WHERE email = ?", (email,))
        user = cursor.fetchone()
        
        if not user:
            # New user - give them 5 free credits
            cursor.execute("""
                INSERT INTO user_usage (email, analyses_used, analyses_limit, reset_date, subscription_status)
                VALUES (?, 0, 5, DATE('now'), 'free')
            """, (email,))
            conn.commit()
            print(f"✅ New user created: {email} - 5 free credits")
        else:
            # Existing user - check if we need to reset monthly credits
            cursor.execute("""
                SELECT reset_date, subscription_status, analyses_limit 
                FROM user_usage WHERE email = ?
            """, (email,))
            
            reset_date_str, subscription_status, analyses_limit = cursor.fetchone()
            
            # Only reset free users
            if subscription_status == 'free':
                today = datetime.now().date()
                reset_date = datetime.strptime(reset_date_str, '%Y-%m-%d').date()
                
                # If last reset was before this month, reset usage
                if reset_date.year < today.year or reset_date.month < today.month:
                    cursor.execute("""
                        UPDATE user_usage 
                        SET analyses_used = 0, reset_date = DATE('now')
                        WHERE email = ?
                    """, (email,))
                    conn.commit()
                    print(f"🔄 Credits reset for {email} - {analyses_limit} fresh credits")
        
        conn.close()
    except Exception as e:
        print(f"⚠️ Credit reset error: {e}")
    # ===== END CREDIT RESET =====
    
    # ===== GET USER STATS =====
    analyses_used = 0
    analyses_limit = 5
    repo_count = 0
    security_scans = 0
    api_calls = 0
    
    try:
        conn = sqlite3.connect('bank.db')
        cursor = conn.cursor()
        
        # Get usage stats
        cursor.execute("""
            SELECT analyses_used, analyses_limit FROM user_usage WHERE email = ?
        """, (email,))
        result = cursor.fetchone()
        if result:
            analyses_used, analyses_limit = result
        
        # Get counts from analyses table (if it exists)
        try:
            cursor.execute("""
                SELECT 
                    COUNT(CASE WHEN type = 'github' THEN 1 END),
                    COUNT(CASE WHEN type = 'security' THEN 1 END),
                    COUNT(CASE WHEN type = 'api' THEN 1 END)
                FROM analyses WHERE user_email = ?
            """, (email,))
            stats = cursor.fetchone()
            if stats:
                repo_count, security_scans, api_calls = stats
        except:
            # Analyses table doesn't exist yet - ignore
            pass
        
        conn.close()
    except Exception as e:
        print(f"⚠️ Error getting user stats: {e}")
    # ===== END GET USER STATS =====
    
    # Mock recent analyses for now
    recent_analyses = [
        {
            "id": "abc123",
            "type": "github",
            "name": "fastapi/fastapi",
            "date": "2 hours ago",
            "duration": "45 seconds",
            "is_mock": False
        },
        {
            "id": "def456",
            "type": "security",
            "name": "Security scan - auth.py",
            "date": "Yesterday",
            "duration": "32 seconds", 
            "is_mock": True
        }
    ]
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "email": email,
        "analyses_used": analyses_used,
        "analyses_limit": analyses_limit,
        "repo_count": repo_count,
        "security_scans": security_scans,
        "api_calls": api_calls,
        "recent_analyses": recent_analyses if analyses_used > 0 else None
    })

# ===== Settings =====
@router.get("/settings")
async def settings_page(request: Request, session: str = Cookie(default=None)):
    if not session:
        return RedirectResponse("/login")
    
    email = verify_magic_link(session, mark_used=False)
    
    if not email:
        return RedirectResponse("/login")
    
    # Get user data from database
    conn = sqlite3.connect('bank.db')
    cursor = conn.cursor()
    
    # Get user usage
    cursor.execute("""
        SELECT analyses_used, analyses_limit, subscription_status 
        FROM user_usage WHERE email = ?
    """, (email,))
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        analyses_used, analyses_limit, subscription_status = result
        balance = analyses_limit - analyses_used  # remaining tokens
        tokens_per_month = analyses_limit
        current_plan = subscription_status.title() if subscription_status else "Free"
    else:
        # Default for users without record
        balance = 5
        tokens_per_month = 5
        current_plan = "Free"
    
    # Format renewal date (first of next month)
    from datetime import datetime, timedelta
    today = datetime.now()
    if today.month == 12:
        next_month = today.replace(year=today.year+1, month=1, day=1)
    else:
        next_month = today.replace(month=today.month+1, day=1)
    renewal_date = next_month.strftime("%B %d, %Y")
    
    return templates.TemplateResponse("settings.html", {
        "request": request,
        "user_email": email,
        "user_id": f"usr_{email.replace('@', '_at_').replace('.', '_')}",
        "current_plan": current_plan,
        "tokens_per_month": tokens_per_month,
        "balance": balance,  # ← This was missing!
        "renewal_date": renewal_date,
        "billing_history": []  # Empty for now
    })
