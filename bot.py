import os
import telebot
import subprocess
import shutil
import urllib.request
import re
from urllib.parse import urlparse

# 🔑 Aapki Details
TOKEN = "8096650971:AAGswGC1bgBuGi3XX7_oOZ6GhDiiqXE6jhM"
CHAT_ID = "7144917062"
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "☠️ **SECRET SCANNER BOT ACTIVATED** ☠️\n\nMujhe kisi app ka link bhejein. Main code ko scan karke usme se API Keys aur Khufiya Links nikal kar aapko text karunga!")

# The Scanning Engine (Jo secrets dhoondega)
def scan_for_secrets(directory):
    secrets_found = set()
    
    # Regex Patterns (In shakal ke passwords aur keys dhoondni hain)
    patterns = {
        "Google API Key": r'AIza[0-9A-Za-z\-_]{35}',
        "AWS Access Key": r'AKIA[0-9A-Z]{16}',
        "Firebase DB": r'https://[a-z0-9-]+\.firebaseio\.com',
        "Stripe Secret": r'sk_live_[0-9a-zA-Z]{24}',
        "Possible Password": r'(?i)(password|passwd|secret)\s*=\s*[\'"]([^\'"]+)[\'"]'
    }

    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.java') or file.endswith('.xml') or file.endswith('.smali'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        
                        # Har pattern ko code mein search karo
                        for key_name, regex in patterns.items():
                            matches = re.findall(regex, content)
                            for match in matches:
                                if isinstance(match, tuple):
                                    match = match[1] # For password tuples
                                secrets_found.add(f"🔴 {key_name}: {match}")
                                
                except Exception:
                    pass
                    
    return list(secrets_found)

@bot.message_handler(func=lambda message: message.text and message.text.startswith('http'))
def handle_apk_link(message):
    if str(message.chat.id) != str(CHAT_ID):
        return bot.reply_to(message, "🚫 Access Denied!")

    url = message.text.strip()
    file_name = "target_app.apk"
    out_dir = "decompiled_source"

    try:
        bot.reply_to(message, f"⬇️ Downloading Target App...")
        urllib.request.urlretrieve(url, file_name)
        
        bot.send_message(CHAT_ID, "🛠️ Dissecting App (Extracting Code)... Please wait.")
        if os.path.exists(out_dir):
            shutil.rmtree(out_dir)

        # Decompile App
        process = subprocess.run(
            ['jadx', '-d', out_dir, file_name], 
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        if process.returncode != 0:
            bot.send_message(CHAT_ID, f"❌ Decompilation Failed!")
            return

        # Start the Scan
        bot.send_message(CHAT_ID, "👁️ Scanning millions of lines of code for Secrets...")
        found_data = scan_for_secrets(out_dir)

        # Send Results via Text
        if not found_data:
            bot.send_message(CHAT_ID, "⚠️ Koi specific API key ya secret nahi mila. (Developer smart tha!)")
        else:
            result_text = "🔥 **SECRETS FOUND!** 🔥\n\n" + "\n".join(found_data)
            
            # Agar text 4000 characters se bada hai (Telegram limit) toh file bana kar bhej do
            if len(result_text) > 4000:
                bot.send_message(CHAT_ID, "⚠️ Data bohat zyada hai! Main Text file bhej raha hoon...")
                with open("secrets_report.txt", "w") as f:
                    f.write(result_text)
                with open("secrets_report.txt", "rb") as doc:
                    bot.send_document(CHAT_ID, doc)
            else:
                # Agar chota hai toh direct text message bhej do!
                bot.send_message(CHAT_ID, result_text)

    except Exception as e:
        bot.send_message(CHAT_ID, f"❌ Error: {str(e)[:300]}")
        
    finally:
        # Piche koi saboot na chhoro
        for item in [file_name, out_dir, "secrets_report.txt"]:
            if os.path.exists(item):
                if os.path.isdir(item): shutil.rmtree(item)
                else: os.remove(item)

bot.polling(non_stop=True)
