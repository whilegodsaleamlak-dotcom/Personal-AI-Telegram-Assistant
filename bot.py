import os
import json
import logging
from datetime import datetime
from collections import defaultdict
from dotenv import load_dotenv
from openai import OpenAI
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1",
)

DATA_FILE = "user_data.json"


def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def get_user_data(user_id):
    data = load_data()
    uid = str(user_id)
    if uid not in data:
        data[uid] = {
            "favorites": [],
            "recent": [],
            "settings": {"notifications": True, "language": "en"},
            "chat_count": 0,
            "first_seen": datetime.now().isoformat(),
        }
        save_data(data)
    return data[uid]


def update_user_data(user_id, update_dict):
    data = load_data()
    uid = str(user_id)
    if uid not in data:
        data[uid] = {
            "favorites": [],
            "recent": [],
            "settings": {"notifications": True, "language": "en"},
            "chat_count": 0,
            "first_seen": datetime.now().isoformat(),
        }
    data[uid].update(update_dict)
    save_data(data)


def add_recent(user_id, action):
    udata = get_user_data(user_id)
    recent = udata.get("recent", [])
    recent.insert(0, {"action": action, "time": datetime.now().isoformat()})
    recent = recent[:10]
    update_user_data(user_id, {"recent": recent})


user_sessions = defaultdict(lambda: {"messages": []})

PROFILE = {
    "name": "Saleamlak Aschalew",
    "title": "Junior Project Manager & Web Developer",
    "email": "whilegodsaleamlak@gmail.com",
    "phone1": "+251 930 220 301",
    "phone2": "+251 944 015 457",
    "address": "Addis Ababa, Figa Traffic Lights",
    "portfolio": "https://saleamlak.vercel.app",
    "github": "https://github.com/saleamlak",
    "cv_link": "https://saleamlak.vercel.app",
    "languages_spoken": "English, Amharic",
    "about": (
        "I am a junior project manager with a strong interest in planning, "
        "teamwork, and digital projects. I am passionate about creating digital "
        "experiences and focus on clear communication, basic planning, and "
        "continuous improvement through real project experience."
    ),
    "education": (
        "1. Diploma (2023-2025) - Misrak Polytechnic College - "
        "Web Development & Database Administration\n"
        "2. Degree (2026 - First year) - GAGE University College - "
        "Computer Science"
    ),
    "skills": (
        "Front-end: HTML/CSS (95%), JavaScript (85%), React & Next.js (80%)\n"
        "Back-end: Node.js (75%), PHP (75%), XAMPP (70%), SQL (65%), MongoDB (65%)\n"
        "Tools: Git & GitHub (85%)\n"
        "Other: UI/UX Design (85%), Project Management (80%)"
    ),
    "programming_languages": "HTML/CSS, JavaScript, PHP, SQL",
    "projects": (
        "1. Gulit E-commerce Web App - Full-stack e-commerce platform\n"
        "2. School Result Management - Student result tracking system\n"
        "3. To Do List - Productivity task management app\n"
        "4. Income Expense Tracker - Personal finance management tool"
    ),
    "experience": (
        "1. Junior Project Manager (2025-Present) at Tech Innovations Inc.\n"
        "2. Lead Developer (2019-2022) at Digital Solutions Corp."
    ),
    "services": (
        "1. Creative Branding - Simple and effective brand identities\n"
        "2. Design Systems - Structured, user-friendly layouts\n"
        "3. Digital Platforms - Reliable websites and web apps"
    ),
    "interests": "Web development, project management, UI/UX design",
    "career_goals": (
        "Grow into a professional project manager and contribute meaningfully "
        "to digital projects."
    ),
    "achievements": (
        "Completed 2+ projects, diploma in Web Development & Database "
        "Administration, currently pursuing Computer Science degree"
    ),
}

