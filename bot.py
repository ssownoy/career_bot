import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = "8729966128:AAHRfG54_PiLU7zklY9O3KDhqocsVf8jLMk"
GROQ_API_KEY = "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"  # вставь свой ключ

from groq import Groq
client = Groq(api_key=GROQ_API_KEY)

user_state = {}
user_requests = {}
FREE_LIMIT = 3

def get_requests(user_id):
    return user_requests.get(user_id, 0)

def increment_requests(user_id):
    user_requests[user_id] = get_requests(user_id) + 1

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔥 Разбор резюме", callback_data="roast")],
        [InlineKeyboardButton("✉️ Сопроводительное письмо", callback_data="cover")],
        [InlineKeyboardButton("🎤 Подготовка к интервью", callback_data="interview")],
        [InlineKeyboardButton("💼 LinkedIn Bio", callback_data="linkedin")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "👋 Привет! Я Career Suite Bot.\n\n"
        "Помогу с карьерой:\n"
        "🔥 Разберу резюме\n"
        "✉️ Напишу сопроводительное письмо\n"
        "🎤 Подготовлю к интервью\n"
        "💼 Создам LinkedIn Bio\n\n"
        f"Бесплатно: {FREE_LIMIT} запроса. Выбери инструмент:",
        reply_markup=reply_markup
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if get_requests(user_id) >= FREE_LIMIT:
        await query.message.reply_text("❌ Лимит исчерпан. Pro версия скоро будет доступна!")
        return

    user_state[user_id] = query.data
    
    prompts = {
        "roast": "📄 Отправь текст своего резюме — разберу по косточкам!",
        "cover": "📄 Отправь резюме и описание вакансии через\n\n---\n\nНапример:\n[резюме]\n---\n[вакансия]",
        "interview": "📄 Отправь описание вакансии — подготовлю 10 вопросов с ответами!",
        "linkedin": "📄 Отправь резюме — создам LinkedIn Bio!",
    }
    await query.message.reply_text(prompts[query.data])

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = user_state.get(user_id)
    
    if not state:
        await update.message.reply_text("Выбери инструмент командой /start")
        return
    
    if get_requests(user_id) >= FREE_LIMIT:
        await update.message.reply_text("❌ Лимит исчерпан. Pro версия скоро будет доступна!")
        return

    text = update.message.text
    await update.message.reply_text("⏳ Генерирую...")

    system_prompts = {
        "roast": "Ты жёсткий но честный карьерный коуч. Разбери резюме: дай оценку 0-100, укажи 5 слабых мест и 5 конкретных улучшений. Отвечай на русском.",
        "cover": "Ты профессиональный HR. Напиши сопроводительное письмо на основе резюме и вакансии (разделены ---). Отвечай на русском.",
        "interview": "Ты опытный интервьюер. Подготовь 10 вероятных вопросов с ответами на основе описания вакансии. Отвечай на русском.",
        "linkedin": "Ты профессиональный копирайтер. Создай LinkedIn Bio на основе резюме. Кратко, профессионально. Отвечай на русском.",
    }

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompts[state]},
                {"role": "user", "content": text}
            ],
            max_tokens=1000
        )
        result = response.choices[0].message.content
        increment_requests(user_id)
        remaining = FREE_LIMIT - get_requests(user_id)
        
        await update.message.reply_text(result)
        await update.message.reply_text(f"✅ Готово! Осталось бесплатных запросов: {remaining}")
        user_state[user_id] = None
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
