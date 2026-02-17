# Chat summary (2026-02-17)

## Goal
- Run the Discord bot 24/7 via hosting.

## What was done
- Added Render blueprint configuration with a web service for the Flask dashboard and a worker for the bot.
- Updated Flask app to bind to 0.0.0.0 and use the PORT env var for hosting platforms.
- Added runtime dependencies including gunicorn.

## Files changed/added
- app.py (run host/port updated)
- render.yaml (Render services: web + worker)
- requirements.txt (discord.py, python-dotenv, Flask, gunicorn)

## Deployment notes (Render)
- Push the project to GitHub.
- In Render: New > Blueprint, select the repo.
- Set DISCORD_TOKEN for the worker service.
- Deploy.
