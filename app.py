from firebase_admin import initialize_app, db, credentials
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    Updater,
)
from typing import Final
from telegram import Update
from dotenv import load_dotenv
from googlemaps import Client
import pandas as pd
from os import getenv
import pyshorteners
import json


load_dotenv()

# Inisialisasi Firebase Admin SDK
cred = credentials.Certificate("serviceAccountKey.json")
initialize_app(cred, {"databaseURL": getenv("URL_FIREBASE")})

# Inisialisasi Bot Telegram
TELEGRAM_BOT_TOKEN: Final = getenv("TELEGRAM_BOT_TOKEN")
BOT_USERNAME: Final = "@busrestMalioboro_bot"

# Inisialisasi Google Maps API
gmaps = Client(key=getenv("GOOGLE_MAPS_API_KEY"))
gmaps_base_url = "https://www.google.com/maps/dir/?api=1&"


# Fungsi URL shorteners
def url_short(url: str):
    s = pyshorteners.Shortener()
    return s.tinyurl.short(url)


# Fungsi Firebase
def fb_query(parkiran_bus: str = "/", db=db) -> dict:
    try:
        result: dict = db.reference(parkiran_bus).get()
    except:
        raise Exception("Data tidak ada")
    return result


# Fungsi Google Maps
def maps_eta(source: str, destination: str):
    try:
        result: dict = gmaps.distance_matrix(
            source, destination, mode="driving", language="id"
        )
    except Exception as err:
        return False
    else:
        duration_text = result["rows"][0]["elements"][0]["duration"]["text"]
        duration_sec = result["rows"][0]["elements"][0]["duration"]["value"]
        return destination, duration_text, duration_sec


# Fungsi Sort
def location_sort(source: str):
    all_parkiran = fb_query()
    
    destination_list = []
    destination_coor_list = []
    duration_text_list = []
    duration_sec_list = []
    slot_kosong_list = []
    
    for parkiran in all_parkiran:
        res = fb_query(f"/{parkiran}")
        destination = res["nama"]
        destination_coor = ",".join([str(coor) for coor in res["location"].values()])
        try:
            _, duration_text, duration_sec = maps_eta(source, destination_coor)
        except Exception as err:
            raise Exception("maps_eta error: ", err)
        else:
            destination_list.append(destination)
            destination_coor_list.append(destination_coor)
            duration_text_list.append(duration_text)
            duration_sec_list.append(duration_sec)
            slot_kosong_list.append(res["slot_kosong"])

    output = pd.DataFrame(destination_list, columns=["destination"])
    output["destination_coor"] = destination_coor_list
    output["duration"] = duration_text_list
    output["duration_in_sec"] = duration_sec_list
    output["slot_kosong"] = slot_kosong_list

# Pisahkan destinasi dengan slot_kosong=0 dan slot_kosong>0
    with_slot_kosong = output[output['slot_kosong'] > 0]
    without_slot_kosong = output[output['slot_kosong'] == 0]

    # Urutkan destinasi dengan slot_kosong>0 berdasarkan durasi perjalanan
    with_slot_kosong.sort_values(by=["duration_in_sec"], inplace=True)
    without_slot_kosong.sort_values(by=["duration_in_sec"], inplace=True)
    # Gabungkan kembali destinasi dengan slot_kosong>0 dan slot_kosong=0
    sorted_output = pd.concat([with_slot_kosong, without_slot_kosong])

    # Periksa apakah semua slot kosong adalah 0
    if all(sorted_output["slot_kosong"] == 0):
        return "Mohon maaf, semua tempat parkir yang tersedia penuh. /SELESAI"
    
    return sorted_output


