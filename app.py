from firebase_admin import initialize_app, db, credentials
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, Updater
from typing import Final
from telegram import Update
from dotenv import load_dotenv
from googlemaps import Client
import pandas as pd
from os import getenv
import pyshorteners


load_dotenv()

# Inisialisasi Firebase Admin SDK
cred = credentials.Certificate('serviceAccountKey.json')
initialize_app(cred, {
    'databaseURL': getenv('URL_FIREBASE')
})

#Inisialisasi Bot Telegram
TELEGRAM_BOT_TOKEN: Final = getenv('TELEGRAM_BOT_TOKEN')
BOT_USERNAME: Final = '@busrestMalioboro_bot'

# Inisialisasi Google Maps API
gmaps = Client(key=getenv('GOOGLE_MAPS_API_KEY'))
gmaps_base_url = 'https://www.google.com/maps/dir/?api=1&'

# Fungsi URL shorteners
def url_short(url):
    s = pyshorteners.Shortener()
    return s.tinyurl.short(url)

#Fungsi Firebase
def fb_query(parkiran_bus='/', db=db):
    return db.reference(parkiran_bus).get()

#Fungsi Google Maps
def maps_eta(source, destination):
    result = gmaps.distance_matrix(source, destination, mode = 'driving', language = 'id')
    duration_text = result['rows'][0]['elements'][0]['duration']['text']
    duration_sec = result['rows'][0]['elements'][0]['duration']['value']
    return destination, duration_text, duration_sec

#Fungsi Sort
def location_sort(source):
    all_parkiran = fb_query()
    destination_list = []
    duration_text_list = []
    duration_sec_list = []
    slot_kosong_list = []
    for parkiran in all_parkiran:
        res = fb_query(f'/{parkiran}')
        destination = res['nama']
        destination, duration_text, duration_sec = maps_eta(source, destination)
        destination_list.append(res['nama'])
        duration_text_list.append(duration_text)
        duration_sec_list.append(duration_sec)
        slot_kosong_list.append(res['slot_kosong'])
    
    output = pd.DataFrame(destination_list, columns = ['destination'])
    output['duration'] = duration_text_list
    output['duration_in_sec'] = duration_sec_list
    output['slot_kosong'] = slot_kosong_list
    output.sort_values(by=['duration_in_sec'], inplace=True)
    return output



# Fungsi untuk mengirim pesan ke Telegram
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
     await update.message.reply_text('Selamat datang di bot Sistem Informasi Parkir Bus Malioboro! \n Silahkan pilih menu: \n/cekparkir_list \n/cekparkir_terdekat')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Ini adalah menu bantuan bot:\nKlik /start untuk memulai.\nKlik /cekparkir_list untuk informasi parkiran.\nKlik /cekparkir_terdekat untuk rekomendasi parkir terdekat dari Anda.')

async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Berikut merupakan parkir khusus Bus resmi, silahkan pilih yang ingin di cek : \n/abu_bakar_ali \n/ngabean \n/senopati \n/semua_parkiran')

async def check_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    all_parkiran = fb_query()
    res = ''
    for parkiran in all_parkiran:
        hasil_firebase = fb_query(f'/{parkiran}')
        res += f'Nama: {hasil_firebase["nama"]} \nSlot Isi: {hasil_firebase["slot_isi"]}\nSlot Kosong: {hasil_firebase["slot_kosong"]}\n\n'
    await update.message.reply_text(res)

async def abu_bakar_ali_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    hasil_firebase = fb_query('/Parkiran Abu Bakar Ali')
    await update.message.reply_text('Nama: ' + str(hasil_firebase['nama']) + '\nSlot Isi: ' + str(hasil_firebase['slot_isi']) + '\nSlot Kosong: ' + str(hasil_firebase['slot_kosong']))

async def ngabean_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    hasil_firebase = fb_query('/Parkiran Ngabean')
    await update.message.reply_text('Nama: ' + str(hasil_firebase['nama']) + '\nSlot Isi: ' + str(hasil_firebase['slot_isi']) + '\nSlot Kosong: ' + str(hasil_firebase['slot_kosong']))

async def senopati_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    hasil_firebase = fb_query('/Parkiran Senopati')
    await update.message.reply_text('Nama: ' + str(hasil_firebase['nama']) + '\nSlot Isi: ' + str(hasil_firebase['slot_isi']) + '\nSlot Kosong: ' + str(hasil_firebase['slot_kosong']))

async def direction_command(update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.location:
        await update.message.reply_text('Please wait...')
        
        context.user_data['current_location'] = update.message.location
        current_location = context.user_data.get('current_location')
        source = (current_location.latitude, current_location.longitude)
        
        result = location_sort(source)
        best_loc = result.iloc[0].to_dict()
        alt_1 = result.iloc[1].to_dict()
        alt_2 = result.iloc[2].to_dict()
        if best_loc:
            best_loc_url = url_short(f'{gmaps_base_url}destination={best_loc["destination"].replace(" ", "+")}&travelmode=car&dir_action=navigate')
            alt_1_url = url_short(f'{gmaps_base_url}destination={alt_1["destination"].replace(" ", "+")}&travelmode=car&dir_action=navigate')
            alt_2_url = url_short(f'{gmaps_base_url}destination={alt_2["destination"].replace(" ", "+")}&travelmode=car&dir_action=navigate')
            await update.message.reply_text(
                f'Berdasarkan lokasi anda, \n'
                f'Opsi terdekat : {best_loc["destination"]}\n'
                f'Perkiraan waktu tiba : {best_loc["duration"]}\n'
                f'Slot tersedia saat ini: {best_loc["slot_kosong"]}\n'
                f'Link Google Maps : {best_loc_url}\n\n'
                f'Alternatif ke-1 : {alt_1["destination"]}\n'
                f'Perkiraan waktu tiba : {alt_1["duration"]}\n'
                f'Slot tersedia saat ini: {alt_1["slot_kosong"]}\n'
                f'Link Google Maps : {alt_1_url}\n\n'
                f'Alternatif ke-2 : {alt_2["destination"]}\n'
                f'Perkiraan waktu tiba : {alt_2["duration"]}\n'
                f'Slot tersedia saat ini: {alt_2["slot_kosong"]}\n'
                f'Link Google Maps : {alt_2_url}\n\n'
                )
    else:
        await update.message.reply_text('Please send me your location...')

if __name__ == '__main__':
    print('Starting bot...')
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('cekparkir_list',list_command))
    app.add_handler(CommandHandler('help',help_command))
    app.add_handler(CommandHandler('cekparkir_terdekat',direction_command))
    app.add_handler(MessageHandler(filters.LOCATION, direction_command))
    app.add_handler(CommandHandler('abu_bakar_ali', abu_bakar_ali_command))
    app.add_handler(CommandHandler('ngabean', ngabean_command))
    app.add_handler(CommandHandler('senopati', senopati_command))
    app.add_handler(CommandHandler('semua_parkiran', check_command))

    print('Polling...')
    app.run_polling(poll_interval=3)