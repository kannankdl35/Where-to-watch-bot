"""
Where to Watch Bot - Main Application
A Telegram bot that finds where movies are streaming, renting, or buying.
"""
import os
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters
)

from utils.tmdb_client import tmdb
from utils.database import (
    init_database,
    set_user_region,
    get_user_region,
    add_to_watchlist,
    get_watchlist,
    remove_from_watchlist,
    add_rating,
    get_user_stats
)
from utils.formatters import (
    format_movie_info,
    format_watchlist,
    format_stats,
    format_similar_movies,
    format_now_playing
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Store temporary data during conversations
user_temp_data = {}

# ============================================
# COMMAND HANDLERS
# ============================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    welcome_text = """🎬 *Welcome to Where to Watch Bot!*

I help you find where movies are streaming, renting, or available to buy.

*Commands:*
🔍 `/watch <movie>` — Find where to watch a movie
🌍 `/region <code>` — Set your country (e.g., US, IN, GB, DE, FR)
📋 `/watchlist` — View your saved movies
⭐ `/rate <movie>` — Rate a movie (1-5 stars)
📊 `/stats` — Your movie statistics
🎥 `/similar <movie>` — Find similar movies
🍿 `/nowplaying` — Movies currently in theaters
❓ `/help` — Show all commands

*Examples:*
`/watch Inception`
`/region IN`
`/watch Dune Part Two`
"""
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_text = """🎬 *Where to Watch Bot - Help*

*Core Commands:*
`/watch <movie>` — Search for a movie and see where to stream/rent/buy
`/region <code>` — Set your country for accurate results
  • Examples: `US`, `IN`, `GB`, `DE`, `FR`, `CA`, `AU`, `JP`

*Personal Features:*
`/watchlist` — Movies you've saved
`/add <movie>` — Quick add to watchlist
`/remove <number>` — Remove item by number from watchlist
`/rate <movie>` — Rate a movie 1-5 stars
`/stats` — Your watchlist count and average ratings

*Discovery:*
`/similar <movie>` — Get movie recommendations
`/nowplaying` — Currently playing in theaters

*Tips:*
• Use full movie names for better results
• Set your region first for accurate provider data
• The bot remembers your region automatically
"""
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def region_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /region command"""
    if not context.args:
        await update.message.reply_text(
            "🌍 *Set Your Region*\n\n"
            "Usage: `/region <country-code>`\n"
            "Examples: `/region US`, `/region IN`, `/region GB`\n\n"
            "Common codes: US, IN, GB, DE, FR, CA, AU, JP, BR, MX",
            parse_mode="Markdown"
        )
        return

    region_code = context.args[0].upper()
    user_id = update.effective_user.id
    username = update.effective_user.username

    # Validate region (basic check - 2-3 chars)
    if len(region_code) < 2 or len(region_code) > 3:
        await update.message.reply_text(
            "❌ Invalid region code. Please use a 2-3 letter country code (e.g., US, IN, GB)",
            parse_mode="Markdown"
        )
        return

    success = set_user_region(user_id, region_code, username)

    if success:
        await update.message.reply_text(
            f"✅ *Region set to {region_code}*\n\n"
            f"I'll now show streaming providers available in {region_code}.\n"
            f"Use `/watch <movie>` to search!",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("❌ Failed to set region. Please try again.")

async def watch_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /watch command - Main feature"""
    if not context.args:
        await update.message.reply_text(
            "🔍 *Search for a Movie*\n\n"
            "Usage: `/watch <movie name>`\n"
            "Examples:\n"
            "• `/watch The Dark Knight`\n"
            "• `/watch Inception`\n"
            "• `/watch Dune Part Two`",
            parse_mode="Markdown"
        )
        return

    query = " ".join(context.args)
    user_id = update.effective_user.id
    region = get_user_region(user_id)

    # Show searching message
    searching_msg = await update.message.reply_text(
        f"🔍 Searching for *{query}*...",
        parse_mode="Markdown"
    )

    # Search TMDB
    movie = tmdb.search_movie(query)

    if not movie:
        await searching_msg.edit_text(
            f"❌ *Movie not found*\n\n"
            f"Could not find "{query}".\n"
            f"Try using the full movie title or check the spelling.",
            parse_mode="Markdown"
        )
        return

    movie_id = movie["id"]

    # Fetch details and providers in parallel would be better, but sequential is fine
    details = tmdb.get_movie_details(movie_id)
    providers_data = tmdb.get_watch_providers(movie_id)
    providers = providers_data.get("results", {}).get(region, {})

    # Build message
    message = format_movie_info(movie, details, providers, region)

    # Create action buttons
    keyboard = [
        [
            InlineKeyboardButton("➕ Add to Watchlist", callback_data=f"add_{movie_id}_{details.get('title', '')}"),
            InlineKeyboardButton("⭐ Rate", callback_data=f"rate_{movie_id}_{details.get('title', '')}")
        ],
        [
            InlineKeyboardButton("🎥 Similar Movies", callback_data=f"similar_{movie_id}"),
            InlineKeyboardButton("🔄 Search Again", callback_data="search_again")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Get poster
    poster_path = details.get("poster_path")
    poster_url = tmdb.get_poster_url(poster_path) if poster_path else None

    # Delete searching message and send result
    await searching_msg.delete()

    if poster_url:
        await update.message.reply_photo(
            photo=poster_url,
            caption=message,
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            message,
            parse_mode="Markdown",
            reply_markup=reply_markup
        )

    # Store temp data for callbacks
    user_temp_data[user_id] = {
        "last_movie_id": movie_id,
        "last_movie_title": details.get("title", "")
    }

async def watchlist_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /watchlist command"""
    user_id = update.effective_user.id
    items = get_watchlist(user_id)

    message = format_watchlist(items)
    await update.message.reply_text(message, parse_mode="Markdown")

async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /add command - Quick add to watchlist"""
    if not context.args:
        await update.message.reply_text(
            "📋 *Add to Watchlist*\n\n"
            "Usage: `/add <movie name>`\n"
            "Example: `/add The Matrix`",
            parse_mode="Markdown"
        )
        return

    query = " ".join(context.args)
    user_id = update.effective_user.id

    msg = await update.message.reply_text(f"🔍 Searching for *{query}*...", parse_mode="Markdown")

    movie = tmdb.search_movie(query)
    if not movie:
        await msg.edit_text(f"❌ Could not find "{query}"")
        return

    movie_id = movie["id"]
    title = movie.get("title", "Unknown")

    success = add_to_watchlist(user_id, movie_id, title)

    if success:
        await msg.edit_text(f"✅ *{title}* added to your watchlist!", parse_mode="Markdown")
    else:
        await msg.edit_text(f"ℹ️ *{title}* is already in your watchlist.", parse_mode="Markdown")

async def remove_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /remove command"""
    if not context.args:
        await update.message.reply_text(
            "🗑 *Remove from Watchlist*\n\n"
            "Usage: `/remove <number>`\n"
            "Use `/watchlist` to see the numbers.",
            parse_mode="Markdown"
        )
        return

    try:
        index = int(context.args[0]) - 1  # Convert to 0-based
        user_id = update.effective_user.id
        items = get_watchlist(user_id)

        if index < 0 or index >= len(items):
            await update.message.reply_text("❌ Invalid number. Use `/watchlist` to see valid numbers.")
            return

        movie_id = items[index][0]
        movie_title = items[index][1]

        remove_from_watchlist(user_id, movie_id)
        await update.message.reply_text(f"🗑 Removed *{movie_title}* from your watchlist.", parse_mode="Markdown")

    except ValueError:
        await update.message.reply_text("❌ Please provide a valid number.")

async def rate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /rate command"""
    if not context.args:
        await update.message.reply_text(
            "⭐ *Rate a Movie*\n\n"
            "Usage: `/rate <movie name>`\n"
            "Example: `/rate Inception`\n\n"
            "After searching, you'll get buttons to rate 1-5 stars.",
            parse_mode="Markdown"
        )
        return

    # For simplicity, search the movie first then show rating buttons
    query = " ".join(context.args)
    user_id = update.effective_user.id

    msg = await update.message.reply_text(f"🔍 Searching for *{query}*...", parse_mode="Markdown")

    movie = tmdb.search_movie(query)
    if not movie:
        await msg.edit_text(f"❌ Could not find "{query}"")
        return

    movie_id = movie["id"]
    title = movie.get("title", "Unknown")

    # Create rating buttons
    keyboard = [
        [InlineKeyboardButton("⭐", callback_data=f"rateval_{movie_id}_{title}_1"),
         InlineKeyboardButton("⭐⭐", callback_data=f"rateval_{movie_id}_{title}_2"),
         InlineKeyboardButton("⭐⭐⭐", callback_data=f"rateval_{movie_id}_{title}_3"),
         InlineKeyboardButton("⭐⭐⭐⭐", callback_data=f"rateval_{movie_id}_{title}_4"),
         InlineKeyboardButton("⭐⭐⭐⭐⭐", callback_data=f"rateval_{movie_id}_{title}_5")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await msg.edit_text(
        f"🎬 *{title}*\n\nHow would you rate this movie?",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stats command"""
    user_id = update.effective_user.id
    stats = get_user_stats(user_id)
    message = format_stats(stats)
    await update.message.reply_text(message, parse_mode="Markdown")

async def similar_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /similar command"""
    if not context.args:
        await update.message.reply_text(
            "🎥 *Find Similar Movies*\n\n"
            "Usage: `/similar <movie name>`\n"
            "Example: `/similar Inception`",
            parse_mode="Markdown"
        )
        return

    query = " ".join(context.args)

    msg = await update.message.reply_text(f"🔍 Finding movies similar to *{query}*...", parse_mode="Markdown")

    movie = tmdb.search_movie(query)
    if not movie:
        await msg.edit_text(f"❌ Could not find "{query}"")
        return

    movie_id = movie["id"]
    title = movie.get("title", "Unknown")
    similar = tmdb.get_similar_movies(movie_id)

    message = format_similar_movies(similar)
    await msg.edit_text(f"🎬 *Similar to {title}*\n\n{message}", parse_mode="Markdown")

async def nowplaying_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /nowplaying command"""
    msg = await update.message.reply_text("🍿 Fetching current releases...")

    movies = tmdb.get_now_playing()
    message = format_now_playing(movies)

    await msg.edit_text(message, parse_mode="Markdown")

# ============================================
# CALLBACK HANDLERS (Button Clicks)
# ============================================

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline keyboard button presses"""
    query = update.callback_query
    await query.answer()

    data = query.data
    user_id = update.effective_user.id

    if data.startswith("add_"):
        # Add to watchlist
        parts = data.split("_", 2)
        if len(parts) >= 3:
            movie_id = int(parts[1])
            movie_title = parts[2]
            success = add_to_watchlist(user_id, movie_id, movie_title)
            if success:
                await query.edit_message_reply_markup(reply_markup=None)
                await query.message.reply_text(f"✅ *{movie_title}* added to watchlist!", parse_mode="Markdown")
            else:
                await query.answer("Already in your watchlist!")

    elif data.startswith("rate_"):
        # Show rating buttons
        parts = data.split("_", 2)
        if len(parts) >= 3:
            movie_id = int(parts[1])
            movie_title = parts[2]

            keyboard = [
                [InlineKeyboardButton("⭐", callback_data=f"rateval_{movie_id}_{movie_title}_1"),
                 InlineKeyboardButton("⭐⭐", callback_data=f"rateval_{movie_id}_{movie_title}_2"),
                 InlineKeyboardButton("⭐⭐⭐", callback_data=f"rateval_{movie_id}_{movie_title}_3"),
                 InlineKeyboardButton("⭐⭐⭐⭐", callback_data=f"rateval_{movie_id}_{movie_title}_4"),
                 InlineKeyboardButton("⭐⭐⭐⭐⭐", callback_data=f"rateval_{movie_id}_{movie_title}_5")]
            ]
            await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("rateval_"):
        # Save rating
        parts = data.split("_", 3)
        if len(parts) >= 4:
            movie_id = int(parts[1])
            movie_title = parts[2]
            rating = int(parts[3])

            add_rating(user_id, movie_id, movie_title, rating)
            stars = "⭐" * rating
            await query.edit_message_reply_markup(reply_markup=None)
            await query.message.reply_text(
                f"✅ You rated *{movie_title}* {stars} ({rating}/5)",
                parse_mode="Markdown"
            )

    elif data.startswith("similar_"):
        # Show similar movies
        movie_id = int(data.split("_")[1])
        similar = tmdb.get_similar_movies(movie_id)
        message = format_similar_movies(similar)
        await query.message.reply_text(message, parse_mode="Markdown")

    elif data == "search_again":
        await query.message.reply_text(
            "🔍 Send `/watch <movie>` to search again!",
            parse_mode="Markdown"
        )

# ============================================
# ERROR HANDLER
# ============================================

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error(f"Update {update} caused error {context.error}")

    if update and update.effective_message:
        await update.effective_message.reply_text(
            "❌ *Oops! Something went wrong.*\n"
            "Please try again or use `/help` for assistance.",
            parse_mode="Markdown"
        )

# ============================================
# MAIN APPLICATION
# ============================================

def main():
    """Start the bot"""
    # Initialize database
    init_database()
    logger.info("Database initialized")

    # Get bot token
    token = os.getenv("BOT_TOKEN")
    if not token:
        logger.error("BOT_TOKEN not found in environment variables!")
        return

    # Build application
    application = Application.builder().token(token).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("watch", watch_command))
    application.add_handler(CommandHandler("region", region_command))
    application.add_handler(CommandHandler("watchlist", watchlist_command))
    application.add_handler(CommandHandler("add", add_command))
    application.add_handler(CommandHandler("remove", remove_command))
    application.add_handler(CommandHandler("rate", rate_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("similar", similar_command))
    application.add_handler(CommandHandler("nowplaying", nowplaying_command))

    # Add callback handler for buttons
    application.add_handler(CallbackQueryHandler(button_callback))

    # Add error handler
    application.add_error_handler(error_handler)

    logger.info("Bot started! Press Ctrl+C to stop.")

    # Run the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
