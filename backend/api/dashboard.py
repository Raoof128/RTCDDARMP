"""
Dashboard API Endpoint
"""

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """
    Serve the monitoring dashboard.

    Returns:
    --------
    HTMLResponse
        Dashboard HTML page
    """
    dashboard_file = Path("frontend/index.html")

    if dashboard_file.exists():
        with open(dashboard_file, "r") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    else:
        # Fallback embedded dashboard
        return HTMLResponse(
            content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>RCD² Dashboard</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
                .container { max-width: 1400px; margin: 0 auto; }
                h1 { color: #333; }
                .card { background: white; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .status { display: inline-block; padding: 5px 10px; border-radius: 4px; font-weight: bold; }
                .status.healthy { background: #4CAF50; color: white; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🔄 RCD² Monitoring Dashboard</h1>
                <div class="card">
                    <h2>System Status</h2>
                    <span class="status healthy">OPERATIONAL</span>
                    <p>Frontend file not found. Using embedded dashboard.</p>
                    <p>Visit <a href="/docs">/docs</a> for API documentation.</p>
                </div>
            </div>
        </body>
        </html>
        """
        )
