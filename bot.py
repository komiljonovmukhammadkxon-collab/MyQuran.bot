import os
import asyncio
import logging
import urllib.request
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes
)
from telegram.error import BadRequest
from flask import Flask

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = os.getenv("BOT_TOKEN")

# Telegram URL orqali audio chegarasi - 20 MB
MAX_AUDIO_SIZE = 19 * 1024 * 1024  # 19 MB xavfsiz chegara

RECITERS = {
    "alafasy": {
        "name": "Mishary Alafasy",
        "url": "https://download.quranicaudio.com/quran/mishaari_raashid_al_3afaasee/{:03d}.mp3"
    },
    "dosari": {
        "name": "Yasser Al-Dosari",
        "url": "https://download.quranicaudio.com/quran/yasser_ad-dussary/{:03d}.mp3"
    }
}

SURAHS = [
    None,
    {"name_uz": "Al-Fotiha", "name_ar": "الفاتحة", "name_en": "Al-Fatihah", "ayahs": 7, "place": "Makka"},
    {"name_uz": "Al-Baqara", "name_ar": "البقرة", "name_en": "Al-Baqarah", "ayahs": 286, "place": "Madina"},
    {"name_uz": "Ali-Imron", "name_ar": "آل عمران", "name_en": "Aal-E-Imran", "ayahs": 200, "place": "Madina"},
    {"name_uz": "An-Niso", "name_ar": "النساء", "name_en": "An-Nisa", "ayahs": 176, "place": "Madina"},
    {"name_uz": "Al-Moida", "name_ar": "المائدة", "name_en": "Al-Maidah", "ayahs": 120, "place": "Madina"},
    {"name_uz": "Al-Anom", "name_ar": "الأنعام", "name_en": "Al-Anam", "ayahs": 165, "place": "Makka"},
    {"name_uz": "Al-Aroaf", "name_ar": "الأعراف", "name_en": "Al-Araf", "ayahs": 206, "place": "Makka"},
    {"name_uz": "Al-Anfol", "name_ar": "الأنفال", "name_en": "Al-Anfal", "ayahs": 75, "place": "Madina"},
    {"name_uz": "At-Tavba", "name_ar": "التوبة", "name_en": "At-Tawbah", "ayahs": 129, "place": "Madina"},
    {"name_uz": "Yunus", "name_ar": "يونس", "name_en": "Yunus", "ayahs": 109, "place": "Makka"},
    {"name_uz": "Hud", "name_ar": "هود", "name_en": "Hud", "ayahs": 123, "place": "Makka"},
    {"name_uz": "Yusuf", "name_ar": "يوسف", "name_en": "Yusuf", "ayahs": 111, "place": "Makka"},
    {"name_uz": "Ar-Rad", "name_ar": "الرعد", "name_en": "Ar-Rad", "ayahs": 43, "place": "Madina"},
    {"name_uz": "Ibrohim", "name_ar": "إبراهيم", "name_en": "Ibrahim", "ayahs": 52, "place": "Makka"},
    {"name_uz": "Al-Hijr", "name_ar": "الحجر", "name_en": "Al-Hijr", "ayahs": 99, "place": "Makka"},
    {"name_uz": "An-Nahl", "name_ar": "النحل", "name_en": "An-Nahl", "ayahs": 128, "place": "Makka"},
    {"name_uz": "Al-Isro", "name_ar": "الإسراء", "name_en": "Al-Isra", "ayahs": 111, "place": "Makka"},
    {"name_uz": "Al-Kahf", "name_ar": "الكهف", "name_en": "Al-Kahf", "ayahs": 110, "place": "Makka"},
    {"name_uz": "Maryam", "name_ar": "مريم", "name_en": "Maryam", "ayahs": 98, "place": "Makka"},
    {"name_uz": "Toha", "name_ar": "طه", "name_en": "Ta-Ha", "ayahs": 135, "place": "Makka"},
    {"name_uz": "Al-Anbiyo", "name_ar": "الأنبياء", "name_en": "Al-Anbiya", "ayahs": 112, "place": "Makka"},
    {"name_uz": "Al-Haj", "name_ar": "الحج", "name_en": "Al-Hajj", "ayahs": 78, "place": "Madina"},
    {"name_uz": "Al-Mo'minun", "name_ar": "المؤمنون", "name_en": "Al-Muminun", "ayahs": 118, "place": "Makka"},
    {"name_uz": "An-Nur", "name_ar": "النور", "name_en": "An-Nur", "ayahs": 64, "place": "Madina"},
    {"name_uz": "Al-Furqon", "name_ar": "الفرقان", "name_en": "Al-Furqan", "ayahs": 77, "place": "Makka"},
    {"name_uz": "Ash-Shuaro", "name_ar": "الشعراء", "name_en": "Ash-Shuara", "ayahs": 227, "place": "Makka"},
    {"name_uz": "An-Naml", "name_ar": "النمل", "name_en": "An-Naml", "ayahs": 93, "place": "Makka"},
    {"name_uz": "Al-Qasas", "name_ar": "القصص", "name_en": "Al-Qasas", "ayahs": 88, "place": "Makka"},
    {"name_uz": "Al-Ankabut", "name_ar": "العنكبوت", "name_en": "Al-Ankabut", "ayahs": 69, "place": "Makka"},
    {"name_uz": "Ar-Rum", "name_ar": "الروم", "name_en": "Ar-Rum", "ayahs": 60, "place": "Makka"},
    {"name_uz": "Luqmon", "name_ar": "لقمان", "name_en": "Luqman", "ayahs": 34, "place": "Makka"},
    {"name_uz": "As-Sajda", "name_ar": "السجدة", "name_en": "As-Sajdah", "ayahs": 30, "place": "Makka"},
    {"name_uz": "Al-Ahzob", "name_ar": "الأحزاب", "name_en": "Al-Ahzab", "ayahs": 73, "place": "Madina"},
    {"name_uz": "Saba", "name_ar": "سبأ", "name_en": "Saba", "ayahs": 54, "place": "Makka"},
    {"name_uz": "Fotir", "name_ar": "فاطر", "name_en": "Fatir", "ayahs": 45, "place": "Makka"},
    {"name_uz": "Yasin", "name_ar": "يس", "name_en": "Ya-Sin", "ayahs": 83, "place": "Makka"},
    {"name_uz": "As-Soffot", "name_ar": "الصافات", "name_en": "As-Saffat", "ayahs": 182, "place": "Makka"},
    {"name_uz": "Sod", "name_ar": "ص", "name_en": "Sad", "ayahs": 88, "place": "Makka"},
    {"name_uz": "Az-Zumar", "name_ar": "الزمر", "name_en": "Az-Zumar", "ayahs": 75, "place": "Makka"},
    {"name_uz": "G'ofir", "name_ar": "غافر", "name_en": "Ghafir", "ayahs": 85, "place": "Makka"},
    {"name_uz": "Fussilat", "name_ar": "فصلت", "name_en": "Fussilat", "ayahs": 54, "place": "Makka"},
    {"name_uz": "Ash-Shuro", "name_ar": "الشورى", "name_en": "Ash-Shura", "ayahs": 53, "place": "Makka"},
    {"name_uz": "Az-Zuxruf", "name_ar": "الزخرف", "name_en": "Az-Zukhruf", "ayahs": 89, "place": "Makka"},
    {"name_uz": "Ad-Duxon", "name_ar": "الدخان", "name_en": "Ad-Dukhan", "ayahs": 59, "place": "Makka"},
    {"name_uz": "Al-Josiya", "name_ar": "الجاثية", "name_en": "Al-Jathiyah", "ayahs": 37, "place": "Makka"},
    {"name_uz": "Al-Ahqof", "name_ar": "الأحقاف", "name_en": "Al-Ahqaf", "ayahs": 35, "place": "Makka"},
    {"name_uz": "Muhammad", "name_ar": "محمد", "name_en": "Muhammad", "ayahs": 38, "place": "Madina"},
    {"name_uz": "Al-Fath", "name_ar": "الفتح", "name_en": "Al-Fath", "ayahs": 29, "place": "Madina"},
    {"name_uz": "Al-Hujurot", "name_ar": "الحجرات", "name_en": "Al-Hujurat", "ayahs": 18, "place": "Madina"},
    {"name_uz": "Qof", "name_ar": "ق", "name_en": "Qaf", "ayahs": 45, "place": "Makka"},
    {"name_uz": "Az-Zariyot", "name_ar": "الذاريات", "name_en": "Adh-Dhariyat", "ayahs": 60, "place": "Makka"},
    {"name_uz": "At-Tur", "name_ar": "الطور", "name_en": "At-Tur", "ayahs": 49, "place": "Makka"},
    {"name_uz": "An-Najm", "name_ar": "النجم", "name_en": "An-Najm", "ayahs": 62, "place": "Makka"},
    {"name_uz": "Al-Qamar", "name_ar": "القمر", "name_en": "Al-Qamar", "ayahs": 55, "place": "Makka"},
    {"name_uz": "Ar-Rahmon", "name_ar": "الرحمن", "name_en": "Ar-Rahman", "ayahs": 78, "place": "Madina"},
    {"name_uz": "Al-Voqia", "name_ar": "الواقعة", "name_en": "Al-Waqiah", "ayahs": 96, "place": "Makka"},
    {"name_uz": "Al-Hadid", "name_ar": "الحديد", "name_en": "Al-Hadid", "ayahs": 29, "place": "Madina"},
    {"name_uz": "Al-Mujodila", "name_ar": "المجادلة", "name_en": "Al-Mujadilah", "ayahs": 22, "place": "Madina"},
    {"name_uz": "Al-Hashr", "name_ar": "الحشر", "name_en": "Al-Hashr", "ayahs": 24, "place": "Madina"},
    {"name_uz": "Al-Mumtahana", "name_ar": "الممتحنة", "name_en": "Al-Mumtahanah", "ayahs": 13, "place": "Madina"},
    {"name_uz": "As-Saff", "name_ar": "الصف", "name_en": "As-Saff", "ayahs": 14, "place": "Madina"},
    {"name_uz": "Al-Jumua", "name_ar": "الجمعة", "name_en": "Al-Jumuah", "ayahs": 11, "place": "Madina"},
    {"name_uz": "Al-Munofiqun", "name_ar": "المنافقون", "name_en": "Al-Munafiqun", "ayahs": 11, "place": "Madina"},
    {"name_uz": "At-Tag'obun", "name_ar": "التغابن", "name_en": "At-Taghabun", "ayahs": 18, "place": "Madina"},
    {"name_uz": "At-Taloq", "name_ar": "الطلاق", "name_en": "At-Talaq", "ayahs": 12, "place": "Madina"},
    {"name_uz": "At-Tahrim", "name_ar": "التحريم", "name_en": "At-Tahrim", "ayahs": 12, "place": "Madina"},
    {"name_uz": "Al-Mulk", "name_ar": "الملك", "name_en": "Al-Mulk", "ayahs": 30, "place": "Makka"},
    {"name_uz": "Al-Qalam", "name_ar": "القلم", "name_en": "Al-Qalam", "ayahs": 52, "place": "Makka"},
    {"name_uz": "Al-Haqqa", "name_ar": "الحاقة", "name_en": "Al-Haqqah", "ayahs": 52, "place": "Makka"},
    {"name_uz": "Al-Maorij", "name_ar": "المعارج", "name_en": "Al-Maarij", "ayahs": 44, "place": "Makka"},
    {"name_uz": "Nuh", "name_ar": "نوح", "name_en": "Nuh", "ayahs": 28, "place": "Makka"},
    {"name_uz": "Al-Jin", "name_ar": "الجن", "name_en": "Al-Jinn", "ayahs": 28, "place": "Makka"},
    {"name_uz": "Al-Muzzammil", "name_ar": "المزمل", "name_en": "Al-Muzzammil", "ayahs": 20, "place": "Makka"},
    {"name_uz": "Al-Muddassir", "name_ar": "المدثر", "name_en": "Al-Muddathir", "ayahs": 56, "place": "Makka"},
    {"name_uz": "Al-Qiyoma", "name_ar": "القيامة", "name_en": "Al-Qiyamah", "ayahs": 40, "place": "Makka"},
    {"name_uz": "Al-Inson", "name_ar": "الإنسان", "name_en": "Al-Insan", "ayahs": 31, "place": "Madina"},
    {"name_uz": "Al-Mursalot", "name_ar": "المرسلات", "name_en": "Al-Mursalat", "ayahs": 50, "place": "Makka"},
    {"name_uz": "An-Naba", "name_ar": "النبأ", "name_en": "An-Naba", "ayahs": 40, "place": "Makka"},
    {"name_uz": "An-Naziot", "name_ar": "النازعات", "name_en": "An-Naziat", "ayahs": 46, "place": "Makka"},
    {"name_uz": "Abasa", "name_ar": "عبس", "name_en": "Abasa", "ayahs": 42, "place": "Makka"},
    {"name_uz": "At-Takvir", "name_ar": "التكوير", "name_en": "At-Takwir", "ayahs": 29, "place": "Makka"},
    {"name_uz": "Al-Infitor", "name_ar": "الإنفطار", "name_en": "Al-Infitar", "ayahs": 19, "place": "Makka"},
    {"name_uz": "Al-Mutaffifin", "name_ar": "المطففين", "name_en": "Al-Mutaffifin", "ayahs": 36, "place": "Makka"},
    {"name_uz": "Al-Inshiqoq", "name_ar": "الإنشقاق", "name_en": "Al-Inshiqaq", "ayahs": 25, "place": "Makka"},
    {"name_uz": "Al-Buruj", "name_ar": "البروج", "name_en": "Al-Buruj", "ayahs": 22, "place": "Makka"},
    {"name_uz": "At-Toriq", "name_ar": "الطارق", "name_en": "At-Tariq", "ayahs": 17, "place": "Makka"},
    {"name_uz": "Al-Alo", "name_ar": "الأعلى", "name_en": "Al-Ala", "ayahs": 19, "place": "Makka"},
    {"name_uz": "Al-G'oshiya", "name_ar": "الغاشية", "name_en": "Al-Ghashiyah", "ayahs": 26, "place": "Makka"},
    {"name_uz": "Al-Fajr", "name_ar": "الفجر", "name_en": "Al-Fajr", "ayahs": 30, "place": "Makka"},
    {"name_uz": "Al-Balad", "name_ar": "البلد", "name_en": "Al-Balad", "ayahs": 20, "place": "Makka"},
    {"name_uz": "Ash-Shams", "name_ar": "الشمس", "name_en": "Ash-Shams", "ayahs": 15, "place": "Makka"},
    {"name_uz": "Al-Layl", "name_ar": "الليل", "name_en": "Al-Layl", "ayahs": 21, "place": "Makka"},
    {"name_uz": "Ad-Duho", "name_ar": "الضحى", "name_en": "Ad-Duha", "ayahs": 11, "place": "Makka"},
    {"name_uz": "Ash-Sharh", "name_ar": "الشرح", "name_en": "Ash-Sharh", "ayahs": 8, "place": "Makka"},
    {"name_uz": "At-Tin", "name_ar": "التين", "name_en": "At-Tin", "ayahs": 8, "place": "Makka"},
    {"name_uz": "Al-Alaq", "name_ar": "العلق", "name_en": "Al-Alaq", "ayahs": 19, "place": "Makka"},
    {"name_uz": "Al-Qadr", "name_ar": "القدر", "name_en": "Al-Qadr", "ayahs": 5, "place": "Makka"},
    {"name_uz": "Al-Bayyina", "name_ar": "البينة", "name_en": "Al-Bayyinah", "ayahs": 8, "place": "Madina"},
    {"name_uz": "Az-Zalzala", "name_ar": "الزلزلة", "name_en": "Az-Zalzalah", "ayahs": 8, "place": "Madina"},
    {"name_uz": "Al-Odiyot", "name_ar": "العاديات", "name_en": "Al-Adiyat", "ayahs": 11, "place": "Makka"},
    {"name_uz": "Al-Qoria", "name_ar": "القارعة", "name_en": "Al-Qariah", "ayahs": 11, "place": "Makka"},
    {"name_uz": "At-Takosur", "name_ar": "التكاثر", "name_en": "At-Takathur", "ayahs": 8, "place": "Makka"},
    {"name_uz": "Al-Asr", "name_ar": "العصر", "name_en": "Al-Asr", "ayahs": 3, "place": "Makka"},
    {"name_uz": "Al-Humaza", "name_ar": "الهمزة", "name_en": "Al-Humazah", "ayahs": 9, "place": "Makka"},
    {"name_uz": "Al-Fil", "name_ar": "الفيل", "name_en": "Al-Fil", "ayahs": 5, "place": "Makka"},
    {"name_uz": "Quraysh", "name_ar": "قريش", "name_en": "Quraysh", "ayahs": 4, "place": "Makka"},
    {"name_uz": "Al-Mo'un", "name_ar": "الماعون", "name_en": "Al-Maun", "ayahs": 7, "place": "Makka"},
    {"name_uz": "Al-Kavsar", "name_ar": "الكوثر", "name_en": "Al-Kawthar", "ayahs": 3, "place": "Makka"},
    {"name_uz": "Al-Kofirun", "name_ar": "الكافرون", "name_en": "Al-Kafirun", "ayahs": 6, "place": "Makka"},
    {"name_uz": "An-Nasr", "name_ar": "النصر", "name_en": "An-Nasr", "ayahs": 3, "place": "Madina"},
    {"name_uz": "Al-Masad", "name_ar": "المسد", "name_en": "Al-Masad", "ayahs": 5, "place": "Makka"},
    {"name_uz": "Al-Ixlos", "name_ar": "الإخلاص", "name_en": "Al-Ikhlas", "ayahs": 4, "place": "Makka"},
    {"name_uz": "Al-Falaq", "name_ar": "الفلق", "name_en": "Al-Falaq", "ayahs": 5, "place": "Makka"},
    {"name_uz": "An-Nas", "name_ar": "الناس", "name_en": "An-Nas", "ayahs": 6, "place": "Madina"},
]

