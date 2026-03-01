import os
import time
import telebot
import subprocess
import shutil
import urllib.request
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright

# 🔑 Aapki Details
TOKEN = "8096650971:AAGswGC1bgBuGi3XX7_oOZ6GhDiiqXE6jhM"
CHAT_ID = "7144917062"
bot = telebot.TeleBot(TOKEN)

# 🧠 State Manager for JazzDrive Login
user_context = {"state": "IDLE", "number": None, "otp": None}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "☠️ **APP DISSECTOR (JAZZDRIVE EDITION)** ☠️\n\nMujhe APK/XAPK ka link bhejein, main decompile karke seedha aapki JazzDrive mein bhej dunga!")

# 📩 OTP aur Number Catch karne ka logic
@bot.message_handler(func=lambda m: str(m.chat.id) == str(CHAT_ID) and not m.text.startswith('/') and not m.text.startswith('http'))
def handle_credentials(message):
    text = message.text.strip()
    if user_context["state"] == "WAITING_FOR_NUMBER":
        user_context["number"] = text
        user_context["state"] = "NUMBER_RECEIVED"
    elif user_context["state"] == "WAITING_FOR_OTP":
        user_context["otp"] = text
        user_context["state"] = "OTP_RECEIVED"

# 🔗 Main Hacking & Uploading Logic
@bot.message_handler(func=lambda message: message.text and message.text.startswith('http'))
def handle_apk_link(message):
    if str(message.chat.id) != str(CHAT_ID):
        return bot.reply_to(message, "🚫 Access Denied!")

    url = message.text.strip()
    file_name = "target_app.apk"
    out_dir = "decompiled_source"
    zip_name = "target_app_source"

    try:
        parsed_url = urlparse(url)
        extracted_name = os.path.basename(parsed_url.path)
        if extracted_name.endswith('.apk') or extracted_name.endswith('.xapk'):
            file_name = extracted_name
            zip_name = f"{file_name}_source"

        bot.reply_to(message, f"⬇️ Downloading: {file_name}...")
        urllib.request.urlretrieve(url, file_name)
        
        # --- 1. DECOMPILE PROCESS ---
        bot.send_message(CHAT_ID, "🛠️ Dissecting App (Extracting Java & XML)...")
        if os.path.exists(out_dir):
            shutil.rmtree(out_dir)

        process = subprocess.run(
            ['jadx', '-d', out_dir, file_name], 
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        if process.returncode != 0:
            bot.send_message(CHAT_ID, f"❌ Decompilation Failed:\n{process.stderr[:500]}")
            return

        bot.send_message(CHAT_ID, "📦 Zipping the extracted source code...")
        shutil.make_archive(zip_name, 'zip', out_dir)
        final_zip = f"{zip_name}.zip"

        file_size_mb = os.path.getsize(final_zip) / (1024 * 1024)
        bot.send_message(CHAT_ID, f"☁️ Source Code Size: {file_size_mb:.2f} MB.\n⬆️ Uploading to JazzDrive...")

        # --- 2. JAZZDRIVE UPLOAD PROCESS ---
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
            context = browser.new_context(storage_state="state.json" if os.path.exists("state.json") else None)
            page = context.new_page()
            
            page.goto("https://cloud.jazzdrive.com.pk/#folders", timeout=90000)
            time.sleep(4)
            
            # 🔥 THE FIX: "#msisdn" use kiya gaya hai direct login box ko target karne ke liye
            if page.locator("#msisdn").is_visible():
                bot.send_message(CHAT_ID, "🔑 JazzDrive Login Required! Enter Number (03xxxxxxxxx):")
                user_context["state"] = "WAITING_FOR_NUMBER"
                while user_context["state"] != "NUMBER_RECEIVED": time.sleep(1)
                
                page.locator("#msisdn").fill(user_context["number"])
                page.locator('#signinbtn').click()
                
                bot.send_message(CHAT_ID, "🔢 OTP bhejein:")
                user_context["state"] = "WAITING_FOR_OTP"
                while user_context["state"] != "OTP_RECEIVED": time.sleep(1)
                
                page.evaluate(f'document.getElementById("otp").value = "{user_context["otp"]}"')
                page.locator('#signinbtn').click()
                time.sleep(8)
                
                context.storage_state(path="state.json")
                bot.send_message(CHAT_ID, "✅ JazzDrive Login Saved!")

            # Uploading File
            page.get_by_role("button").filter(has_text="Upload").first.click()
            time.sleep(2)
            with page.expect_file_chooser() as fc_info:
                page.click("/html/body/div[2]/div[3]/div/div/form/div/div/div/div[1]")
            fc_info.value.set_files(os.path.abspath(final_zip))
            
            # Wait for upload to complete
            while not page.locator("text=Uploads completed").is_visible():
                time.sleep(2)
                
            bot.send_message(CHAT_ID, f"🎉 BOOM! Success!\n**{final_zip}** aapki JazzDrive mein upload ho chuki hai! Jakar check karein.")
            browser.close()

    except Exception as e:
        bot.send_message(CHAT_ID, f"❌ Error: {str(e)[:300]}")
        
    finally:
        # Cleanup tracks
        final_zip = f"{zip_name}.zip"
        for item in [file_name, out_dir, final_zip]:
            if os.path.exists(item):
                if os.path.isdir(item): shutil.rmtree(item)
                else: os.remove(item)

bot.polling(non_stop=True)
