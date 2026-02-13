@router.get("/history")
async def history_page(request: Request, session: str = Cookie(default=None)):
    # Show all user's analyses with pagination
    cursor.execute("""
        SELECT id, type, name, created_at, duration, is_mock 
        FROM analyses WHERE user_email = ?
        ORDER BY created_at DESC LIMIT 50
    """, (email,))
    analyses = cursor.fetchall()
    
    return templates.TemplateResponse("history.html", {
        "request": request,
        "analyses": analyses
    })