SYSTEM_PROMPT = f"""You are Saleamlak Aschalew's Personal AI Telegram Assistant. 
Answer questions about him using ONLY the information below. 
Be friendly, concise, and professional.

PROFILE:
- Name: {PROFILE['name']}
- Title: {PROFILE['title']}
- About: {PROFILE['about']}
- Email: {PROFILE['email']}
- Phone: {PROFILE['phone1']}, {PROFILE['phone2']}
- Address: {PROFILE['address']}
- Portfolio: {PROFILE['portfolio']}
- GitHub: {PROFILE['github']}
- Education: {PROFILE['education']}
- Skills: {PROFILE['skills']}
- Programming Languages: {PROFILE['programming_languages']}
- Projects: {PROFILE['projects']}
- Experience: {PROFILE['experience']}
- Services: {PROFILE['services']}
- Interests: {PROFILE['interests']}
- Career Goals: {PROFILE['career_goals']}
- Achievements: {PROFILE['achievements']}

Answer as Saleamlak's assistant. Be helpful and professional."""


MAIN_KEYBOARD = [
    [InlineKeyboardButton("👤 Profile", callback_data="profile"),
     InlineKeyboardButton("⚙️ Settings", callback_data="settings")],
    [InlineKeyboardButton("📂 Favorites", callback_data="favorites"),
     InlineKeyboardButton("🕐 Recent", callback_data="recent")],
    [InlineKeyboardButton("📊 Stats", callback_data="stats"),
     InlineKeyboardButton("❓ Help", callback_data="help_main")],
    [InlineKeyboardButton("🤖 Ask AI", callback_data="ask_ai")],
]

BACK_KEYBOARD = [
    [InlineKeyboardButton("🔙 Back to Menu", callback_data="back_main")]
]


def back_kb():
    return InlineKeyboardMarkup(BACK_KEYBOARD)