def find_surah(query):
    query = query.strip().lower()
    if query.isdigit():
        num = int(query)
        if 1 <= num <= 114:
            return num, SURAHS[num]
        return None, None
    for i in range(1, 115):
        s = SURAHS[i]
        names = [
            s["name_uz"].lower(),
            s["name_en"].lower(),
            s["name_ar"],
            s["name_uz"].lower().replace("'", "").replace("-", ""),
            s["name_en"].lower().replace("-", ""),
        ]
        for n in names:
            if query == n.lower() or query in n.lower() or n.lower() in query:
                return i, s
    return None, None

def get_file_size(url):
    """Audio fayl o'lchamini tekshirish (HEAD request)"""
    try:
        req = urllib.request.Request(url, method='HEAD')
        with urllib.request.urlopen(req, timeout=10) as r:
            return int(r.headers.get('Content-Length', 0))
    except Exception as e:
        logging.error(f"Size check error: {e}")
        return 0

WELCOME_TEXT = (
    "🕌 *Assalomu alaykum!*\n\n"
    "Bu bot Qur'oni Karim suralarini ovoz bilan yuboradi.\n\n"
    "📖 *Sura raqami yoki nomini yozing:*\n\n"
    "Masalan:\n"
    "• `36` yoki `Yasin`\n"
    "• `112` yoki `Al-Ixlos`\n"
    "• `1` yoki `Al-Fotiha`"
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME_TEXT, parse_mode="Markdown")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    text = update.message.text.strip()
    greetings = ["salom", "assalom", "hi", "hello", "menu", "start", "boshla", "help", "yordam"]
    if text.lower() in greetings:
        await update.message.reply_text(WELCOME_TEXT, parse_mode="Markdown")
        return
    surah_num, surah = find_surah(text)
    if not surah:
        await update.message.reply_text(
            "❌ *Sura topilmadi*\n\n"
            "Iltimos, 1 dan 114 gacha bo'lgan raqam yoki sura nomini yuboring.\n\n"
            "Masalan: `36` yoki `Yasin`",
            parse_mode="Markdown"
        )
        return
    keyboard = [
        [InlineKeyboardButton("🎙️ Mishary Alafasy", callback_data=f"play_alafasy_{surah_num}")],
        [InlineKeyboardButton("🎙️ Yasser Al-Dosari", callback_data=f"play_dosari_{surah_num}")]
    ]
    info_text = (
        f"📖 *{surah_num}. {surah['name_uz']}*\n"
        f"🕋 {surah['name_ar']}\n\n"
        f"📊 Oyatlar: {surah['ayahs']} | Joyi: {surah['place']}\n\n"
        f"👇 *Qori tanlang:*"
    )
    await update.message.reply_text(
        info_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def play_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer("⏳ Tayyorlanmoqda...")
    except BadRequest:
        return

    parts = query.data.split("_")
    if len(parts) != 3:
        return

    reciter_key = parts[1]
    surah_num = int(parts[2])

    if reciter_key not in RECITERS or not (1 <= surah_num <= 114):
        return

    reciter = RECITERS[reciter_key]
    surah = SURAHS[surah_num]
    audio_url = reciter["url"].format(surah_num)

    # Avval fayl o'lchamini tekshiramiz (asyncio orqali, blok qilmasdan)
    loop = asyncio.get_event_loop()
    file_size = await loop.run_in_executor(None, get_file_size, audio_url)
    file_size_mb = file_size / 1024 / 1024

    caption = (
        f"📖 *{surah_num}. {surah['name_uz']}*\n"
        f"🕋 {surah['name_ar']}\n\n"
        f"📊 Oyatlar: {surah['ayahs']} | Joyi: {surah['place']}\n"
        f"🎙️ Qori: {reciter['name']}"
    )

    # Agar fayl kichik bo'lsa - to'g'ridan-to'g'ri audio yuborish
    if 0 < file_size <= MAX_AUDIO_SIZE:
        try:
            await query.message.reply_audio(
                audio=audio_url,
                caption=caption,
                parse_mode="Markdown",
                title=f"{surah_num}. {surah['name_en']}",
                performer=reciter['name']
            )
            return
        except Exception as e:
            logging.error(f"Audio yuborish xatosi: {e}")
            # Xato bo'lsa link bilan davom etamiz

    # Katta fayl yoki xato - link sifatida yuborish
    link_text = (
        f"{caption}\n"
        f"💾 Fayl o'lchami: {file_size_mb:.1f} MB\n\n"
        f"⚠️ *Bu sura juda katta, audio fayl sifatida yuborib bo'lmadi.*\n\n"
        f"🎧 [Tinglash uchun bosing]({audio_url})\n"
        f"📥 Yoki linkni telefonda ushlab \"Save link\" qiling"
    )

    try:
        await query.message.reply_text(
            link_text,
            parse_mode="Markdown",
            disable_web_page_preview=False
        )
    except Exception as e:
        logging.error(f"Link yuborish xatosi: {e}")
        await query.message.reply_text(
            f"❌ Xato yuz berdi.\n\n"
            f"Audio link:\n{audio_url}"
        )

async def error_handler(update, context):
    logging.error(f"Xato: {context.error}")

app_web = Flask(__name__)

@app_web.route("/")
def home():
    return "Quran Bot ishlayapti ✅"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app_web.run(host="0.0.0.0", port=port)

def main():
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    except Exception:
        pass
    Thread(target=run_web, daemon=True).start()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(play_callback, pattern="^play_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
