"""
Модуль отправки PDF смет через различные каналы:
- Email (SMTP)
- Telegram (Bot API)
- WhatsApp (wa.me ссылка по номеру телефона)
- MAX (российский мессенджер, по номеру телефона)
"""

import os
import smtplib
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import Optional


# ===================== НАСТРОЙКИ (из .env или по умолчанию) =====================

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.yandex.ru")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USER)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# Пути
OUTPUT_DIR = Path(__file__).parent.parent / "output"


# ===================== EMAIL =====================

def send_via_email(recipient: str, pdf_path: str, client_name: str, total: float) -> dict:
    """
    Отправка PDF по email через SMTP (STARTTLS на порту 587).
    """
    if not SMTP_USER or not SMTP_PASSWORD:
        return {
            "status": "error",
            "method": "email",
            "message": "SMTP не настроен. Укажите SMTP_USER и SMTP_PASSWORD в .env"
        }

    if not os.path.exists(pdf_path):
        return {
            "status": "error",
            "method": "email",
            "message": f"PDF файл не найден: {pdf_path}"
        }

    try:
        msg = MIMEMultipart()
        msg["From"] = SMTP_FROM
        msg["To"] = recipient
        msg["Subject"] = f"Смета для {client_name} — {total} ₽"

        body = f"Здравствуйте, {client_name}!\n\nВо вложении — ваша смета на сумму {total} ₽.\n\nС уважением,\nГенератор смет"
        msg.attach(MIMEText(body, "plain", "utf-8"))

        with open(pdf_path, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename=smeta_{client_name}.pdf")
            msg.attach(part)

        # Попробуем STARTTLS на порту 587
        with smtplib.SMTP(SMTP_HOST, 587, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_FROM, recipient, msg.as_string())

        return {
            "status": "ok",
            "method": "email",
            "recipient": recipient,
            "message": f"PDF успешно отправлен на {recipient}"
        }

    except smtplib.SMTPAuthenticationError as e:
        return {
            "status": "error",
            "method": "email",
            "message": "Ошибка авторизации SMTP. Проверьте логин и пароль приложения",
            "error": str(e)
        }
    except smtplib.SMTPConnectError as e:
        return {
            "status": "error",
            "method": "email",
            "message": f"Не удалось подключиться к SMTP серверу {SMTP_HOST}:587",
            "error": str(e)
        }
    except Exception as e:
        return {
            "status": "error",
            "method": "email",
            "message": f"Ошибка отправки email: {str(e)}",
            "error": str(e)
        }


# ===================== TELEGRAM =====================

async def send_via_telegram(recipient: str, pdf_path: str, client_name: str, total: float) -> dict:
    """
    Отправка PDF через Telegram Bot API.
    recipient — username (@user) или chat_id
    Требует TELEGRAM_BOT_TOKEN в .env
    """
    import aiohttp

    if not TELEGRAM_BOT_TOKEN:
        return {
            "status": "error",
            "method": "telegram",
            "message": "Telegram бот не настроен. Укажите TELEGRAM_BOT_TOKEN в .env",
            "hint": "Создай бота через @BotFather в Telegram и скопируй токен"
        }

    # Нормализуем username
    chat_id = recipient
    if recipient.startswith("@"):
        chat_id = recipient[1:]

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"

    try:
        data = {
            "chat_id": chat_id,
            "caption": f"📄 Смета для {client_name}\n💰 Сумма: {total} ₽"
        }

        async with aiohttp.ClientSession() as session:
            with open(pdf_path, "rb") as pdf_file:
                files = {"document": (f"smeta_{client_name}.pdf", pdf_file, "application/pdf")}
                async with session.post(url, data=data, files=files) as response:
                    result = await response.json()

        if result.get("ok"):
            return {
                "status": "ok",
                "method": "telegram",
                "recipient": recipient,
                "message": f"PDF отправлен в Telegram @{chat_id}"
            }
        else:
            return {
                "status": "error",
                "method": "telegram",
                "message": f"Telegram API ошибка: {result.get('description', 'неизвестно')}",
                "hint": "Убедитесь что пользователь запустил бота (нажал /start)"
            }

    except Exception as e:
        return {
            "status": "error",
            "method": "telegram",
            "message": f"Ошибка отправки в Telegram: {str(e)}"
        }


# ===================== WHATSAPP =====================

def send_via_whatsapp(phone: str, pdf_path: str, client_name: str, total: float) -> dict:
    """
    WhatsApp: генерируем ссылку wa.me с готовым текстом.
    Пользователь открывает ссылку и сам прикрепляет PDF.
    
    phone — в формате +79991234567 или 79991234567 или 89991234567
    """
    # Нормализуем номер (убираем +, пробелы, скобки, дефисы)
    clean_phone = phone.replace("+", "").replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    
    # Если начинается с 8, заменяем на 7
    if clean_phone.startswith("8"):
        clean_phone = "7" + clean_phone[1:]
    
    # Если не начинается с 7, добавляем 7
    if not clean_phone.startswith("7"):
        clean_phone = "7" + clean_phone

    message = f"Здравствуйте, {client_name}! Ваша смета на сумму {total} ₽. Файл PDF во вложении."
    
    # Ссылка wa.me
    wa_link = f"https://wa.me/{clean_phone}?text={message}"

    return {
        "status": "ok",
        "method": "whatsapp",
        "recipient": phone,
        "pdf_path": os.path.abspath(pdf_path),
        "wa_link": wa_link,
        "message": f"Откройте ссылку для отправки в WhatsApp: {wa_link}\n\nPDF файл находится по пути: {os.path.abspath(pdf_path)}\n\nПрикрепите этот файл в открывшемся чате WhatsApp.",
        "action": "open_link",
        "link": wa_link
    }


# ===================== MAX (российский мессенджер) =====================

def send_via_max(phone: str, pdf_path: str, client_name: str, total: float) -> dict:
    """
    MAX — российский мессенджер, работает по номеру телефона.
    """
    clean_phone = phone.replace("+", "").replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    if clean_phone.startswith("8"):
        clean_phone = "7" + clean_phone[1:]
    if not clean_phone.startswith("7"):
        clean_phone = "7" + clean_phone

    message = f"Здравствуйте, {client_name}! Ваша смета на сумму {total} ₽."

    # Правильный формат deeplink для MAX
    max_link = f"https://max.ru/chat?phone={clean_phone}"

    return {
        "status": "ok",
        "method": "max",
        "recipient": phone,
        "pdf_path": os.path.abspath(pdf_path),
        "max_link": max_link,
        "message": f"Откройте ссылку для поиска контакта в MAX: {max_link}\n\nPDF файл: {os.path.abspath(pdf_path)}\n\nНайдите контакт по номеру +{clean_phone} и отправьте PDF вручную.",
        "action": "open_link",
        "link": max_link
    }


# ===================== УНИВЕРСАЛЬНАЯ ФУНКЦИЯ =====================

async def send_estimate(
    method: str,
    recipient: str,
    pdf_path: str,
    client_name: str,
    total: float
) -> dict:
    """
    Универсальная функция отправки.
    method: email | telegram | whatsapp | max
    """
    # Проверяем что PDF существует
    if not os.path.exists(pdf_path):
        return {
            "status": "error",
            "message": f"PDF файл не найден: {pdf_path}"
        }

    if method == "email":
        return send_via_email(recipient, pdf_path, client_name, total)
    
    elif method == "telegram":
        return await send_via_telegram(recipient, pdf_path, client_name, total)
    
    elif method == "whatsapp":
        return send_via_whatsapp(recipient, pdf_path, client_name, total)
    
    elif method == "max":
        return send_via_max(recipient, pdf_path, client_name, total)
    
    else:
        return {
            "status": "error",
            "message": f"Неизвестный метод отправки: {method}. Допустимые: email, telegram, whatsapp, max"
        }