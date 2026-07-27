"""
Message Formatters - Build beautiful Telegram messages
"""
from typing import Dict, List


def format_movie_info(movie: Dict, details: Dict, providers: Dict, region: str) -> str:
    title = details.get("title", "Unknown")
    year = details.get("release_date", "")[:4] if details.get("release_date") else "N/A"
    rating = details.get("vote_average", 0)
    runtime = details.get("runtime", 0)
    overview = details.get("overview", "No description available.")

    hours = runtime // 60
    mins = runtime % 60
    runtime_str = f"{hours}h {mins}m" if hours > 0 else f"{mins}m"

    flatrate = providers.get("flatrate", [])
    rent = providers.get("rent", [])
    buy = providers.get("buy", [])

    def format_list(items: List[Dict]) -> str:
        if not items:
            return "❌ Not available"
        names = [f"• {p.get('provider_name', 'Unknown')}" for p in items]
        return "\n".join(names)

    message = (
        f"🎬 *{title}* ({year})\n\n"
        f"⭐ *Rating:* {rating}/10\n"
        f"⏱ *Runtime:* {runtime_str}\n"
        f"🌍 *Region:* {region}\n\n"
        f"📝 *Overview:*\n"
        f"{overview[:300]}{'...' if len(overview) > 300 else ''}\n\n"
        f"📺 *Stream:*\n"
        f"{format_list(flatrate)}\n\n"
        f"💰 *Rent:*\n"
        f"{format_list(rent)}\n\n"
        f"🛒 *Buy:*\n"
        f"{format_list(buy)}"
    )
    return message


def format_watchlist(items: List) -> str:
    if not items:
        return "📭 Your watchlist is empty. Use `/watch <movie>` then tap 'Add to Watchlist'"

    message = "🎬 *Your Watchlist*\n\n"
    for i, (movie_id, title, added_at) in enumerate(items, 1):
        message += f"{i}. *{title}*\n"

    message += "\n💡 Use `/remove <number>` to remove an item"
    return message


def format_stats(stats: Dict) -> str:
    return (
        f"📊 *Your Movie Stats*\n\n"
        f"🎬 Watchlist: {stats['watchlist_count']} movies\n"
        f"⭐ Ratings given: {stats['ratings_count']}\n"
        f"📈 Average rating: {stats['avg_rating']}/5"
    )


def format_similar_movies(movies: List[Dict]) -> str:
    if not movies:
        return "No similar movies found."

    message = "🎥 *You might also like:*\n\n"
    for movie in movies:
        title = movie.get("title", "Unknown")
        year = movie.get("release_date", "")[:4] if movie.get("release_date") else "N/A"
        rating = movie.get("vote_average", 0)
        message += f"• *{title}* ({year}) — ⭐{rating}\n"

    return message


def format_now_playing(movies: List[Dict]) -> str:
    if not movies:
        return "No data available."

    message = "🍿 *Now Playing in Theaters*\n\n"
    for i, movie in enumerate(movies[:10], 1):
        title = movie.get("title", "Unknown")
        year = movie.get("release_date", "")[:4] if movie.get("release_date") else "N/A"
        rating = movie.get("vote_average", 0)
        message += f"{i}. *{title}* ({year}) — ⭐{rating}\n"

    return message
