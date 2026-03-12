import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler, PreCheckoutQueryHandler

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

from groq import Groq
client = Groq(api_key=GROQ_API_KEY)

user_state = {}
user_requests = {}
user_lang = {}
user_paid = {}

FREE_LIMIT = 3
STARS_PRICE = 50  # 50 Telegram Stars = ~1$

TEXTS = {
    "ru": {
        "welcome": (
            "👋 Привет! Я <b>Career Suite Bot</b>.\n\n"
            "Помогу прокачать карьеру:\n"
            "🔥 Разбор резюме\n"
            "✉️ Сопроводительное письмо\n"
            "🎤 Подготовка к интервью\n"
            "💼 LinkedIn Bio\n\n"
            "🆓 <b>Бесплатно:</b> 3 запроса\n"
            "🌐 <b>Все инструменты бесплатны</b> на сайте: career-suite-seven.vercel.app\n\n"
            "Выбери инструмент:"
        ),
        "roast_btn": "🔥 Разбор резюме",
        "cover_btn": "✉️ Сопроводительное письмо",
        "interview_btn": "🎤 Подготовка к интервью",
        "linkedin_btn": "💼 LinkedIn Bio",
        "pro_btn": "⭐ Купить Pro — 50 Stars",
        "site_btn": "🌐 Бесплатно на сайте",
        "lang_btn": "🇬🇧 Switch to English",
        "roast_prompt": "📄 Отправь своё резюме — дам честную оценку, найду слабые места и скажу что улучшить.",
        "cover_prompt": "📄 Отправь резюме и описание вакансии.\n\nФормат:\n[твоё резюме]\n---\n[описание вакансии]",
        "interview_prompt": "📄 Отправь описание вакансии — подготовлю 10 вопросов которые скорее всего зададут, с готовыми ответами.",
        "linkedin_prompt": "📄 Отправь резюме — напишу профессиональный LinkedIn Bio который выделит тебя среди других.",
        "rewrite_btn": "✨ Переписать резюме",
        "rewrite_prompt": "📄 Отправь своё резюме — перепишу его так, чтобы оно выглядело профессионально и цепляло рекрутеров.",
        "rewrite_sys": "Ты профессиональный карьерный коуч. Перепиши резюме пользователя: сделай его чётким, профессиональным, с сильными глаголами и конкретными достижениями. Сохрани структуру но улучши каждый пункт. Отвечай на русском.",
        "limit_reached": (
            "❌ <b>Бесплатные запросы закончились</b>\n\n"
            "Варианты:\n"
            "⭐ Купить Pro за 50 Telegram Stars\n"
            "🌐 Использовать бесплатно на сайте: career-suite-seven.vercel.app"
        ),
        "generating": "⏳ Генерирую...",
        "done": "✅ Готово! Осталось бесплатных запросов: {}",
        "done_pro": "✅ Готово! У тебя Pro доступ ⭐",
        "no_tool": "Выбери инструмент — /start",
        "pay_title": "Career Suite Pro",
        "pay_desc": "50 запросов к AI карьерным инструментам",
        "pay_success": "🎉 Оплата прошла! Теперь у тебя <b>50 запросов</b> ⭐\n\nИспользуй /start чтобы начать.",
        "error": "❌ Ошибка: {}",
        "roast_sys": "Ты жёсткий но честный карьерный коуч. Разбери резюме: дай оценку 0-100, укажи 5 слабых мест и 5 конкретных улучшений. Отвечай на русском.",
        "cover_sys": "Ты профессиональный HR. Напиши сопроводительное письмо на основе резюме и вакансии (разделены ---). Отвечай на русском.",
        "interview_sys": "Ты опытный интервьюер. Подготовь 10 вероятных вопросов с ответами на основе описания вакансии. Отвечай на русском.",
        "linkedin_sys": "Ты профессиональный копирайтер. Создай LinkedIn Bio на основе резюме. Кратко, профессионально. Отвечай на русском.",
        "menu_btn": "🏠 Главное меню",
        "rewrite_after_roast_btn": "✨ Теперь перепиши его",
        "copy_hint": "☝️ Нажми и удержи текст выше чтобы скопировать",
    },
    "en": {
        "welcome": (
            "👋 Hi! I'm <b>Career Suite Bot</b>.\n\n"
            "I'll help boost your career:\n"
            "🔥 Resume Roast\n"
            "✉️ Cover Letter\n"
            "🎤 Interview Prep\n"
            "💼 LinkedIn Bio\n\n"
            "🆓 <b>Free:</b> 3 requests\n"
            "🌐 <b>All tools are free</b> on the website: career-suite-seven.vercel.app\n\n"
            "Choose a tool:"
        ),
        "roast_btn": "🔥 Resume Roast",
        "cover_btn": "✉️ Cover Letter",
        "interview_btn": "🎤 Interview Prep",
        "linkedin_btn": "💼 LinkedIn Bio",
        "pro_btn": "⭐ Buy Pro — 50 Stars",
        "site_btn": "🌐 Free on website",
        "lang_btn": "🇷🇺 Переключить на русский",
        "roast_prompt": "📄 Send your resume — I'll give an honest score, find weak spots and tell you exactly what to improve.",
        "cover_prompt": "📄 Send your resume and job description.\n\nFormat:\n[your resume]\n---\n[job description]",
        "interview_prompt": "📄 Send job description — I'll prepare 10 likely interview questions with strong answers.",
        "linkedin_prompt": "📄 Send your resume — I'll write a professional LinkedIn Bio that makes you stand out.",
        "rewrite_btn": "✨ Rewrite Resume",
        "rewrite_prompt": "📄 Send your resume — I'll rewrite it to look professional and catch recruiters' attention.",
        "rewrite_sys": "You are a professional career coach. Rewrite user's resume: make it clear, professional, with strong action verbs and specific achievements. Keep the structure but improve every point. Reply in English.",
        "limit_reached": (
            "❌ <b>Free requests used up</b>\n\n"
            "Options:\n"
            "⭐ Buy Pro for 50 Telegram Stars\n"
            "🌐 Use for free on the website: career-suite-seven.vercel.app"
        ),
        "generating": "⏳ Generating...",
        "done": "✅ Done! Free requests left: {}",
        "done_pro": "✅ Done! You have Pro access ⭐",
        "no_tool": "Choose a tool — /start",
        "pay_title": "Career Suite Pro",
        "pay_desc": "50 requests to AI career tools",
        "pay_success": "🎉 Payment successful! You now have <b>50 requests</b> ⭐\n\nUse /start to begin.",
        "error": "❌ Error: {}",
        "roast_sys": "You are a harsh but honest career coach. Review the resume: give a score 0-100, list 5 weaknesses and 5 concrete improvements. Reply in English.",
        "cover_sys": "You are a professional HR. Write a cover letter based on the resume and job description (separated by ---). Reply in English.",
        "interview_sys": "You are an experienced interviewer. Prepare 10 likely questions with answers based on the job description. Reply in English.",
        "linkedin_sys": "You are a professional copywriter. Create a LinkedIn Bio based on the resume. Keep it brief and professional. Reply in English.",
        "menu_btn": "🏠 Main Menu",
        "rewrite_after_roast_btn": "✨ Now rewrite it",
        "copy_hint": "☝️ Press and hold the text above to copy",
    }
}

