import os
import re
import json
import requests
import asyncio
import subprocess
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

BOT_TOKEN = os.environ.get("BOT_TOKEN", "SEU_TOKEN_DO_BOT_AQUI")
MY_TARGET_ID = os.environ.get("MY_TARGET_ID", "SEU ID DO TELEGRAM")
OWNER_NAME = "LEOMODZOFC"
BOT_NAME = "𝐋𝐄𝐎 𝐌𝐃𝐙 𝐁𝐎𝐓"
VERSION = "V1.0"

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

is_bot_active = True
total_messages = 0
total_downloads = 0
bot_start_time = datetime.now()

def menu_principal():
    keyboard = [
        [
            InlineKeyboardButton("🎵 BAIXAR MÚSICA", callback_data="baixar"),
            InlineKeyboardButton("🆘 AJUDA", callback_data="ajuda")
        ],
        [
            InlineKeyboardButton("🎨 GERAR IMAGEM", callback_data="gerar_img"),
            InlineKeyboardButton("👑 CRIADOR", callback_data="criador")
        ],
        [
            InlineKeyboardButton("⚙️ PAINEL ADMIN", callback_data="admin_panel")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def menu_baixar():
    keyboard = [
        [
            InlineKeyboardButton("🎵 COMO BAIXAR", callback_data="tutorial"),
            InlineKeyboardButton("📝 EXEMPLOS", callback_data="exemplos")
        ],
        [
            InlineKeyboardButton("📂 VER DOWNLOADS", callback_data="yt_list"),
            InlineKeyboardButton("🧹 LIMPAR", callback_data="yt_clean")
        ],
        [
            InlineKeyboardButton("🔙 VOLTAR", callback_data="voltar_inicio")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def menu_imagem():
    keyboard = [
        [
            InlineKeyboardButton("🎨 GERAR IMAGEM", callback_data="gerar_imagem_agora"),
            InlineKeyboardButton("📖 COMO USAR", callback_data="tutorial_img")
        ],
        [
            InlineKeyboardButton("🔙 VOLTAR", callback_data="voltar_inicio")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def menu_admin():
    global is_bot_active
    btn_status = "🔴 PARAR BOT" if is_bot_active else "🟢 LIGAR BOT"
    cb_status = "stop_bot" if is_bot_active else "start_bot"
    keyboard = [
        [
            InlineKeyboardButton("📊 STATUS", callback_data="status"),
            InlineKeyboardButton("📈 ESTATÍSTICAS", callback_data="stats")
        ],
        [
            InlineKeyboardButton(btn_status, callback_data=cb_status),
            InlineKeyboardButton("🔄 REINICIAR", callback_data="restart")
        ],
        [
            InlineKeyboardButton("🔙 VOLTAR", callback_data="voltar_inicio")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_ai_response(message):
    m = message.lower()
    replies = {
        "ola": f"🌟 Olá! Seja bem-vindo ao {BOT_NAME}!\n🎵 Use /lp + nome da música para baixar!",
        "olá": f"🌟 Olá! Seja bem-vindo ao {BOT_NAME}!\n🎵 Use /lp + nome da música para baixar!",
        "oi": f"👋 Oi! Que bom te ver por aqui!\n🎵 Quer baixar uma música? Use /lp!",
        "bom dia": f"🌅 Bom dia! Que seu dia seja incrível!\n🎵 Use /lp para ouvir suas músicas favoritas!",
        "boa tarde": f"☀️ Boa tarde! Pronto para relaxar?\n🎵 Digite /lp + nome da música!",
        "boa noite": f"🌙 Boa noite! A música perfeita para encerrar o dia?\n🎵 Use /lp e descubra!",
        "obrigado": f"🤝 Por nada! Sempre que precisar, estou aqui!\n🎵 Use /lp para mais músicas!",
        "obrigada": f"🤝 De nada! Foi um prazer ajudar!\n🎵 Use /lp quando quiser!",
        "valeu": f"💪 Valeu você! Conta comigo sempre!\n🎵 Manda um /lp aí!",
        "música": f"🎵 Quer baixar uma música?\nUse: /lp nome da música\nExemplo: /lp imagine dragons believer",
        "musica": f"🎵 Quer baixar uma música?\nUse: /lp nome da música\nExemplo: /lp henrique e juliano",
        "tocar": f"🎵 Quer tocar uma música?\nUse /lp + nome!\nEx: /lp metallica nothing",
        "ouvir": f"🎧 Vamos ouvir algo bom?\nUse /lp + nome da música!",
        "imagem": f"🎨 Quer gerar uma imagem?\nClique no menu /start e escolha GERAR IMAGEM!",
        "foto": f"🎨 Quer gerar uma imagem?\nClique no menu /start e escolha GERAR IMAGEM!",
    }
    for key, reply in replies.items():
        if key in m:
            return reply
    return f"💬 Use /lp + nome da música para baixar MP3 do YouTube!\n📝 Exemplo: /lp imagine dragons believer 🎵"

def check_deps():
    try:
        subprocess.run("yt-dlp --version", shell=True, capture_output=True, timeout=5)
        subprocess.run("ffmpeg -version", shell=True, capture_output=True, timeout=5)
        return True
    except:
        return False

def search_yt(query):
    try:
        cmd = f'yt-dlp --dump-json --no-download --flat-playlist "ytsearch3:{query}"'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
        if result.returncode != 0 or not result.stdout.strip():
            return None
        songs = []
        for line in result.stdout.strip().split('\n'):
            if line:
                try:
                    data = json.loads(line)
                    songs.append({
                        "title": data.get("title", "Desconhecida"),
                        "url": f"https://youtube.com/watch?v={data.get('id', '')}",
                        "duration": data.get("duration", 0) or 0,
                        "channel": data.get("channel", data.get("uploader", "Desconhecido")),
                    })
                except:
                    continue
        return songs
    except:
        return None

def download_audio(url, title):
    safe = re.sub(r'[^a-zA-Z0-9\s]', '', title)[:40].strip()
    if not safe:
        safe = f"music_{int(datetime.now().timestamp())}"
    output = os.path.join(DOWNLOAD_DIR, f"{safe}.mp3")
    cmd = f'yt-dlp -x --audio-format mp3 --audio-quality 0 -o "{output}" "{url}"'
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            return None
        if os.path.exists(output):
            size = os.path.getsize(output) / (1024 * 1024)
            return {"path": output, "size": size, "name": os.path.basename(output)}
        for f in os.listdir(DOWNLOAD_DIR):
            if f.endswith('.mp3') and safe[:20] in f:
                path = os.path.join(DOWNLOAD_DIR, f)
                size = os.path.getsize(path) / (1024 * 1024)
                return {"path": path, "size": size, "name": f}
        return None
    except:
        return None

def generate_image(prompt_text):
    try:
        url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(prompt_text)}?width=800&height=800&nologo=true"
        res = requests.get(url, timeout=15)
        if res.status_code == 200:
            filename = f"img_{int(datetime.now().timestamp())}.jpg"
            filepath = os.path.join(DOWNLOAD_DIR, filename)
            with open(filepath, "wb") as f:
                f.write(res.content)
            return filepath
    except:
        pass
    return None

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = f"""
🌟 *═══ {BOT_NAME} ═══* 🌟

👋 *Olá, {user.first_name}!* 🤗
Seja bem-vindo! Escolha uma opção abaixo:

🎵 *BAIXAR MÚSICA* → Pesquise e baixe MP3
🆘 *AJUDA* → Veja tutoriais e exemplos
🎨 *GERAR IMAGEM* → Crie imagens com IA
👑 *CRIADOR* → Sobre o dono do bot
⚙️ *PAINEL ADMIN* → Controle do bot (dono)

💡 *Dica rápida:* Use /lp + nome da música!
"""
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=menu_principal())

async def cmd_lp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global total_downloads
    if not is_bot_active:
        await update.message.reply_text("⛔ *BOT PARADO!* Use /go para ligar!", parse_mode="Markdown")
        return
    query = " ".join(context.args)
    if not query:
        text = f"""
🎵 *═══ COMO USAR /LP ═══*

📝 *SINTAXE:*
`/lp nome da música`

📌 *EXEMPLOS:*
• `/lp imagine dragons believer`
• `/lp henrique e juliano`
• `/lp metallica nothing`
• `/lp lofi hip hop relax`

💡 *Dica:* Seja específico!
"""
        await update.message.reply_text(text, parse_mode="Markdown")
        return
    if not check_deps():
        await update.message.reply_text("❌ *Falta yt-dlp ou ffmpeg!* Instale no Railway: `apt-get install ffmpeg`", parse_mode="Markdown")
        return
    msg = await update.message.reply_text(f"🔍 *PESQUISANDO:* `{query}`\n⏳ Aguarde...", parse_mode="Markdown")
    results = search_yt(query)
    if not results:
        await msg.edit_text(f"❌ *Nada encontrado para:* `{query}`\n💡 Tente ser mais específico!", parse_mode="Markdown")
        return
    best = results[0]
    title = best["title"]
    url = best["url"]
    channel = best["channel"]
    duration = best["duration"]
    dur_str = f"{duration//60}:{duration%60:02d}" if duration else "Desconhecida"
    await msg.edit_text(f"🎵 *{title[:50]}*\n👤 {channel}\n⏱ {dur_str}\n\n⬇️ *Baixando...*", parse_mode="Markdown")
    audio = download_audio(url, title)
    if not audio:
        await msg.edit_text("❌ *Erro no download!* Tente outro nome.", parse_mode="Markdown")
        return
    await msg.edit_text(f"📤 *Enviando...* 🎵 {title[:30]}", parse_mode="Markdown")
    try:
        with open(audio["path"], "rb") as f:
            caption = f"🎵 *{title[:50]}*\n👤 {channel}\n⏱ {dur_str} | 📦 {audio['size']:.1f}MB\n⚡ Via {BOT_NAME}"
            await update.message.reply_audio(
                audio=f,
                title=title[:50],
                performer=channel[:30],
                duration=duration if duration else None,
                caption=caption,
                parse_mode="Markdown"
            )
        total_downloads += 1
        await msg.delete()
        try:
            os.remove(audio["path"])
        except:
            pass
    except Exception as e:
        await msg.edit_text(f"❌ *Erro:* {str(e)[:50]}", parse_mode="Markdown")

async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id != MY_TARGET_ID and user_id != str(MY_TARGET_ID):
        await update.message.reply_text("⛔ *Acesso negado!* Só o dono!", parse_mode="Markdown")
        return
    uptime = datetime.now() - bot_start_time
    hours, remainder = divmod(int(uptime.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    text = f"""
👑 *═══ PAINEL ADMIN ═══*

📋 *INFORMAÇÕES:*
🤖 {BOT_NAME} | ⚡ v{VERSION}
🕐 {hours}h {minutes}m {seconds}s

📊 *ESTATÍSTICAS:*
🔘 {'🟢 ATIVO' if is_bot_active else '🔴 PARADO'}
💬 {total_messages} msgs
🎵 {total_downloads} downloads
"""
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=menu_admin())

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uptime = datetime.now() - bot_start_time
    hours, remainder = divmod(int(uptime.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    text = f"""
📊 *═══ STATUS ═══*

🔘 {'🟢 ATIVO ✅' if is_bot_active else '🔴 PARADO ⛔'}
🕐 {hours}h {minutes}m {seconds}s
💬 {total_messages} msgs
🎵 {total_downloads} downloads
🎧 {'✅' if check_deps() else '❌'} yt-dlp
⚡ v{VERSION}
👑 {OWNER_NAME}
"""
    await update.message.reply_text(text, parse_mode="Markdown")

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"""
❓ *═══ AJUDA ═══*

📌 *COMANDOS:*
• /start → Menu principal com botões
• /lp nome → Baixar música pelo nome
• /admin → Painel administrativo
• /status → Status do bot
• /go → Ligar o bot
• /stop → Parar o bot
• /help → Esta ajuda

🎵 *EXEMPLOS /LP:*
• /lp imagine dragons believer
• /lp henrique e juliano
• /lp metallica nothing
• /lp lofi hip hop

👑 {OWNER_NAME} ⚡ v{VERSION}
"""
    await update.message.reply_text(text, parse_mode="Markdown")

async def cmd_go_stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_bot_active
    user_id = str(update.effective_user.id)
    text = update.message.text.strip()
    if user_id != MY_TARGET_ID and user_id != str(MY_TARGET_ID):
        return
    if text == "/stop":
        is_bot_active = False
        await update.message.reply_text("⛔ *BOT PARADO!* Use /go para ligar.", parse_mode="Markdown")
    elif text == "/go":
        is_bot_active = True
        await update.message.reply_text("✅ *BOT LIGADO!* Use /lp para baixar músicas! 🎵", parse_mode="Markdown")


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_bot_active, bot_start_time, total_messages, total_downloads
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    is_owner = (user_id == MY_TARGET_ID or user_id == str(MY_TARGET_ID))
    data = query.data
    uptime = datetime.now() - bot_start_time
    hours, remainder = divmod(int(uptime.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)

    if data == "voltar_inicio":
        text = f"🌟 *{BOT_NAME}*\n\n👋 Escolha uma opção abaixo:"
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=menu_principal())
    elif data == "baixar":
        text = f"🎵 *═══ BAIXAR MÚSICA ═══*\n\n📝 *Use o comando:*\n`/lp nome da música`\n\n📌 *EXEMPLOS:*\n• `/lp imagine dragons believer`\n• `/lp henrique e juliano`\n• `/lp metallica nothing`"
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=menu_baixar())
    elif data == "ajuda":
        text = f"🆘 *═══ AJUDA ═══*\n\n📌 *COMANDOS:*\n• 🎵 /lp nome → Baixar música\n• 🏠 /start → Menu\n• ⚙️ /admin → Painel (dono)\n• 📊 /status → Status\n• 🟢 /go → Ligar\n• 🔴 /stop → Parar\n\n📝 *Ex:* `/lp imagine dragons`\n\n👑 {OWNER_NAME}"
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=menu_principal())
    elif data == "gerar_img":
        text = f"🎨 *═══ GERAR IMAGEM ═══*\n\n📝 *Como usar:*\nEnvie um prompt!\n\n📌 *EXEMPLOS:*\n• `gato cyberpunk`\n• `paisagem montanhosa`\n• `castelo medieval`"
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=menu_imagem())
    elif data == "criador":
        text = f"👑 *═══ CRIADOR ═══*\n\n🤖 *Bot:* {BOT_NAME}\n⚡ *Versão:* {VERSION}\n👤 *Criador:* {OWNER_NAME}\n\n🚀 *Powered by:*\n• Python + Telegram\n• YouTube + yt-dlp\n• IA + Pollinations"
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=menu_principal())
    elif data == "admin_panel":
        if not is_owner:
            await query.edit_message_text("⛔ *Acesso negado!* Só o dono!", parse_mode="Markdown", reply_markup=menu_principal())
            return
        text = f"👑 *═══ PAINEL ADMIN ═══*\n\n📋 *Info:*\n🤖 {BOT_NAME} | ⚡ v{VERSION}\n🕐 {hours}h {minutes}m\n\n📊 *Stats:*\n🔘 {'🟢 ATIVO' if is_bot_active else '🔴 PARADO'}\n💬 {total_messages} | 🎵 {total_downloads}"
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=menu_admin())
    elif data == "tutorial":
        text = f"📖 *═══ TUTORIAL /LP ═══*\n\n1️⃣ Digite: `/lp nome da música`\n2️⃣ Bot pesquisa 🔍\n3️⃣ Baixa MP3 ⬇️\n4️⃣ Toca no player 🎧\n\n📝 *Ex:* `/lp metallica nothing`"
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=menu_baixar())
    elif data == "exemplos":
        text = f"📝 *═══ EXEMPLOS ═══*\n\n🎵 *Internacionais:*\n• `/lp imagine dragons believer`\n• `/lp metallica nothing`\n• `/lp the weeknd blinding lights`\n\n🎵 *Nacionais:*\n• `/lp henrique e juliano`\n• `/lp gusttavo lima`\n• `/lp anitta`"
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=menu_baixar())
    elif data == "yt_list":
        files = sorted([f for f in os.listdir(DOWNLOAD_DIR) if f.endswith('.mp3')], key=lambda x: os.path.getmtime(os.path.join(DOWNLOAD_DIR, x)), reverse=True)[:10]
        if not files:
            text = "📭 *Nenhum download ainda!*\n\nBaixe músicas com /lp!"
        else:
            text = "📂 *DOWNLOADS:*\n\n"
            for i, f in enumerate(files[:5], 1):
                size = os.path.getsize(os.path.join(DOWNLOAD_DIR, f)) / (1024*1024)
                text += f"{i}. 🎵 `{f[:20]}...` ({size:.1f}MB)\n"
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=menu_baixar())
    elif data == "yt_clean":
        count = 0
        for f in os.listdir(DOWNLOAD_DIR):
            if f.endswith('.mp3'):
                try:
                    os.remove(os.path.join(DOWNLOAD_DIR, f))
                    count += 1
                except:
                    pass
        text = f"🧹 *{count} arquivos removidos!*" if count > 0 else "📭 *Nada para limpar!*"
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=menu_baixar())
    elif data == "gerar_imagem_agora":
        context.user_data["awaiting_image_prompt"] = True
        await query.edit_message_text("🎨 *Envie o prompt:*\n\nEx: `gato cyberpunk futurista`", parse_mode="Markdown", reply_markup=menu_imagem())
    elif data == "tutorial_img":
        text = f"📖 *═══ GERAR IMAGEM ═══*\n\n1️⃣ Clique em GERAR IMAGEM\n2️⃣ Envie um prompt\n3️⃣ IA gera a imagem 🎨\n\n📝 *Ex:* `astronauta no espaço`"
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=menu_imagem())
    elif data == "status":
        text = f"📊 *STATUS*\n\n🔘 {'🟢 ATIVO' if is_bot_active else '🔴 PARADO'}\n🕐 {hours}h {minutes}m\n💬 {total_messages}\n🎵 {total_downloads}\n🎧 {'✅' if check_deps() else '❌'}"
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=menu_admin())
    elif data == "stats":
        text = f"📈 *ESTATÍSTICAS*\n\n💬 {total_messages} msgs\n🎵 {total_downloads} downloads\n🕐 {hours}h online\n⚡ v{VERSION}\n👑 {OWNER_NAME}"
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=menu_admin())
    elif data == "start_bot":
        is_bot_active = True
        await query.edit_message_text("✅ *Bot ligado!*", parse_mode="Markdown", reply_markup=menu_admin())
    elif data == "stop_bot":
        is_bot_active = False
        await query.edit_message_text("⛔ *Bot parado!*", parse_mode="Markdown", reply_markup=menu_admin())
    elif data == "restart":
        await query.edit_message_text("🔄 *Reiniciando...*", parse_mode="Markdown")
        await asyncio.sleep(1.5)
        bot_start_time = datetime.now()
        is_bot_active = True
        await query.edit_message_text("✅ *Reiniciado!*", parse_mode="Markdown", reply_markup=menu_admin())


