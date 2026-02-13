from fastapi import APIRouter, Request, Cookie
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from shared.auth import verify_magic_link
import sqlite3
from datetime import datetime, timedelta

router = APIRouter()
templates = Jinja2Templates(directory="templates")

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
        balance = analyses_limit - analyses_used
        tokens_per_month = analyses_limit
        current_plan = subscription_status.title() if subscription_status else "Free"
    else:
        balance = 5
        tokens_per_month = 5
        current_plan = "Free"
    
    # Format renewal date (first of next month)
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
        "balance": balance,
        "renewal_date": renewal_date
    })