import imaplib
import email
import re
import time
import requests
import os

# --- Configuración de entorno ---
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# --- Conexión IMAP a Gmail ---
def obtener_emails():
    imap = imaplib.IMAP4_SSL("imap.gmail.com")
    imap.login(EMAIL_USER, EMAIL_PASS)
    imap.select("inbox")

    status, messages = imap.search(None, '(FROM "enviodigital@bancochile.cl" SUBJECT "Cargo en Cuenta")')

    correos = []
    for num in messages[0].split()[-5:]:  # últimos 5 correos
        status, data = imap.fetch(num, "(RFC822)")
        msg = email.message_from_bytes(data[0][1])
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/html":
                    body = part.get_payload(decode=True).decode()
                    correos.append((num, body))
    imap.logout()
    return correos

# --- Extraer información del cargo ---
def extraer_datos(html):
    match = re.search(r"una compra por \$([\d\.]+).*?en (.*?) el (\d{2}/\d{2}/\d{4} \d{2}:\d{2})", html)
    if match:
        monto = match.group(1)
        comercio = match.group(2)
        fecha = match.group(3)
        return monto, comercio, fecha
    return None, None, None

# --- Notificar por Telegram ---
def enviar_telegram(monto, comercio, fecha):
    mensaje = f"💳 Se detectó un nuevo cargo:\n\n💰 Monto: ${monto}\n🏬 Comercio: {comercio}\n📅 Fecha: {fecha}\n\n¿Fue tuyo? Responde directamente al bot."
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensaje
    }
    requests.post(url, data=data)

# --- Ejecutar ---
enviados = set()
while True:
    emails = obtener_emails()
    for id_correo, html in emails:
        if id_correo in enviados:
            continue
        monto, comercio, fecha = extraer_datos(html)
        if monto:
            enviar_telegram(monto, comercio, fecha)
            enviados.add(id_correo)
    time.sleep(300)  # Revisa cada 5 minutos