# Fungsi untuk mengirim pesan ke Telegram
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Selamat datang di bot Sistem Informasi Parkir Bus Malioboro! \n\nSilahkan pilih menu: \n/cekparkir_list \n/cekparkir_terdekat \n/HELP"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        """Ini adalah menu bantuan bot:\n/START untuk memulai.\n/cekparkir_list untuk informasi daftar parkiran.
        \n/cekparkir_terdekat untuk rekomendasi parkir terdekat dari lokasi Anda."""
    )


async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        """Berikut merupakan parkir khusus Bus resmi, silahkan pilih yang ingin di cek :
        \n/abu_bakar_ali \n/ngabean \n/senopati \n/semua_parkiran \n\n Kembali ke /START"""
    )


async def selesai_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Terimakasih telah berkunjung! Untuk memulai kembali klik /START"
    )


async def check_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    all_parkiran = fb_query()
    res = ""
    for parkiran in all_parkiran:
        hasil_firebase = fb_query(f"/{parkiran}")
        res += f'Nama: {hasil_firebase["nama"]} \nSlot Isi: {hasil_firebase["slot_isi"]}\nSlot Kosong: {hasil_firebase["slot_kosong"]}\n\n'
    await update.message.reply_text(res + 'Kembali ke /START')


async def abu_bakar_ali_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    hasil_firebase = fb_query("/Parkiran Abu Bakar Ali")
    await update.message.reply_text(
        "Nama: "
        + str(hasil_firebase["nama"])
        + "\nSlot Isi: "
        + str(hasil_firebase["slot_isi"])
        + "\nSlot Kosong: "
        + str(hasil_firebase["slot_kosong"]) + "\n\nIngin cek parkiran lain? /cekparkir_list \n/SELESAI"
    )


async def ngabean_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    hasil_firebase = fb_query("/Parkiran Ngabean")
    await update.message.reply_text(
        "Nama: "
        + str(hasil_firebase["nama"])
        + "\nSlot Isi: "
        + str(hasil_firebase["slot_isi"])
        + "\nSlot Kosong: "
        + str(hasil_firebase["slot_kosong"]) + "\n\nIngin cek parkiran lain? /cekparkir_list \n/SELESAI"
    )


async def senopati_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    hasil_firebase = fb_query("/Parkiran Senopati")
    await update.message.reply_text(
        "Nama: "
        + str(hasil_firebase["nama"])
        + "\nSlot Isi: "
        + str(hasil_firebase["slot_isi"])
        + "\nSlot Kosong: "
        + str(hasil_firebase["slot_kosong"]) + "\n\nIngin cek parkiran lain? /cekparkir_list \n/SELESAI"
    )


async def direction_command(update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.location:
        await update.message.reply_text("Please wait...")

        context.user_data["current_location"] = update.message.location
        current_location = context.user_data.get("current_location")
        source = (current_location.latitude, current_location.longitude)

        result = location_sort(source)
        if isinstance(result, str):
            # Menanggapi dengan pesan jika semua tempat parkir penuh
            await update.message.reply_text(result + " /SELESAI")
        else:
            response_text = [f"Berdasarkan lokasi anda, \n"]
            i = 1
        for item in result.iloc:
            location = item.to_dict()
            gmaps_nav_url = url_short(
                f'{gmaps_base_url}destination={location["destination_coor"]}&travelmode=car&dir_action=navigate'
            )
            response_text.append(f'Opsi ke-{i}: {location["destination"]}\n')
            response_text.append(f'Perkiraan waktu tiba : {location["duration"]}\n')
            response_text.append(f'Slot tersedia saat ini: {location["slot_kosong"]}\n')
            response_text.append(f"Link Google Maps : {gmaps_nav_url}\n\n")
            i += 1
        response_text.append("/SELESAI")

        await update.message.reply_text("".join(response_text))
    else:
        await update.message.reply_text("Please send me your location...")


def handle_response(text: str) -> str:
    processed: str = text.lower()

    if "hai" in processed or "hallo" in processed:
        return 'Hai! Saya asisen Parkir Bus Anda. Silahkan klik "/START" untuk memulai.'

    return 'Mohon maaf saya tidak mengerti. Silahkan klik "/START" untuk memulai.'


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type: str = update.message.chat.type
    text: str = update.message.text

    print(f'User ({update.message.chat.id}) in {message_type}: "{text}" ')

    if message_type == "group":
        if BOT_USERNAME in text:
            new_text: str = text.replace(BOT_USERNAME, "").strip()
            response: str = handle_response(new_text)
        else:
            return
    else:
        response: str = handle_response(text)

    print("Bot:", response)
    await update.message.reply_text(response)


if __name__ == "__main__":
    print("Starting bot...")
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("START", start_command))
    app.add_handler(CommandHandler("cekparkir_list", list_command))
    app.add_handler(CommandHandler("HELP", help_command))
    app.add_handler(CommandHandler("SELESAI", selesai_command))
    app.add_handler(CommandHandler("cekparkir_terdekat", direction_command))
    app.add_handler(MessageHandler(filters.LOCATION, direction_command))
    app.add_handler(CommandHandler("abu_bakar_ali", abu_bakar_ali_command))
    app.add_handler(CommandHandler("ngabean", ngabean_command))
    app.add_handler(CommandHandler("senopati", senopati_command))
    app.add_handler(CommandHandler("semua_parkiran", check_command))
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    print("Polling...")
    app.run_polling(poll_interval=3)