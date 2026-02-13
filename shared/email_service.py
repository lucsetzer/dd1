import os
import resend
from shared.auth import create_magic_link  # ← CHANGED THIS LINE
from dotenv import load_dotenv

load_dotenv()

# Detect environment
is_render = os.getenv("RENDER") is not None

if is_render:
    public_url = os.getenv("PUBLIC_URL", "https://promptsalchemy.com")
    print(f"🔐 PRODUCTION: Using {public_url}")
else:
    public_url = "http://localhost:10000"
    print(f"🔧 LOCAL: Using {public_url}")

print(f"DEBUG: Loading .env from {os.path.abspath('.env')}")
print(f"DEBUG: RESEND_API_KEY = {'SET' if os.getenv('RESEND_API_KEY') else 'NOT SET'}")

def send_magic_link_email(email: str):
    """Send magic link email via Resend.com"""
    print(f"📨 [email_service] Starting for {email}")
    
    try:
        # Create a proper token using shared.auth
        print(f"📨 [email_service] Creating token...")
        from shared.auth import create_magic_link
        token = create_magic_link(email)  # This will store it in database
        print(f"📨 [email_service] Token created: {token[:30]}...")
        
        # Get your Render URL for the magic link
        public_url = os.getenv("PUBLIC_URL", "https://docudecipher.com")
        magic_link = f"{public_url}/auth?token={token}"
        print(f"📨 [email_service] Magic link: {magic_link}")
        
        # Get Resend API key
        api_key = os.getenv("RESEND_API_KEY")
        print(f"📨 [email_service] RESEND_API_KEY set: {bool(api_key)}")
        
        if not api_key:
            print("❌ RESEND_API_KEY not set. Using mock mode.")
            print(f"📨 MOCK: Magic link for {email}: {magic_link}")
            return magic_link
        
        # ... rest of email sending code
        print(f"📨 [email_service] Would send real email")
        return magic_link
        
    except Exception as e:
        print(f"❌ [email_service] ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        # Return a fallback
        return f"https://docudecipher.com/auth?token=error_{email}"