def t(user_id, key):
    lang = user_lang.get(user_id, "ru")
    return TEXTS[lang][key]

def get_requests(user_id):
    return user_requests.get(user_id, 0)

def increment_requests(user_id):
    user_requests[user_id] = get_requests(user_id) + 1

def has_access(user_id):
    paid = user_paid.get(user_id, 0)
    if paid > 0:
        return True
    return get_requests(user_id) < FREE_LIMIT

def main_keyboard(user_id):
    lang = user_lang.get(user_id, "ru")
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t(user_id, "roast_btn"), callback_data="roast")],
        [InlineKeyboardButton(t(user_id, "cover_btn"), callback_data="cover")],
        [InlineKeyboardButton(t(user_id, "interview_btn"), callback_data="interview")],
        [InlineKeyboardButton(t(user_id, "linkedin_btn"), callback_data="linkedin")],
        [InlineKeyboardButton(t(user_id, "rewrite_btn"), callback_data="rewrite")],
        [InlineKeyboardButton(t(user_id, "pro_btn"), callback_data="buy_pro")],
        [InlineKeyboardButton(t(user_id, "site_btn"), url="https://career-suite-seven.vercel.app")],
        [InlineKeyboardButton(t(user_id, "lang_btn"), callback_data="switch_lang")],
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text(
        t(user_id, "welcome"),
        reply_markup=main_keyboard(user_id),
        parse_mode="HTML"
    )

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text(
        t(user_id, "welcome"),
        reply_markup=main_keyboard(user_id),
        parse_mode="HTML"
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "switch_lang":
        current = user_lang.get(user_id, "ru")
        user_lang[user_id] = "en" if current == "ru" else "ru"
        await query.message.reply_text(
            t(user_id, "welcome"),
            reply_markup=main_keyboard(user_id),
            parse_mode="HTML"
        )
        return

    if query.data == "main_menu":
        await query.message.reply_text(
            t(user_id, "welcome"),
            reply_markup=main_keyboard(user_id),
            parse_mode="HTML"
        )
        return

    if query.data == "buy_pro":
        lang = user_lang.get(user_id, "ru")
        await context.bot.send_invoice(
            chat_id=user_id,
            title=t(user_id, "pay_title"),
            description=t(user_id, "pay_desc"),
            payload="pro_50_requests",
            provider_token="",
            currency="XTR",  # Telegram Stars
            prices=[LabeledPrice(label="Pro", amount=STARS_PRICE)],
        )
        return

    if not has_access(user_id):
        await query.message.reply_text(
            t(user_id, "limit_reached"),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(t(user_id, "pro_btn"), callback_data="buy_pro")],
                [InlineKeyboardButton(t(user_id, "site_btn"), url="https://career-suite-seven.vercel.app")],
            ]),
            parse_mode="HTML"
        )
        return

    user_state[user_id] = query.data
    prompts = {
        "roast": t(user_id, "roast_prompt"),
        "cover": t(user_id, "cover_prompt"),
        "interview": t(user_id, "interview_prompt"),
        "linkedin": t(user_id, "linkedin_prompt"),
        "rewrite": t(user_id, "rewrite_prompt"),
    }
    await query.message.reply_text(
        prompts[query.data],
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(t(user_id, "menu_btn"), callback_data="main_menu")]
        ])
    )