async def send_main_menu(query_or_update, user_id, first_name=None):
    if first_name:
        text = (
            f"Welcome {first_name}! 👋\n\n"
            f"I am the Personal AI Assistant of {PROFILE['name']}.\n"
            f"({PROFILE['title']})\n\n"
            f"Select an option below:"
        )
    else:
        text = "🏠 **Main Menu**\n\nSelect an option:"
    markup = InlineKeyboardMarkup(MAIN_KEYBOARD)
    if hasattr(query_or_update, "message") and query_or_update.message:
        await query_or_update.message.reply_text(text, reply_markup=markup)
    else:
        await query_or_update.edit_message_text(text, reply_markup=markup)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    get_user_data(user_id)
    add_recent(user_id, "Started bot")
    await send_main_menu(update, user_id, user.first_name)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    if data == "back_main":
        add_recent(user_id, "Back to menu")
        await query.edit_message_text(
            "🏠 **Main Menu**\n\nSelect an option:",
            reply_markup=InlineKeyboardMarkup(MAIN_KEYBOARD),
        )
        return

    if data == "profile":
        add_recent(user_id, "Viewed profile")
        keyboard = [
            [InlineKeyboardButton("👤 About", callback_data="p_about"),
             InlineKeyboardButton("💼 Skills", callback_data="p_skills")],
            [InlineKeyboardButton("💻 Projects", callback_data="p_projects"),
             InlineKeyboardButton("🎓 Education", callback_data="p_education")],
            [InlineKeyboardButton("🛠 Services", callback_data="p_services"),
             InlineKeyboardButton("💼 Experience", callback_data="p_experience")],
            [InlineKeyboardButton("📧 Contact", callback_data="p_contact"),
             InlineKeyboardButton("📄 CV", callback_data="p_cv")],
            [InlineKeyboardButton("🎯 Goals", callback_data="p_goals"),
             InlineKeyboardButton("🏆 Achievements", callback_data="p_achievements")],
            [InlineKeyboardButton("🌐 Portfolio", callback_data="p_portfolio"),
             InlineKeyboardButton("🐙 GitHub", callback_data="p_github")],
            [InlineKeyboardButton("🔙 Back to Menu", callback_data="back_main")],
        ]
        await query.edit_message_text(
            f"👤 **{PROFILE['name']}'s Profile**\n\nSelect a section:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif data == "p_about":
        text = (
            f"👤 **About {PROFILE['name']}**\n\n"
            f"{PROFILE['about']}\n\n"
            f"🗣 Languages: {PROFILE['languages_spoken']}\n"
            f"❤️ Interests: {PROFILE['interests']}"
        )
        await query.edit_message_text(text, reply_markup=back_kb())

    elif data == "p_skills":
        await query.edit_message_text(
            f"💼 **Skills**\n\n{PROFILE['skills']}", reply_markup=back_kb()
        )

    elif data == "p_projects":
        await query.edit_message_text(
            f"💻 **Projects**\n\n{PROFILE['projects']}", reply_markup=back_kb()
        )

    elif data == "p_education":
        await query.edit_message_text(
            f"🎓 **Education**\n\n{PROFILE['education']}", reply_markup=back_kb()
        )

    elif data == "p_services":
        await query.edit_message_text(
            f"🛠 **Services**\n\n{PROFILE['services']}", reply_markup=back_kb()
        )

    elif data == "p_experience":
        await query.edit_message_text(
            f"💼 **Experience**\n\n{PROFILE['experience']}", reply_markup=back_kb()
        )

    elif data == "p_contact":
        text = (
            f"📧 **Contact {PROFILE['name']}**\n\n"
            f"Email: {PROFILE['email']}\n"
            f"Phone: {PROFILE['phone1']}\n"
            f"Phone: {PROFILE['phone2']}\n"
            f"Address: {PROFILE['address']}"
        )
        await query.edit_message_text(text, reply_markup=back_kb())

    elif data == "p_cv":
        await query.edit_message_text(
            f"📄 **Download CV**\n\n{PROFILE['cv_link']}", reply_markup=back_kb()
        )

    elif data == "p_goals":
        await query.edit_message_text(
            f"🎯 **Career Goals**\n\n{PROFILE['career_goals']}", reply_markup=back_kb()
        )

    elif data == "p_achievements":
        await query.edit_message_text(
            f"🏆 **Achievements**\n\n{PROFILE['achievements']}", reply_markup=back_kb()
        )

    elif data == "p_portfolio":
        await query.edit_message_text(
            f"🌐 **Portfolio**\n\n{PROFILE['portfolio']}", reply_markup=back_kb()
        )

    elif data == "p_github":
        await query.edit_message_text(
            f"🐙 **GitHub**\n\n{PROFILE['github']}", reply_markup=back_kb()
        )

    elif data == "settings":
        udata = get_user_data(user_id)
        notif = "ON" if udata["settings"].get("notifications", True) else "OFF"
        lang = udata["settings"].get("language", "en")
        add_recent(user_id, "Viewed settings")
        keyboard = [
            [InlineKeyboardButton(
                f"🔔 Notifications: {notif}", callback_data="toggle_notif")],
            [InlineKeyboardButton(
                f"🌐 Language: {lang}", callback_data="toggle_lang")],
            [InlineKeyboardButton("🗑 Clear My Data", callback_data="clear_data")],
            [InlineKeyboardButton("🔙 Back to Menu", callback_data="back_main")],
        ]
        await query.edit_message_text(
            "⚙️ **Settings**\n\nCustomize your experience:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif data == "toggle_notif":
        udata = get_user_data(user_id)
        current = udata["settings"].get("notifications", True)
        udata["settings"]["notifications"] = not current
        update_user_data(user_id, {"settings": udata["settings"]})
        new_val = "ON" if not current else "OFF"
        keyboard = [
            [InlineKeyboardButton(
                f"🔔 Notifications: {new_val}", callback_data="toggle_notif")],
            [InlineKeyboardButton(
                f"🌐 Language: {udata['settings'].get('language', 'en')}",
                callback_data="toggle_lang")],
            [InlineKeyboardButton("🗑 Clear My Data", callback_data="clear_data")],
            [InlineKeyboardButton("🔙 Back to Menu", callback_data="back_main")],
        ]
        await query.edit_message_text(
            "⚙️ **Settings**\n\nCustomize your experience:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif data == "toggle_lang":
        udata = get_user_data(user_id)
        current = udata["settings"].get("language", "en")
        new_lang = "am" if current == "en" else "en"
        udata["settings"]["language"] = new_lang
        update_user_data(user_id, {"settings": udata["settings"]})
        notif = "ON" if udata["settings"].get("notifications", True) else "OFF"
        keyboard = [
            [InlineKeyboardButton(
                f"🔔 Notifications: {notif}", callback_data="toggle_notif")],
            [InlineKeyboardButton(
                f"🌐 Language: {new_lang}", callback_data="toggle_lang")],
            [InlineKeyboardButton("🗑 Clear My Data", callback_data="clear_data")],
            [InlineKeyboardButton("🔙 Back to Menu", callback_data="back_main")],
        ]
        await query.edit_message_text(
            "⚙️ **Settings**\n\nCustomize your experience:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif data == "clear_data":
        update_user_data(user_id, {"favorites": [], "recent": []})
        await query.edit_message_text(
            "✅ Your data has been cleared!", reply_markup=back_kb()
        )

    elif data == "favorites":
        udata = get_user_data(user_id)
        favs = udata.get("favorites", [])
        add_recent(user_id, "Viewed favorites")
        if favs:
            fav_list = "\n".join(
                [f"  {i+1}. {f}" for i, f in enumerate(favs)]
            )
            text = f"📂 **Your Favorites**\n\n{fav_list}"
        else:
            text = "📂 **Your Favorites**\n\nNo favorites yet.\nType /addfav <item> to add one!"
        keyboard = [
            [InlineKeyboardButton("➕ Add Favorite", callback_data="add_fav")],
            [InlineKeyboardButton("🗑 Clear All", callback_data="clear_favs")],
            [InlineKeyboardButton("🔙 Back to Menu", callback_data="back_main")],
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "add_fav":
        await query.edit_message_text(
            "➕ Send me the item you want to add as a favorite:\n\n"
            "Example: /addfav Gulit E-commerce Project",
            reply_markup=back_kb(),
        )

    elif data == "clear_favs":
        update_user_data(user_id, {"favorites": []})
        await query.edit_message_text(
            "✅ All favorites cleared!", reply_markup=back_kb()
        )

    elif data == "recent":
        udata = get_user_data(user_id)
        recent = udata.get("recent", [])
        add_recent(user_id, "Viewed recent activity")
        if recent:
            lines = []
            for r in recent[:10]:
                t = r.get("time", "")[:16].replace("T", " ")
                lines.append(f"  - {r['action']}  ({t})")
            text = "🕐 **Recent Activity**\n\n" + "\n".join(lines)
        else:
            text = "🕐 **Recent Activity**\n\nNo recent activity yet."
        await query.edit_message_text(text, reply_markup=back_kb())

    elif data == "stats":
        udata = get_user_data(user_id)
        favs = len(udata.get("favorites", []))
        chats = udata.get("chat_count", 0)
        recent_count = len(udata.get("recent", []))
        first = udata.get("first_seen", "Unknown")[:10]
        add_recent(user_id, "Viewed stats")
        text = (
            f"📊 **Your Stats**\n\n"
            f"👤 User ID: {user_id}\n"
            f"📅 First seen: {first}\n"
            f"💬 Total chats: {chats}\n"
            f"📂 Favorites: {favs}\n"
            f"🕐 Recent actions: {recent_count}"
        )
        await query.edit_message_text(text, reply_markup=back_kb())

    elif data == "help_main":
        add_recent(user_id, "Viewed help")
        text = (
            "❓ **Help**\n\n"
            "**Navigation:**\n"
            "Use the buttons to navigate between sections.\n"
            "Every section has a 🔙 Back button.\n\n"
            "**Commands:**\n"
            "/start - Main menu\n"
            "/addfav <item> - Add a favorite\n"
            "/new - Clear AI chat history\n"
            "/help - Show help\n\n"
            "**AI Chat:**\n"
            "Type any question about Saleamlak and I will answer!"
        )
        await query.edit_message_text(text, reply_markup=back_kb())

    elif data == "ask_ai":
        add_recent(user_id, "Started AI chat")
        await query.edit_message_text(
            "🤖 **AI Chat Mode**\n\n"
            "Type any question about Saleamlak!\n"
            "Examples:\n"
            '- "Who are you?"\n'
            '- "What projects have you built?"\n'
            '- "Can I hire you?"\n'
            '- "What technologies do you know?"\n\n'
            "Type /new to clear chat history.",
            reply_markup=back_kb(),
        )


async def addfav_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    item = text.replace("/addfav", "").strip()
    if not item:
        await update.message.reply_text(
            "Usage: /addfav <item>\nExample: /addfav Gulit E-commerce Project"
        )
        return
    udata = get_user_data(user_id)
    favs = udata.get("favorites", [])
    favs.append(item)
    update_user_data(user_id, {"favorites": favs})
    add_recent(user_id, f"Added favorite: {item}")
    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="back_main")]]
    await update.message.reply_text(
        f"✅ Added to favorites:\n\n  {item}",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="back_main")]]
    await update.message.reply_text(
        "Commands:\n"
        "/start - Main menu\n"
        "/addfav <item> - Add favorite\n"
        "/new - Clear AI chat history\n"
        "/help - This message\n\n"
        "Type any question to chat with AI!",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def new_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_sessions[user_id]["messages"] = []
    update_user_data(user_id, {"chat_count": 0})
    add_recent(user_id, "Cleared chat history")
    await update.message.reply_text("Chat history cleared!")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text

    if user_text.startswith("/addfav "):
        return

    udata = get_user_data(user_id)
    chat_count = udata.get("chat_count", 0) + 1
    update_user_data(user_id, {"chat_count": chat_count})

    user_sessions[user_id]["messages"].append(
        {"role": "user", "content": user_text}
    )

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(user_sessions[user_id]["messages"][-20:])

    await update.message.chat.send_action("typing")

    try:
        response = client.chat.completions.create(
            model="google/gemini-3.1-flash-lite-preview",
            messages=messages,
            max_tokens=1000,
            temperature=0.7,
        )

        assistant_reply = response.choices[0].message.content

        user_sessions[user_id]["messages"].append(
            {"role": "assistant", "content": assistant_reply}
        )

        add_recent(user_id, f"AI chat: {user_text[:30]}...")

        keyboard = [
            [InlineKeyboardButton("📂 Save to Favorites", callback_data="add_fav")],
            [InlineKeyboardButton("🔙 Back to Menu", callback_data="back_main")],
        ]
        await update.message.reply_text(
            assistant_reply, reply_markup=InlineKeyboardMarkup(keyboard)
        )

    except Exception as e:
        logger.error(f"API error: {e}")
        error_msg = str(e)
        if "api_key" in error_msg.lower() or "unauthorized" in error_msg.lower():
            await update.message.reply_text("API Key is invalid. Check your .env file.")
        elif "quota" in error_msg.lower():
            await update.message.reply_text("API quota exceeded.")
        else:
            await update.message.reply_text(f"Error: {error_msg[:200]}")


def main():
    if not TELEGRAM_TOKEN:
        raise ValueError("TELEGRAM_TOKEN not found!")
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY not found!")

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("new", new_conversation))
    app.add_handler(CommandHandler("addfav", addfav_cmd))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot is starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
