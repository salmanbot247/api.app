import os
import telebot
import subprocess
import shutil
import urllib.request
from urllib.parse import urlparse

# 🔑 Aapki Details
TOKEN = "8096650971:AAGswGC1bgBuGi3XX7_oOZ6GhDiiqXE6jhM"
CHAT_ID = "7144917062"
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "☠️ **APP DISSECTOR BOT ACTIVATED** ☠️\n\nMujhe kisi bhi Android App (.apk) ka DIRECT LINK bhejein, main usay decompile karke Source Code aapko de dunga!")

# 🔥 NAYA HANDLER: Jo sirf links ko pakrega
@bot.message_handler(func=lambda message: message.text and message.text.startswith('http'))
def handle_apk_link(message):
    if str(message.chat.id) != str(CHAT_ID):
        return bot.reply_to(message, "🚫 Access Denied!")

    url = message.text.strip()
    bot.reply_to(message, f"🔗 Link received! Downloading APK from URL...\n{url}")

    file_name = "target_app.apk"
    out_dir = "decompiled_source"
    zip_name = "target_app_source"

    try:
        # URL se file ka asli naam nikalne ki koshish karega
        parsed_url = urlparse(url)
        extracted_name = os.path.basename(parsed_url.path)
        if extracted_name.endswith('.apk'):
            file_name = extracted_name
            zip_name = f"{file_name}_source"

        # 1. Internet se direct APK download karna (10Gbps speed se)
        urllib.request.urlretrieve(url, file_name)
        bot.send_message(CHAT_ID, f"✅ Download complete: {file_name}\n\n🛠️ Dissecting App (Extracting Java & XML)... Please wait.")

        # 2. Setup output folder
        if os.path.exists(out_dir):
            shutil.rmtree(out_dir)

        # 3. RUN JADX (The Reverse Engineering Magic)
        process = subprocess.run(
            ['jadx', '-d', out_dir, file_name], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )

        if process.returncode != 0:
            bot.send_message(CHAT_ID, f"❌ Decompilation Failed:\n{process.stderr[:500]}")
            return

        # 4. ZIP the Source Code
        bot.send_message(CHAT_ID, "📦 Zipping the extracted source code...")
        shutil.make_archive(zip_name, 'zip', out_dir)
        final_zip = f"{zip_name}.zip"

        # 5. Send back to Hacker
        bot.send_message(CHAT_ID, "✅ Dissection Complete! Sending Source Code...")
        with open(final_zip, 'rb') as doc:
            bot.send_document(CHAT_ID, doc)

    except Exception as e:
        bot.send_message(CHAT_ID, f"❌ Error: {str(e)[:300]}")
        
    finally:
        # Cleanup tracks (Saboot mitana)
        final_zip = f"{zip_name}.zip"
        for item in [file_name, out_dir, final_zip]:
            if os.path.exists(item):
                if os.path.isdir(item):
                    shutil.rmtree(item)
                else:
                    os.remove(item)

bot.polling(non_stop=True)