async def precheckout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.pre_checkout_query.answer(ok=True)

async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_paid[user_id] = user_paid.get(user_id, 0) + 50
    await update.message.reply_text(
        t(user_id, "pay_success"),
        parse_mode="HTML"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = user_state.get(user_id)

    if not state:
        await update.message.reply_text(t(user_id, "no_tool"))
        return

    if not has_access(user_id):
        await update.message.reply_text(
            t(user_id, "limit_reached"),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(t(user_id, "pro_btn"), callback_data="buy_pro")],
                [InlineKeyboardButton(t(user_id, "site_btn"), url="https://career-suite-seven.vercel.app")],
            ]),
            parse_mode="HTML"
        )
        return

    text = update.message.text
    await update.message.reply_text(t(user_id, "generating"))

    sys_key = f"{state}_sys"
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": t(user_id, sys_key)},
                {"role": "user", "content": text}
            ],
            max_tokens=1000
        )
        result = response.choices[0].message.content

        paid = user_paid.get(user_id, 0)
        if paid > 0:
            user_paid[user_id] -= 1
            status_msg = t(user_id, "done_pro")
        else:
            increment_requests(user_id)
            remaining = FREE_LIMIT - get_requests(user_id)
            status_msg = t(user_id, "done").format(remaining)

        if state == "roast":
            await update.message.reply_text(result)
            await update.message.reply_text(
                t(user_id, "copy_hint"),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(t(user_id, "rewrite_after_roast_btn"), callback_data="rewrite")],
                    [InlineKeyboardButton(t(user_id, "menu_btn"), callback_data="main_menu")],
                ])
            )
        else:
            await update.message.reply_text(result)
            await update.message.reply_text(
                t(user_id, "copy_hint"),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(t(user_id, "menu_btn"), callback_data="main_menu")],
                ])
            )

        await update.message.reply_text(status_msg)
        user_state[user_id] = None

    except Exception as e:
        await update.message.reply_text(t(user_id, "error").format(str(e)))

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(PreCheckoutQueryHandler(precheckout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
