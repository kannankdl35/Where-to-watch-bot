# 🚀 Deployment Guide

## Option 1: Local Development

```bash
# 1. Clone/download the project
cd where-to-watch-bot

# 2. Create virtual environment
python -m venv venv

# 3. Activate it
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Set up environment
cp .env.example .env
# Edit .env with your BOT_TOKEN and TMDB_API_KEY

# 6. Run the bot
python bot.py
```

## Option 2: Docker

```bash
# Build and run
docker-compose up --build -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

## Option 3: Render (Recommended for Free Hosting)

1. Push code to GitHub
2. Go to [render.com](https://render.com) → New Web Service
3. Connect your GitHub repo
4. Set environment variables:
   - `BOT_TOKEN`
   - `TMDB_API_KEY`
5. Set start command: `python bot.py`
6. Deploy!

## Option 4: Railway

1. Push code to GitHub
2. Go to [railway.app](https://railway.app)
3. New Project → Deploy from GitHub repo
4. Add environment variables in dashboard
5. Deploy automatically

## Option 5: PythonAnywhere

1. Upload files via SFTP or Git
2. Create virtual environment and install requirements
3. Set environment variables in WSGI config
4. Run bot in a "Always-on task"