async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global total_messages
    if not is_bot_active or not update.message or not update.message.text:
        return
    text = update.message.text.strip()
    total_messages += 1
    if context.user_data.get("awaiting_image_prompt"):
        msg = await update.message.reply_text("🎨 *Gerando imagem...* ⏳", parse_mode="Markdown")
        filepath = generate_image(text)
        if filepath and os.path.exists(filepath):
            with open(filepath, "rb") as img:
                await update.message.reply_photo(photo=img, caption=f"🎨 *Imagem gerada!*\n📝 `{text[:40]}`\n⚡ Via {BOT_NAME}", parse_mode="Markdown")
            await msg.delete()
            os.remove(filepath)
        else:
            await msg.edit_text("❌ *Erro ao gerar imagem!* Tente outro prompt.", parse_mode="Markdown")
        context.user_data["awaiting_image_prompt"] = False
        return
    if update.effective_chat.type in ["group", "supergroup"]:
        bot_username = context.bot.username.lower()
        if not (f"@{bot_username}" in text.lower() or "ai" in text.lower() or "bot" in text.lower() or "leo" in text.lower() or "mdz" in text.lower()):
            return
    reply = get_ai_response(text)
    if reply:
        await update.message.reply_text(reply, parse_mode="Markdown")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("lp", cmd_lp))
    app.add_handler(CommandHandler("admin", cmd_admin))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler(["stop", "go"], cmd_go_stop))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))
    
    print(f"""
╔══════════════════════════════════════════╗
║       🌟 {BOT_NAME} v{VERSION} 🌟      ║
╠══════════════════════════════════════════╣
║  🟢 Online - Railway ✓                  ║
║  🎵 /lp nome → Baixar música            ║
║  🎨 Gerar imagem por prompt             ║
║  ⚙️  /admin → Painel                    ║
║  👑 Dono: {OWNER_NAME}         ║
╚══════════════════════════════════════════╝
    """)
    
    if check_deps():
        print("✅ yt-dlp + ffmpeg OK!")
    else:
        print("⚠️ ffmpeg pode não estar instalado. O download pode falhar.")
    
    app.run_polling()

if __name__ == "__main__":
    main()