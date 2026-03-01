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
    bot.reply_to(message, "☠️ **UI BLUEPRINT EXTRACTOR ACTIVATED** ☠️\n\nMujhe App ka link bhejein. Main uske saare Screens se Buttons, Inputs aur unke IDs (Locators) nikal kar aapko de dunga!")

# 🔍 The Extractor Engine (Jo UI Elements dhoondega)
def extract_ui_elements(directory):
    ui_data = []
    
    # JADX XML layouts ko 'res/layout' ya 'resources/res/layout' mein rakhta hai
    res_layout_path = os.path.join(directory, 'resources', 'res', 'layout')
    if not os.path.exists(res_layout_path):
        res_layout_path = os.path.join(directory, 'res', 'layout')
        
    if not os.path.exists(res_layout_path):
        return ["⚠️ Layout folder nahi mila. Shayad app obfuscated hai."]

    # Regex jo kisi bhi element (Button, TextView) aur uske ID ko pakrega
    # Misaal: <Button android:id="@+id/submit_btn" ... />
    pattern = re.compile(r'<([A-Za-z0-9_.]+)[^>]*?android:id="@\+id/([^"]+)"')

    # Har screen ki layout file ko parho
    for root, dirs, files in os.walk(res_layout_path):
        for file in files:
            if file.endswith('.xml'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        matches = pattern.findall(content)
                        
                        # Agar is screen par koi IDs hain, toh unko list mein daalo
                        if matches:
                            ui_data.append(f"\n📱 [Screen: {file}]")
                            for tag_name, element_id in matches:
                                # Appium Automation ke liye Type aur ID
                                ui_data.append(f"  └─ Element: {tag_name}")
                                ui_data.append(f"     ➔ ID: {element_id}")
                                # Automation walay isko aise XPath banate hain:
                                ui_data.append(f"     ➔ XPath: //{tag_name}[@resource-id='{element_id}']\n")
                except Exception:
                    pass
                    
    return ui_data

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
        
        bot.send_message(CHAT_ID, "🛠️ Decompiling App... Please wait.")
        if os.path.exists(out_dir):
            shutil.rmtree(out_dir)

        # Decompile App with Resources (XML)
        process = subprocess.run(
            ['jadx', '-d', out_dir, file_name], 
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        bot.send_message(CHAT_ID, "👁️ Extracting UI Layouts, XPaths, and Resource IDs...")
        found_data = extract_ui_elements(out_dir)

        # Result Bhejna
        if len(found_data) <= 1:
            bot.send_message(CHAT_ID, "⚠️ Koi UI Elements nahi milay.")
        else:
            result_text = "🔥 **APP UI BLUEPRINT EXTRACTED!** 🔥\n" + "\n".join(found_data)
            
            # Text file bana kar bhejo kyunke UI list bohat lambi hogi
            file_path = "app_ui_locators.txt"
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(result_text)
                
            with open(file_path, "rb") as doc:
                bot.send_document(CHAT_ID, doc, caption="✅ Yeh lein! Saari screens ke UI Elements, IDs, aur XPaths is file mein hain.")

    except Exception as e:
        bot.send_message(CHAT_ID, f"❌ Error: {str(e)[:300]}")
        
    finally:
        # Piche koi saboot na chhoro
        for item in [file_name, out_dir, "app_ui_locators.txt"]:
            if os.path.exists(item):
                if os.path.isdir(item): shutil.rmtree(item)
                else: os.remove(item)

bot.polling(non_stop=True)
