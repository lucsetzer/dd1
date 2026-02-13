# Create a simple test file test_email.py in your clean project:
from shared.email_service import send_magic_link_email

print("✅ Email service imports successfully!")

# Optional: Test with a dummy email (comment out if you don't want to send)
# result = send_magic_link_email("test@example.com")
# print(f"Result: {result}")