

# auth/magic_links.py - BUSINESS LOGIC ONLY

def generate_magic_link(email: str):
    """Generate and send magic link for login."""
    print("=" * 60)
    print(f"🎯 GENERATING MAGIC LINK - Email: {email}")
    print("=" * 60)
    
    token = None
    
    # Try email service
    print(f"1️⃣ ATTEMPTING EMAIL SERVICE...")
    try:
        from shared.email_service import send_magic_link_email
        print(f"   ✅ Import successful")
        print(f"   Calling send_magic_link_email('{email}')...")
        magic_link = send_magic_link_email(email)
        print(f"   ✅ Function returned: {magic_link}")
        
        # Extract token
        if magic_link and "token=" in str(magic_link):
            token = magic_link.split("token=")[-1]
            print(f"   Extracted token: {token[:30]}...")
        else:
            token = magic_link or "unknown"
            print(f"   Using as-is token: {token[:30]}...")
            
    except ImportError as e:
        print(f"   ❌ IMPORT ERROR: {e}")
        token = f"test_{email}"
        print(f"   Created fallback token: {token}")
    except Exception as e:
        print(f"   ❌ UNEXPECTED ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        token = f"error_{email}"
    
    return token