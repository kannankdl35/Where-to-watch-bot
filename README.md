# 🎬 Where to Watch Bot

A Telegram bot that finds where movies are streaming, renting, or available to buy — with personalized watchlists, ratings, and recommendations.

## Features

- 🔍 **Movie Search** — Find any movie with streaming/rent/buy info
- 🌍 **Region Support** — Set your country for accurate provider data
- 📋 **Personal Watchlist** — Save movies to watch later
- ⭐ **Ratings** — Rate movies 1-5 stars
- 🎥 **Similar Movies** — Get recommendations based on any movie
- 🍿 **Now Playing** — See what's currently in theaters
- 📊 **Statistics** — Track your watchlist and ratings

## Quick Start

1. Copy `.env.example` to `.env` and fill in your tokens
2. Install dependencies: `pip install -r requirements.txt`
3. Run: `python bot.py`

## Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message |
| `/watch <movie>` | Search where to watch |
| `/region <code>` | Set country (US, IN, GB, etc.) |
| `/watchlist` | View saved movies |
| `/add <movie>` | Quick add to watchlist |
| `/remove <number>` | Remove from watchlist |
| `/rate <movie>` | Rate a movie |
| `/stats` | Your movie stats |
| `/similar <movie>` | Find similar movies |
| `/nowplaying` | Movies in theaters |
| `/help` | Show all commands |

## Deployment

See `DEPLOY.md` for Render, Railway, and Docker deployment guides.

## License

MIT
