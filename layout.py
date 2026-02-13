def layout(title: str, content: str) -> str:
    print(f"🔧 LAYOUT() CALLED for: {title}")  # <-- ADD THIS LINE
    
    return f'''<!DOCTYPE html>

<html>
<head>
    <title>{title}</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@1/css/pico.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        .card-grid {{
            display: grid !important;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)) !important;
            gap: 1.5rem !important;
            margin: 2rem 0 !important;
        }}

        .step-card {{
            background: rgba(255, 255, 255, 0.05) !important;
            border-radius: 12px !important;
            padding: 1.5rem !important;
            text-align: center !important;
            text-decoration: none !important;
            color: inherit !important;
            border: 2px solid transparent !important;
            transition: all 0.3s ease !important;
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
        }}

        .step-card:hover {{
            border-color: #0cc0df !important;
            transform: translateY(-4px) !important;
            box-shadow: 0 8px 20px rgba(12, 192, 223, 0.15) !important;
        }}

        .step-card i {{
            font-size: 2.5rem !important;
            color: #0cc0df !important;
            margin-bottom: 1rem !important;
        }}

        .step-card h3 {{
            margin: 0.5rem 0 !important;
            color: white !important;
        }}

        .step-card p {{
            color: #9ca3af !important;
            margin: 0 !important;
            font-size: 0.95rem !important;
        }}

        .steps {{
            display: flex !important;
            justify-content: space-between !important;
            max-width: 400px !important;
            margin: 2rem auto !important;
            position: relative !important;
        }}

        .steps::before {{
            content: '' !important;
            position: absolute !important;
            top: 24px !important;
            left: 50px !important;
            right: 50px !important;
            height: 2px !important;
            background: #374151 !important;
            z-index: 1 !important;
        }}

        .step {{
            width: 50px !important;
            height: 50px !important;
            border-radius: 50% !important;
            background: #374151 !important;
            color: #9ca3af !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            font-weight: bold !important;
            position: relative !important;
            z-index: 2 !important;
            transition: all 0.3s !important;
        }}

        .step.active {{
            background: #0cc0df !important;
            color: white !important;
            transform: scale(1.1) !important;
        }}

        button:focus, a:focus {{
            outline: 2px solid #0cc0df !important;
            outline-offset: 2px !important;
        }}
    </style>
</head>
<body>
    <nav class="container">
        <ul>
            <li><strong><i class="fas fa-hat-wizard"></i> Prompts Alchemy</strong></li>
        </ul>
    </nav>
    </nav>
    <main class="container">
        {content}
    </main>
</body>
</html>'''