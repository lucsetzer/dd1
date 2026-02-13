# shared/auth.py

import sqlite3
from datetime import datetime

def store_magic_token(email: str, token: str) -> bool:
    """Store magic token in database."""
    print(f"💾 STORING TOKEN: {token} for {email}")
    
    try:
        conn = sqlite3.connect('bank.db')
        cursor = conn.cursor()
        
        # Debug: show what's in DB before insert
        cursor.execute("SELECT token, email FROM magic_links")
        existing = cursor.fetchall()
        print(f"💾 Existing tokens in DB: {existing}")
        
        cursor.execute("""
            INSERT OR REPLACE INTO magic_links (token, email, created, used)
            VALUES (?, ?, ?, ?)
        """, (token, email, datetime.now(), False))
        
        conn.commit()
        conn.close()
        print(f"✅ Token stored for: {email}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to store token: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_magic_link(email: str) -> str:
    """Create a unique token for magic link."""
    import uuid
    token = f"magic_{uuid.uuid4().hex}"
    return token

def verify_magic_link(token: str, mark_used: bool = True):
    print(f"🔍 VERIFYING TOKEN: {token}")
    
    try:
        conn = sqlite3.connect('bank.db')
        cursor = conn.cursor()
        
        # REMOVE the used=0 condition COMPLETELY for dashboard
        cursor.execute("""
            SELECT email FROM magic_links 
            WHERE token = ?
        """, (token,))
        
        result = cursor.fetchone()
        print(f"🔍 DB result: {result}")
        
        if result:
            email = result[0]
            # Only mark as used if this is a login attempt
            if mark_used:
                cursor.execute(
                    "UPDATE magic_links SET used = 1 WHERE token = ?",
                    (token,)
                )
                conn.commit()
            conn.close()
            return email
        
        conn.close()
        return None
        
    except Exception as e:
        print(f"❌ verify_magic_link error: {e}")
        return None