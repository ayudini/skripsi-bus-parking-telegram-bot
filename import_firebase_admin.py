import firebase_admin
from firebase_admin import db, credentials
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, Updater
from typing import Final
from telegram import Update
from dotenv import load_dotenv
import googlemaps
import os


# Inisialisasi Firebase Admin SDK
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://parkir-bus-malioboro-default-rtdb.asia-southeast1.firebasedatabase.app'
})

#Fungsi Firebase
def fb_query(parkiran_bus):
    return db.reference(parkiran_bus).get()

#Inisialisasi Bot Telegram
load_dotenv()
TOKEN: Final = "6513981601:AAF6tbQLwcTVKZF7Fpe1KFAkpoSuUISAgDM"
BOT_USERNAME: Final = '@busrestMalioboro_bot'
gmaps = googlemaps.Client(key='AIzaSyC2gEDvh3iFVQDDICti5Yxsrh4MpxOAgmE')
# Untuk Araaaaa
# 'Slot Isi: ' + str(hasil_firebase['slot_isi']) + 'Slot Kosong: ' + str(hasil_firebase['slot_kosong'])

# Fungsi untuk mengirim pesan ke Telegram
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
     await update.message.reply_text('Silahkan pilih lokasi parkiran yang dituju: \n /abu_bakar_ali \n /ngabean \n /senopati')

async def abu_bakar_ali_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    hasil_firebase = fb_query('/Parkiran Abu Bakar Ali')
    await update.message.reply_text('Nama: ' + str(hasil_firebase['nama']) + '\nSlot Isi: ' + str(hasil_firebase['slot_isi']) + '\nSlot Kosong: ' + str(hasil_firebase['slot_kosong']))

async def ngabean_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    hasil_firebase = fb_query('/Parkiran Ngabean')
    await update.message.reply_text('Nama: ' + str(hasil_firebase['nama']) + '\nSlot Isi: ' + str(hasil_firebase['slot_isi']) + '\nSlot Kosong: ' + str(hasil_firebase['slot_kosong']))

async def senopati_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    hasil_firebase = fb_query('/Parkiran Senopati')
    await update.message.reply_text('Nama: ' + str(hasil_firebase['nama']) + '\nSlot Isi: ' + str(hasil_firebase['slot_isi']) + '\nSlot Kosong: ' + str(hasil_firebase['slot_kosong']))

#async def location_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    #current_pos = (update.message.location.latitude,update.message.location.longitude)
    #await update.message.reply_text(current_pos)

def location(update, context):
    current_location = update.message.location
    context.user_data['current_location'] = current_location
    context.bot.send_message(chat_id=update.effective_chat.id, text="Please send me your destination.")

def destination(update, context):
    destination = update.message.text
    current_location = context.user_data.get('current_location')
    result = gmaps.directions(current_location.latitude, current_location.longitude, destination)
    distance = result[0]['legs'][0]['distance']['text']
    duration = result[0]['legs'][0]['duration']['text']
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"The distance to {destination} is {distance}. The estimated time of arrival is {duration}.")

def main():
    updater = Updater(token=TELEGRAM_BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    location_handler = MessageHandler(Filters.location, location)
    destination_handler = MessageHandler(Filters.text, destination)
    dispatcher.add_handler(location_handler)
    dispatcher.add_handler(destination_handler)

if __name__ == '__main__':
    print('Starting bot...')
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('abu_bakar_ali', abu_bakar_ali_command))
    app.add_handler(CommandHandler('ngabean', ngabean_command))
    app.add_handler(CommandHandler('senopati', senopati_command))
    #app.add_handler(CommandHandler('location',location_command))
    #app.add_handler(CommandHandler('help', help_command))

    #app.add_handler(MessageHandler(filters.TEXT, handle_message))

    #app.add_error_handler(error)

    print('Polling...')
    app.run_polling(poll_interval=3)