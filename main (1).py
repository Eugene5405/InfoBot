import os
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

import httpx
import pytz
from timezonefinder import TimezoneFinder
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ==================== CONFIG ====================
TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required")

DATA_FILE = "user_data.json"

def load_user_data() -> Dict[int, Dict[str, Any]]:
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                raw = json.load(f)
                # keys come as strings from JSON
                return {int(k): v for k, v in raw.items()}
    except Exception as e:
        logging.error(f"Failed to load user data: {e}")
    return {}

def save_user_data():
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(user_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"Failed to save user data: {e}")

# Persistent storage
user_data: Dict[int, Dict[str, Any]] = load_user_data()

# ==================== LANGUAGES ====================
LANGUAGES = {
    "en": {"name": "English", "flag": "🇬🇧"},
    "ru": {"name": "Русский", "flag": "🇷🇺"},
    "uk": {"name": "Українська", "flag": "🇺🇦"},
    "es": {"name": "Español", "flag": "🇪🇸"},
    "de": {"name": "Deutsch", "flag": "🇩🇪"},
    "fr": {"name": "Français", "flag": "🇫🇷"},
    "pt": {"name": "Português", "flag": "🇧🇷"},
    "tr": {"name": "Türkçe", "flag": "🇹🇷"},
    "ar": {"name": "العربية", "flag": "🇸🇦"},
    "zh": {"name": "中文", "flag": "🇨🇳"},
}

# ==================== TEXTS ====================
TEXTS = {
    "en": {
        "choose_lang": "🌐 <b>Please choose your language:</b>",
        "welcome": (
            "👋 <b>Hello! Welcome to the Time & Weather Bot!</b>\n\n"
            "🌍 I show the current time and weather for your saved location.\n"
            "You can also check forecasts, rain, air quality, UV levels, "
            "sunrise and sunset, wind, and weather alerts.\n\n"
            "📍 First, please share your location using the button below "
            "or send a location pin.\n\n"
            "After that use the menu or commands."
        ),
        "welcome_ready": (
            "👋 <b>Hello! Welcome to the Time & Weather Bot!</b>\n\n"
            "🌍 I show the current time and weather for your saved location.\n"
            "You can also check forecasts, rain, air quality, UV levels, "
            "sunrise and sunset, wind, and weather alerts.\n\n"
            "✅ Your saved location is ready.\n"
            "Use the menu below or send a command."
        ),
        "help": (
            "📋 <b>Available commands:</b>\n\n"
            "/watch — current time\n"
            "/weather — current weather\n"
            "/week — 7-day forecast\n"
            "/hourly — next 24 hours\n"
            "/tomorrow — tomorrow's forecast\n"
            "/rain — rain probability\n"
            "/air — air quality\n"
            "/uv — UV index\n"
            "/sun — sunrise and sunset\n"
            "/wind — wind details\n"
            "/alerts — weather warnings\n"
            "/dst — next clock change (DST)\n"
            "/change_location — share a new location\n"
            "/language — change language\n"
            "/help — show this list\n\n"
            "Or just use the buttons below 👇"
        ),
        "btn_change_loc": "📍 Change location",
        "btn_help": "❓ Help",
        "btn_time": "🕐 Show time",
        "btn_share": "📌 Share my location",
        "btn_weather": "🌤 Weather commands",
        "btn_back": "⬅️ Back to main menu",
        "btn_current": "🌡 Current weather",
        "btn_week": "📅 7-day forecast",
        "btn_hourly": "⏱ Hourly",
        "btn_tomorrow": "📆 Tomorrow",
        "btn_rain": "🌧 Rain forecast",
        "btn_air": "🌬 Air quality",
        "btn_uv": "☀️ UV index",
        "btn_sun": "🌅 Sun times",
        "btn_wind": "💨 Wind",
        "btn_alerts": "⚠️ Weather alerts",
        "ask_location": "📍 Please share your location using the button below:",
        "location_saved": "✅ Location saved! I'll use it for time and weather commands.",
        "no_location": "❌ You haven't shared a location yet.\nPlease use the button «Share my location».",
        "current_time": "🕐 <b>Current time in {tz}:</b>\n{time}",
        "weather_title": "🌤 <b>Weather at your location:</b>\nTimezone: {tz}",
        "weather_body": (
            "{desc}\n"
            "🌡 Temperature: {temp}°C\n"
            "🤒 Feels like: {feels}°C\n"
            "💧 Humidity: {hum}%\n"
            "💨 Wind: {wind} km/h"
        ),
        "week_title": "📅 <b>7-day forecast:</b>\nTimezone: {tz}",
        "hourly_title": "⏱ <b>Hourly forecast (next 24h):</b>",
        "tomorrow_title": "📆 <b>Tomorrow at your location:</b>",
        "rain_title": "🌧 <b>Rain forecast for today:</b>",
        "air_title": "🌬 <b>Air quality:</b>",
        "uv_title": "☀️ <b>UV index for today:</b>",
        "sun_title": "🌅 <b>Sun times:</b>",
        "wind_title": "💨 <b>Wind:</b>",
        "alerts_title": "⚠️ <b>Weather alerts:</b>",
        "no_alerts": "✅ No significant weather alerts for today.",
        "dst_title": "🕒 <b>Daylight Saving Time (DST)</b>",
        "dst_next": "Next clock change in <b>{tz}</b>:\n📅 <b>{date}</b>\n⏰ From {old} → {new}\n\n{direction}",
        "dst_none": "✅ No DST transitions found in the next 2 years for {tz}.\nThis timezone may not observe daylight saving time.",
        "btn_dst": "🕒 DST / Clock change",
        "error": "❌ Something went wrong. Please try again later.",
        "lang_changed": "✅ Language changed!",
    },
    "ru": {
        "choose_lang": "🌐 <b>Пожалуйста, выберите язык:</b>",
        "welcome": (
            "👋 <b>Привет! Добро пожаловать в бот Время и Погода!</b>\n\n"
            "🌍 Я показываю текущее время и погоду для сохранённой локации.\n"
            "Также можно смотреть прогнозы, дождь, качество воздуха, УФ-индекс, "
            "восход и закат, ветер и предупреждения.\n\n"
            "📍 Сначала поделитесь своей геолокацией кнопкой ниже "
            "или отправьте точку на карте.\n\n"
            "После этого используйте меню или команды."
        ),
        "welcome_ready": (
            "👋 <b>Привет! Добро пожаловать в бот Время и Погода!</b>\n\n"
            "🌍 Я показываю текущее время и погоду для сохранённой локации.\n"
            "Также можно смотреть прогнозы, дождь, качество воздуха, УФ-индекс, "
            "восход и закат, ветер и предупреждения.\n\n"
            "✅ Ваша локация уже сохранена.\n"
            "Используйте меню ниже или отправьте команду."
        ),
        "help": (
            "📋 <b>Доступные команды:</b>\n\n"
            "/watch — текущее время\n"
            "/weather — текущая погода\n"
            "/week — прогноз на 7 дней\n"
            "/hourly — ближайшие 24 часа\n"
            "/tomorrow — прогноз на завтра\n"
            "/rain — вероятность дождя\n"
            "/air — качество воздуха\n"
            "/uv — УФ-индекс\n"
            "/sun — восход и закат\n"
            "/wind — ветер\n"
            "/alerts — предупреждения\n"
            "/dst — следующий перевод часов\n"
            "/change_location — изменить локацию\n"
            "/language — сменить язык\n"
            "/help — показать этот список\n\n"
            "Или просто используйте кнопки ниже 👇"
        ),
        "btn_change_loc": "📍 Изменить локацию",
        "btn_help": "❓ Помощь",
        "btn_time": "🕐 Показать время",
        "btn_share": "📌 Поделиться локацией",
        "btn_weather": "🌤 Команды погоды",
        "btn_back": "⬅️ Назад в меню",
        "btn_current": "🌡 Текущая погода",
        "btn_week": "📅 Прогноз на 7 дней",
        "btn_hourly": "⏱ По часам",
        "btn_tomorrow": "📆 Завтра",
        "btn_rain": "🌧 Прогноз дождя",
        "btn_air": "🌬 Качество воздуха",
        "btn_uv": "☀️ УФ-индекс",
        "btn_sun": "🌅 Восход и закат",
        "btn_wind": "💨 Ветер",
        "btn_alerts": "⚠️ Предупреждения",
        "ask_location": "📍 Пожалуйста, поделитесь локацией кнопкой ниже:",
        "location_saved": "✅ Локация сохранена! Теперь я буду использовать её для времени и погоды.",
        "no_location": "❌ Вы ещё не указали локацию.\nНажмите кнопку «Поделиться локацией».",
        "current_time": "🕐 <b>Текущее время в {tz}:</b>\n{time}",
        "weather_title": "🌤 <b>Погода в вашей локации:</b>\nЧасовой пояс: {tz}",
        "weather_body": (
            "{desc}\n"
            "🌡 Температура: {temp}°C\n"
            "🤒 Ощущается как: {feels}°C\n"
            "💧 Влажность: {hum}%\n"
            "💨 Ветер: {wind} км/ч"
        ),
        "week_title": "📅 <b>Прогноз на 7 дней:</b>\nЧасовой пояс: {tz}",
        "hourly_title": "⏱ <b>Прогноз по часам (24ч):</b>",
        "tomorrow_title": "📆 <b>Завтра в вашей локации:</b>",
        "rain_title": "🌧 <b>Прогноз дождя на сегодня:</b>",
        "air_title": "🌬 <b>Качество воздуха:</b>",
        "uv_title": "☀️ <b>УФ-индекс на сегодня:</b>",
        "sun_title": "🌅 <b>Восход и закат:</b>",
        "wind_title": "💨 <b>Ветер:</b>",
        "alerts_title": "⚠️ <b>Предупреждения о погоде:</b>",
        "no_alerts": "✅ Значительных предупреждений на сегодня нет.",
        "dst_title": "🕒 <b>Перевод часов (летнее/зимнее время)</b>",
        "dst_next": "Следующий перевод часов в <b>{tz}</b>:\n📅 <b>{date}</b>\n⏰ С {old} → {new}\n\n{direction}",
        "dst_none": "✅ В ближайшие 2 года перевода часов в {tz} не будет.\nВ этом часовом поясе летнее время может не использоваться.",
        "btn_dst": "🕒 Перевод часов",
        "error": "❌ Что-то пошло не так. Попробуйте позже.",
        "lang_changed": "✅ Язык изменён!",
    },
    "uk": {
        "choose_lang": "🌐 <b>Будь ласка, оберіть мову:</b>",
        "welcome": (
            "👋 <b>Привіт! Ласкаво просимо до бота Час і Погода!</b>\n\n"
            "🌍 Я показую поточний час і погоду для збереженої локації.\n"
            "Також можна дивитися прогнози, дощ, якість повітря, УФ-індекс, "
            "схід і захід сонця, вітер та попередження.\n\n"
            "📍 Спочатку поділіться своєю геолокацією кнопкою нижче "
            "або надішліть точку на карті.\n\n"
            "Після цього використовуйте меню або команди."
        ),
        "welcome_ready": (
            "👋 <b>Привіт! Ласкаво просимо до бота Час і Погода!</b>\n\n"
            "🌍 Я показую поточний час і погоду для збереженої локації.\n"
            "Також можна дивитися прогнози, дощ, якість повітря, УФ-індекс, "
            "схід і захід сонця, вітер та попередження.\n\n"
            "✅ Ваша локація вже збережена.\n"
            "Використовуйте меню нижче або надішліть команду."
        ),
        "help": (
            "📋 <b>Доступні команди:</b>\n\n"
            "/watch — поточний час\n"
            "/weather — поточна погода\n"
            "/week — прогноз на 7 днів\n"
            "/hourly — найближчі 24 години\n"
            "/tomorrow — прогноз на завтра\n"
            "/rain — ймовірність дощу\n"
            "/air — якість повітря\n"
            "/uv — УФ-індекс\n"
            "/sun — схід і захід\n"
            "/wind — вітер\n"
            "/alerts — попередження\n"
            "/dst — наступний перехід годинника\n"
            "/change_location — змінити локацію\n"
            "/language — змінити мову\n"
            "/help — показати цей список\n\n"
            "Або просто використовуйте кнопки нижче 👇"
        ),
        "btn_change_loc": "📍 Змінити локацію",
        "btn_help": "❓ Допомога",
        "btn_time": "🕐 Показати час",
        "btn_share": "📌 Поділитися локацією",
        "btn_weather": "🌤 Команди погоди",
        "btn_back": "⬅️ Назад до меню",
        "btn_current": "🌡 Поточна погода",
        "btn_week": "📅 Прогноз на 7 днів",
        "btn_hourly": "⏱ Погодинно",
        "btn_tomorrow": "📆 Завтра",
        "btn_rain": "🌧 Прогноз дощу",
        "btn_air": "🌬 Якість повітря",
        "btn_uv": "☀️ УФ-індекс",
        "btn_sun": "🌅 Схід і захід",
        "btn_wind": "💨 Вітер",
        "btn_alerts": "⚠️ Попередження",
        "ask_location": "📍 Будь ласка, поділіться локацією кнопкою нижче:",
        "location_saved": "✅ Локацію збережено! Тепер я буду використовувати її для часу та погоди.",
        "no_location": "❌ Ви ще не вказали локацію.\nНатисніть кнопку «Поділитися локацією».",
        "current_time": "🕐 <b>Поточний час у {tz}:</b>\n{time}",
        "weather_title": "🌤 <b>Погода у вашій локації:</b>\nЧасовий пояс: {tz}",
        "weather_body": (
            "{desc}\n"
            "🌡 Температура: {temp}°C\n"
            "🤒 Відчувається як: {feels}°C\n"
            "💧 Вологість: {hum}%\n"
            "💨 Вітер: {wind} км/год"
        ),
        "week_title": "📅 <b>Прогноз на 7 днів:</b>\nЧасовий пояс: {tz}",
        "hourly_title": "⏱ <b>Погодинний прогноз (24г):</b>",
        "tomorrow_title": "📆 <b>Завтра у вашій локації:</b>",
        "rain_title": "🌧 <b>Прогноз дощу на сьогодні:</b>",
        "air_title": "🌬 <b>Якість повітря:</b>",
        "uv_title": "☀️ <b>УФ-індекс на сьогодні:</b>",
        "sun_title": "🌅 <b>Схід і захід:</b>",
        "wind_title": "💨 <b>Вітер:</b>",
        "alerts_title": "⚠️ <b>Попередження про погоду:</b>",
        "no_alerts": "✅ Значних попереджень на сьогодні немає.",
        "dst_title": "🕒 <b>Перехід на літній/зимовий час</b>",
        "dst_next": "Наступний перехід годинника в <b>{tz}</b>:\n📅 <b>{date}</b>\n⏰ З {old} → {new}\n\n{direction}",
        "dst_none": "✅ У найближчі 2 роки переходу годинника в {tz} не буде.\nУ цьому часовому поясі літній час може не використовуватися.",
        "btn_dst": "🕒 Перехід годинника",
        "error": "❌ Щось пішло не так. Спробуйте пізніше.",
        "lang_changed": "✅ Мову змінено!",
    },
    "es": {
        "choose_lang": "🌐 <b>Por favor, elige tu idioma:</b>",
        "welcome": (
            "👋 <b>¡Hola! Bienvenido al Bot de Tiempo y Clima!</b>\n\n"
            "🌍 Muestro la hora actual y el clima de tu ubicación guardada.\n"
            "También puedes consultar pronósticos, lluvia, calidad del aire, "
            "índice UV, amanecer y atardecer, viento y alertas.\n\n"
            "📍 Primero comparte tu ubicación con el botón de abajo "
            "o envía un pin en el mapa.\n\n"
            "Después usa el menú o los comandos."
        ),
        "welcome_ready": (
            "👋 <b>¡Hola! Bienvenido al Bot de Tiempo y Clima!</b>\n\n"
            "🌍 Muestro la hora actual y el clima de tu ubicación guardada.\n"
            "También puedes consultar pronósticos, lluvia, calidad del aire, "
            "índice UV, amanecer y atardecer, viento y alertas.\n\n"
            "✅ Tu ubicación ya está guardada.\n"
            "Usa el menú de abajo o envía un comando."
        ),
        "help": (
            "📋 <b>Comandos disponibles:</b>\n\n"
            "/watch — hora actual\n"
            "/weather — clima actual\n"
            "/week — pronóstico 7 días\n"
            "/hourly — próximas 24 horas\n"
            "/tomorrow — pronóstico de mañana\n"
            "/rain — probabilidad de lluvia\n"
            "/air — calidad del aire\n"
            "/uv — índice UV\n"
            "/sun — amanecer y atardecer\n"
            "/wind — viento\n"
            "/alerts — alertas meteorológicas\n"
            "/dst — próximo cambio de hora\n"
            "/change_location — cambiar ubicación\n"
            "/language — cambiar idioma\n"
            "/help — mostrar esta lista\n\n"
            "O simplemente usa los botones 👇"
        ),
        "btn_change_loc": "📍 Cambiar ubicación",
        "btn_help": "❓ Ayuda",
        "btn_time": "🕐 Mostrar hora",
        "btn_share": "📌 Compartir ubicación",
        "btn_weather": "🌤 Comandos del clima",
        "btn_back": "⬅️ Volver al menú",
        "btn_current": "🌡 Clima actual",
        "btn_week": "📅 Pronóstico 7 días",
        "btn_hourly": "⏱ Por horas",
        "btn_tomorrow": "📆 Mañana",
        "btn_rain": "🌧 Pronóstico de lluvia",
        "btn_air": "🌬 Calidad del aire",
        "btn_uv": "☀️ Índice UV",
        "btn_sun": "🌅 Amanecer y atardecer",
        "btn_wind": "💨 Viento",
        "btn_alerts": "⚠️ Alertas",
        "ask_location": "📍 Por favor comparte tu ubicación con el botón de abajo:",
        "location_saved": "✅ ¡Ubicación guardada! La usaré para la hora y el clima.",
        "no_location": "❌ Aún no has compartido una ubicación.\nUsa el botón «Compartir ubicación».",
        "current_time": "🕐 <b>Hora actual en {tz}:</b>\n{time}",
        "weather_title": "🌤 <b>Clima en tu ubicación:</b>\nZona horaria: {tz}",
        "weather_body": (
            "{desc}\n"
            "🌡 Temperatura: {temp}°C\n"
            "🤒 Sensación: {feels}°C\n"
            "💧 Humedad: {hum}%\n"
            "💨 Viento: {wind} km/h"
        ),
        "week_title": "📅 <b>Pronóstico de 7 días:</b>\nZona horaria: {tz}",
        "hourly_title": "⏱ <b>Pronóstico por horas (24h):</b>",
        "tomorrow_title": "📆 <b>Mañana en tu ubicación:</b>",
        "rain_title": "🌧 <b>Pronóstico de lluvia para hoy:</b>",
        "air_title": "🌬 <b>Calidad del aire:</b>",
        "uv_title": "☀️ <b>Índice UV de hoy:</b>",
        "sun_title": "🌅 <b>Amanecer y atardecer:</b>",
        "wind_title": "💨 <b>Viento:</b>",
        "alerts_title": "⚠️ <b>Alertas meteorológicas:</b>",
        "no_alerts": "✅ No hay alertas significativas para hoy.",
        "dst_title": "🕒 <b>Cambio de hora (horario de verano)</b>",
        "dst_next": "Próximo cambio de hora en <b>{tz}</b>:\n📅 <b>{date}</b>\n⏰ De {old} → {new}\n\n{direction}",
        "dst_none": "✅ No hay cambios de hora en los próximos 2 años para {tz}.\nEsta zona horaria puede no observar el horario de verano.",
        "btn_dst": "🕒 Cambio de hora",
        "error": "❌ Algo salió mal. Inténtalo más tarde.",
        "lang_changed": "✅ ¡Idioma cambiado!",
    },
    "de": {
        "choose_lang": "🌐 <b>Bitte wähle deine Sprache:</b>",
        "welcome": (
            "👋 <b>Hallo! Willkommen beim Zeit- & Wetter-Bot!</b>\n\n"
            "🌍 Ich zeige die aktuelle Zeit und das Wetter für deinen gespeicherten Standort.\n"
            "Du kannst auch Vorhersagen, Regen, Luftqualität, UV-Index, "
            "Sonnenauf- und -untergang, Wind und Warnungen abrufen.\n\n"
            "📍 Teile zuerst deinen Standort mit dem Button unten "
            "oder sende einen Standort-Pin.\n\n"
            "Danach nutze das Menü oder die Befehle."
        ),
        "welcome_ready": (
            "👋 <b>Hallo! Willkommen beim Zeit- & Wetter-Bot!</b>\n\n"
            "🌍 Ich zeige die aktuelle Zeit und das Wetter für deinen gespeicherten Standort.\n"
            "Du kannst auch Vorhersagen, Regen, Luftqualität, UV-Index, "
            "Sonnenauf- und -untergang, Wind und Warnungen abrufen.\n\n"
            "✅ Dein Standort ist bereits gespeichert.\n"
            "Nutze das Menü unten oder sende einen Befehl."
        ),
        "help": (
            "📋 <b>Verfügbare Befehle:</b>\n\n"
            "/watch — aktuelle Zeit\n"
            "/weather — aktuelles Wetter\n"
            "/week — 7-Tage-Vorhersage\n"
            "/hourly — nächste 24 Stunden\n"
            "/tomorrow — Vorhersage für morgen\n"
            "/rain — Regenwahrscheinlichkeit\n"
            "/air — Luftqualität\n"
            "/uv — UV-Index\n"
            "/sun — Sonnenauf- und -untergang\n"
            "/wind — Wind\n"
            "/alerts — Wetterwarnungen\n"
            "/dst — nächste Zeitumstellung\n"
            "/change_location — Standort ändern\n"
            "/language — Sprache ändern\n"
            "/help — diese Liste anzeigen\n\n"
            "Oder nutze einfach die Buttons 👇"
        ),
        "btn_change_loc": "📍 Standort ändern",
        "btn_help": "❓ Hilfe",
        "btn_time": "🕐 Zeit anzeigen",
        "btn_share": "📌 Standort teilen",
        "btn_weather": "🌤 Wetter-Befehle",
        "btn_back": "⬅️ Zurück zum Menü",
        "btn_current": "🌡 Aktuelles Wetter",
        "btn_week": "📅 7-Tage-Vorhersage",
        "btn_hourly": "⏱ Stündlich",
        "btn_tomorrow": "📆 Morgen",
        "btn_rain": "🌧 Regenvorhersage",
        "btn_air": "🌬 Luftqualität",
        "btn_uv": "☀️ UV-Index",
        "btn_sun": "🌅 Sonnenzeiten",
        "btn_wind": "💨 Wind",
        "btn_alerts": "⚠️ Warnungen",
        "ask_location": "📍 Bitte teile deinen Standort mit dem Button unten:",
        "location_saved": "✅ Standort gespeichert! Ich verwende ihn für Zeit und Wetter.",
        "no_location": "❌ Du hast noch keinen Standort geteilt.\nNutze den Button «Standort teilen».",
        "current_time": "🕐 <b>Aktuelle Zeit in {tz}:</b>\n{time}",
        "weather_title": "🌤 <b>Wetter an deinem Standort:</b>\nZeitzone: {tz}",
        "weather_body": (
            "{desc}\n"
            "🌡 Temperatur: {temp}°C\n"
            "🤒 Gefühlte Temperatur: {feels}°C\n"
            "💧 Luftfeuchtigkeit: {hum}%\n"
            "💨 Wind: {wind} km/h"
        ),
        "week_title": "📅 <b>7-Tage-Vorhersage:</b>\nZeitzone: {tz}",
        "hourly_title": "⏱ <b>Stündliche Vorhersage (24h):</b>",
        "tomorrow_title": "📆 <b>Morgen an deinem Standort:</b>",
        "rain_title": "🌧 <b>Regenvorhersage für heute:</b>",
        "air_title": "🌬 <b>Luftqualität:</b>",
        "uv_title": "☀️ <b>UV-Index für heute:</b>",
        "sun_title": "🌅 <b>Sonnenzeiten:</b>",
        "wind_title": "💨 <b>Wind:</b>",
        "alerts_title": "⚠️ <b>Wetterwarnungen:</b>",
        "no_alerts": "✅ Keine signifikanten Warnungen für heute.",
        "dst_title": "🕒 <b>Zeitumstellung (Sommer-/Winterzeit)</b>",
        "dst_next": "Nächste Zeitumstellung in <b>{tz}</b>:\n📅 <b>{date}</b>\n⏰ Von {old} → {new}\n\n{direction}",
        "dst_none": "✅ In den nächsten 2 Jahren keine Zeitumstellung in {tz}.\nDiese Zeitzone beobachtet möglicherweise keine Sommerzeit.",
        "btn_dst": "🕒 Zeitumstellung",
        "error": "❌ Etwas ist schiefgelaufen. Bitte später erneut versuchen.",
        "lang_changed": "✅ Sprache geändert!",
    },
    "fr": {
        "choose_lang": "🌐 <b>Veuillez choisir votre langue :</b>",
        "welcome": (
            "👋 <b>Bonjour ! Bienvenue sur le Bot Temps & Météo !</b>\n\n"
            "🌍 Je montre l'heure actuelle et la météo pour votre position enregistrée.\n"
            "Vous pouvez aussi consulter les prévisions, la pluie, la qualité de l'air, "
            "l'indice UV, le lever et coucher du soleil, le vent et les alertes.\n\n"
            "📍 Commencez par partager votre position avec le bouton ci-dessous "
            "ou envoyez un pin sur la carte.\n\n"
            "Ensuite utilisez le menu ou les commandes."
        ),
        "welcome_ready": (
            "👋 <b>Bonjour ! Bienvenue sur le Bot Temps & Météo !</b>\n\n"
            "🌍 Je montre l'heure actuelle et la météo pour votre position enregistrée.\n"
            "Vous pouvez aussi consulter les prévisions, la pluie, la qualité de l'air, "
            "l'indice UV, le lever et coucher du soleil, le vent et les alertes.\n\n"
            "✅ Votre position est déjà enregistrée.\n"
            "Utilisez le menu ci-dessous ou envoyez une commande."
        ),
        "help": (
            "📋 <b>Commandes disponibles :</b>\n\n"
            "/watch — heure actuelle\n"
            "/weather — météo actuelle\n"
            "/week — prévisions 7 jours\n"
            "/hourly — prochaines 24 heures\n"
            "/tomorrow — prévisions de demain\n"
            "/rain — probabilité de pluie\n"
            "/air — qualité de l'air\n"
            "/uv — indice UV\n"
            "/sun — lever et coucher du soleil\n"
            "/wind — vent\n"
            "/alerts — alertes météo\n"
            "/dst — prochain changement d'heure\n"
            "/change_location — changer de position\n"
            "/language — changer de langue\n"
            "/help — afficher cette liste\n\n"
            "Ou utilisez simplement les boutons 👇"
        ),
        "btn_change_loc": "📍 Changer de position",
        "btn_help": "❓ Aide",
        "btn_time": "🕐 Afficher l'heure",
        "btn_share": "📌 Partager ma position",
        "btn_weather": "🌤 Commandes météo",
        "btn_back": "⬅️ Retour au menu",
        "btn_current": "🌡 Météo actuelle",
        "btn_week": "📅 Prévisions 7 jours",
        "btn_hourly": "⏱ Par heure",
        "btn_tomorrow": "📆 Demain",
        "btn_rain": "🌧 Prévisions de pluie",
        "btn_air": "🌬 Qualité de l'air",
        "btn_uv": "☀️ Indice UV",
        "btn_sun": "🌅 Lever/coucher",
        "btn_wind": "💨 Vent",
        "btn_alerts": "⚠️ Alertes",
        "ask_location": "📍 Veuillez partager votre position avec le bouton ci-dessous :",
        "location_saved": "✅ Position enregistrée ! Je l'utiliserai pour l'heure et la météo.",
        "no_location": "❌ Vous n'avez pas encore partagé de position.\nUtilisez le bouton « Partager ma position ».",
        "current_time": "🕐 <b>Heure actuelle à {tz} :</b>\n{time}",
        "weather_title": "🌤 <b>Météo à votre position :</b>\nFuseau horaire : {tz}",
        "weather_body": (
            "{desc}\n"
            "🌡 Température : {temp}°C\n"
            "🤒 Ressenti : {feels}°C\n"
            "💧 Humidité : {hum}%\n"
            "💨 Vent : {wind} km/h"
        ),
        "week_title": "📅 <b>Prévisions sur 7 jours :</b>\nFuseau horaire : {tz}",
        "hourly_title": "⏱ <b>Prévisions horaires (24h) :</b>",
        "tomorrow_title": "📆 <b>Demain à votre position :</b>",
        "rain_title": "🌧 <b>Prévisions de pluie pour aujourd'hui :</b>",
        "air_title": "🌬 <b>Qualité de l'air :</b>",
        "uv_title": "☀️ <b>Indice UV d'aujourd'hui :</b>",
        "sun_title": "🌅 <b>Lever et coucher du soleil :</b>",
        "wind_title": "💨 <b>Vent :</b>",
        "alerts_title": "⚠️ <b>Alertes météo :</b>",
        "no_alerts": "✅ Aucune alerte significative pour aujourd'hui.",
        "dst_title": "🕒 <b>Changement d'heure (heure d'été)</b>",
        "dst_next": "Prochain changement d'heure à <b>{tz}</b> :\n📅 <b>{date}</b>\n⏰ De {old} → {new}\n\n{direction}",
        "dst_none": "✅ Aucun changement d'heure dans les 2 prochaines années pour {tz}.\nCe fuseau horaire n'observe peut-être pas l'heure d'été.",
        "btn_dst": "🕒 Changement d'heure",
        "error": "❌ Une erreur est survenue. Réessayez plus tard.",
        "lang_changed": "✅ Langue changée !",
    },
    "pt": {
        "choose_lang": "🌐 <b>Por favor, escolha seu idioma:</b>",
        "welcome": (
            "👋 <b>Olá! Bem-vindo ao Bot de Tempo e Clima!</b>\n\n"
            "🌍 Mostro a hora atual e o clima da sua localização salva.\n"
            "Você também pode verificar previsões, chuva, qualidade do ar, "
            "índice UV, nascer e pôr do sol, vento e alertas.\n\n"
            "📍 Primeiro compartilhe sua localização com o botão abaixo "
            "ou envie um pin no mapa.\n\n"
            "Depois use o menu ou os comandos."
        ),
        "welcome_ready": (
            "👋 <b>Olá! Bem-vindo ao Bot de Tempo e Clima!</b>\n\n"
            "🌍 Mostro a hora atual e o clima da sua localização salva.\n"
            "Você também pode verificar previsões, chuva, qualidade do ar, "
            "índice UV, nascer e pôr do sol, vento e alertas.\n\n"
            "✅ Sua localização já está salva.\n"
            "Use o menu abaixo ou envie um comando."
        ),
        "help": (
            "📋 <b>Comandos disponíveis:</b>\n\n"
            "/watch — hora atual\n"
            "/weather — clima atual\n"
            "/week — previsão 7 dias\n"
            "/hourly — próximas 24 horas\n"
            "/tomorrow — previsão de amanhã\n"
            "/rain — probabilidade de chuva\n"
            "/air — qualidade do ar\n"
            "/uv — índice UV\n"
            "/sun — nascer e pôr do sol\n"
            "/wind — vento\n"
            "/alerts — alertas meteorológicos\n"
            "/dst — próxima mudança de horário\n"
            "/change_location — mudar localização\n"
            "/language — mudar idioma\n"
            "/help — mostrar esta lista\n\n"
            "Ou simplesmente use os botões 👇"
        ),
        "btn_change_loc": "📍 Mudar localização",
        "btn_help": "❓ Ajuda",
        "btn_time": "🕐 Mostrar hora",
        "btn_share": "📌 Compartilhar localização",
        "btn_weather": "🌤 Comandos do clima",
        "btn_back": "⬅️ Voltar ao menu",
        "btn_current": "🌡 Clima atual",
        "btn_week": "📅 Previsão 7 dias",
        "btn_hourly": "⏱ Por hora",
        "btn_tomorrow": "📆 Amanhã",
        "btn_rain": "🌧 Previsão de chuva",
        "btn_air": "🌬 Qualidade do ar",
        "btn_uv": "☀️ Índice UV",
        "btn_sun": "🌅 Nascer/pôr do sol",
        "btn_wind": "💨 Vento",
        "btn_alerts": "⚠️ Alertas",
        "ask_location": "📍 Por favor compartilhe sua localização com o botão abaixo:",
        "location_saved": "✅ Localização salva! Vou usá-la para hora e clima.",
        "no_location": "❌ Você ainda não compartilhou uma localização.\nUse o botão «Compartilhar localização».",
        "current_time": "🕐 <b>Hora atual em {tz}:</b>\n{time}",
        "weather_title": "🌤 <b>Clima na sua localização:</b>\nFuso horário: {tz}",
        "weather_body": (
            "{desc}\n"
            "🌡 Temperatura: {temp}°C\n"
            "🤒 Sensação: {feels}°C\n"
            "💧 Umidade: {hum}%\n"
            "💨 Vento: {wind} km/h"
        ),
        "week_title": "📅 <b>Previsão de 7 dias:</b>\nFuso horário: {tz}",
        "hourly_title": "⏱ <b>Previsão por hora (24h):</b>",
        "tomorrow_title": "📆 <b>Amanhã na sua localização:</b>",
        "rain_title": "🌧 <b>Previsão de chuva para hoje:</b>",
        "air_title": "🌬 <b>Qualidade do ar:</b>",
        "uv_title": "☀️ <b>Índice UV de hoje:</b>",
        "sun_title": "🌅 <b>Nascer e pôr do sol:</b>",
        "wind_title": "💨 <b>Vento:</b>",
        "alerts_title": "⚠️ <b>Alertas meteorológicos:</b>",
        "no_alerts": "✅ Nenhum alerta significativo para hoje.",
        "dst_title": "🕒 <b>Mudança de horário (horário de verão)</b>",
        "dst_next": "Próxima mudança de horário em <b>{tz}</b>:\n📅 <b>{date}</b>\n⏰ De {old} → {new}\n\n{direction}",
        "dst_none": "✅ Nenhuma mudança de horário nos próximos 2 anos para {tz}.\nEste fuso horário pode não observar o horário de verão.",
        "btn_dst": "🕒 Mudança de horário",
        "error": "❌ Algo deu errado. Tente novamente mais tarde.",
        "lang_changed": "✅ Idioma alterado!",
    },
    "tr": {
        "choose_lang": "🌐 <b>Lütfen dilinizi seçin:</b>",
        "welcome": (
            "👋 <b>Merhaba! Zaman ve Hava Botuna hoş geldiniz!</b>\n\n"
            "🌍 Kayıtlı konumunuz için mevcut saati ve havayı gösteriyorum.\n"
            "Ayrıca tahminler, yağmur, hava kalitesi, UV endeksi, "
            "güneş doğuş/batış, rüzgar ve uyarıları kontrol edebilirsiniz.\n\n"
            "📍 Önce aşağıdaki butonla konumunuzu paylaşın "
            "veya haritadan bir nokta gönderin.\n\n"
            "Sonra menüyü veya komutları kullanın."
        ),
        "welcome_ready": (
            "👋 <b>Merhaba! Zaman ve Hava Botuna hoş geldiniz!</b>\n\n"
            "🌍 Kayıtlı konumunuz için mevcut saati ve havayı gösteriyorum.\n"
            "Ayrıca tahminler, yağmur, hava kalitesi, UV endeksi, "
            "güneş doğuş/batış, rüzgar ve uyarıları kontrol edebilirsiniz.\n\n"
            "✅ Konumunuz zaten kayıtlı.\n"
            "Aşağıdaki menüyü kullanın veya bir komut gönderin."
        ),
        "help": (
            "📋 <b>Mevcut komutlar:</b>\n\n"
            "/watch — mevcut saat\n"
            "/weather — mevcut hava\n"
            "/week — 7 günlük tahmin\n"
            "/hourly — sonraki 24 saat\n"
            "/tomorrow — yarının tahmini\n"
            "/rain — yağmur olasılığı\n"
            "/air — hava kalitesi\n"
            "/uv — UV endeksi\n"
            "/sun — güneş doğuş/batış\n"
            "/wind — rüzgar\n"
            "/alerts — hava uyarıları\n"
            "/dst — sonraki saat değişimi\n"
            "/change_location — konum değiştir\n"
            "/language — dil değiştir\n"
            "/help — bu listeyi göster\n\n"
            "Veya sadece aşağıdaki butonları kullanın 👇"
        ),
        "btn_change_loc": "📍 Konum değiştir",
        "btn_help": "❓ Yardım",
        "btn_time": "🕐 Saati göster",
        "btn_share": "📌 Konumumu paylaş",
        "btn_weather": "🌤 Hava komutları",
        "btn_back": "⬅️ Ana menüye dön",
        "btn_current": "🌡 Mevcut hava",
        "btn_week": "📅 7 günlük tahmin",
        "btn_hourly": "⏱ Saatlik",
        "btn_tomorrow": "📆 Yarın",
        "btn_rain": "🌧 Yağmur tahmini",
        "btn_air": "🌬 Hava kalitesi",
        "btn_uv": "☀️ UV endeksi",
        "btn_sun": "🌅 Güneş saatleri",
        "btn_wind": "💨 Rüzgar",
        "btn_alerts": "⚠️ Uyarılar",
        "ask_location": "📍 Lütfen aşağıdaki butonla konumunuzu paylaşın:",
        "location_saved": "✅ Konum kaydedildi! Saat ve hava için kullanacağım.",
        "no_location": "❌ Henüz bir konum paylaşmadınız.\n«Konumumu paylaş» butonunu kullanın.",
        "current_time": "🕐 <b>{tz} saati:</b>\n{time}",
        "weather_title": "🌤 <b>Konumunuzdaki hava:</b>\nSaat dilimi: {tz}",
        "weather_body": (
            "{desc}\n"
            "🌡 Sıcaklık: {temp}°C\n"
            "🤒 Hissedilen: {feels}°C\n"
            "💧 Nem: {hum}%\n"
            "💨 Rüzgar: {wind} km/s"
        ),
        "week_title": "📅 <b>7 günlük tahmin:</b>\nSaat dilimi: {tz}",
        "hourly_title": "⏱ <b>Saatlik tahmin (24s):</b>",
        "tomorrow_title": "📆 <b>Yarın konumunuzda:</b>",
        "rain_title": "🌧 <b>Bugünün yağmur tahmini:</b>",
        "air_title": "🌬 <b>Hava kalitesi:</b>",
        "uv_title": "☀️ <b>Bugünün UV endeksi:</b>",
        "sun_title": "🌅 <b>Güneş saatleri:</b>",
        "wind_title": "💨 <b>Rüzgar:</b>",
        "alerts_title": "⚠️ <b>Hava uyarıları:</b>",
        "no_alerts": "✅ Bugün için önemli uyarı yok.",
        "dst_title": "🕒 <b>Saat değişimi (yaz saati)</b>",
        "dst_next": "<b>{tz}</b> için sonraki saat değişimi:\n📅 <b>{date}</b>\n⏰ {old} → {new}\n\n{direction}",
        "dst_none": "✅ Önümüzdeki 2 yıl içinde {tz} için saat değişimi yok.\nBu saat dilimi yaz saatini uygulamıyor olabilir.",
        "btn_dst": "🕒 Saat değişimi",
        "error": "❌ Bir şeyler ters gitti. Lütfen daha sonra tekrar deneyin.",
        "lang_changed": "✅ Dil değiştirildi!",
    },
    "ar": {
        "choose_lang": "🌐 <b>الرجاء اختيار لغتك:</b>",
        "welcome": (
            "👋 <b>مرحباً! أهلاً بك في بوت الوقت والطقس!</b>\n\n"
            "🌍 أعرض الوقت الحالي والطقس لموقعك المحفوظ.\n"
            "يمكنك أيضاً التحقق من التوقعات، المطر، جودة الهواء، "
            "مؤشر الأشعة فوق البنفسجية، شروق وغروب الشمس، الرياح والتنبيهات.\n\n"
            "📍 أولاً شارك موقعك باستخدام الزر أدناه "
            "أو أرسل دبوس موقع على الخريطة.\n\n"
            "بعد ذلك استخدم القائمة أو الأوامر."
        ),
        "welcome_ready": (
            "👋 <b>مرحباً! أهلاً بك في بوت الوقت والطقس!</b>\n\n"
            "🌍 أعرض الوقت الحالي والطقس لموقعك المحفوظ.\n"
            "يمكنك أيضاً التحقق من التوقعات، المطر، جودة الهواء، "
            "مؤشر الأشعة فوق البنفسجية، شروق وغروب الشمس، الرياح والتنبيهات.\n\n"
            "✅ موقعك محفوظ بالفعل.\n"
            "استخدم القائمة أدناه أو أرسل أمراً."
        ),
        "help": (
            "📋 <b>الأوامر المتاحة:</b>\n\n"
            "/watch — الوقت الحالي\n"
            "/weather — الطقس الحالي\n"
            "/week — توقعات 7 أيام\n"
            "/hourly — الـ 24 ساعة القادمة\n"
            "/tomorrow — توقعات الغد\n"
            "/rain — احتمالية المطر\n"
            "/air — جودة الهواء\n"
            "/uv — مؤشر الأشعة فوق البنفسجية\n"
            "/sun — شروق وغروب الشمس\n"
            "/wind — الرياح\n"
            "/alerts — تنبيهات الطقس\n"
            "/dst — التغيير التالي للساعة\n"
            "/change_location — تغيير الموقع\n"
            "/language — تغيير اللغة\n"
            "/help — عرض هذه القائمة\n\n"
            "أو استخدم الأزرار أدناه 👇"
        ),
        "btn_change_loc": "📍 تغيير الموقع",
        "btn_help": "❓ مساعدة",
        "btn_time": "🕐 عرض الوقت",
        "btn_share": "📌 مشاركة موقعي",
        "btn_weather": "🌤 أوامر الطقس",
        "btn_back": "⬅️ العودة للقائمة",
        "btn_current": "🌡 الطقس الحالي",
        "btn_week": "📅 توقعات 7 أيام",
        "btn_hourly": "⏱ كل ساعة",
        "btn_tomorrow": "📆 غداً",
        "btn_rain": "🌧 توقعات المطر",
        "btn_air": "🌬 جودة الهواء",
        "btn_uv": "☀️ مؤشر UV",
        "btn_sun": "🌅 أوقات الشمس",
        "btn_wind": "💨 الرياح",
        "btn_alerts": "⚠️ التنبيهات",
        "ask_location": "📍 الرجاء مشاركة موقعك باستخدام الزر أدناه:",
        "location_saved": "✅ تم حفظ الموقع! سأستخدمه للوقت والطقس.",
        "no_location": "❌ لم تشارك موقعاً بعد.\nاستخدم زر «مشاركة موقعي».",
        "current_time": "🕐 <b>الوقت الحالي في {tz}:</b>\n{time}",
        "weather_title": "🌤 <b>الطقس في موقعك:</b>\nالمنطقة الزمنية: {tz}",
        "weather_body": (
            "{desc}\n"
            "🌡 درجة الحرارة: {temp}°C\n"
            "🤒 الإحساس: {feels}°C\n"
            "💧 الرطوبة: {hum}%\n"
            "💨 الرياح: {wind} كم/س"
        ),
        "week_title": "📅 <b>توقعات 7 أيام:</b>\nالمنطقة الزمنية: {tz}",
        "hourly_title": "⏱ <b>التوقعات كل ساعة (24س):</b>",
        "tomorrow_title": "📆 <b>غداً في موقعك:</b>",
        "rain_title": "🌧 <b>توقعات المطر لليوم:</b>",
        "air_title": "🌬 <b>جودة الهواء:</b>",
        "uv_title": "☀️ <b>مؤشر UV لليوم:</b>",
        "sun_title": "🌅 <b>أوقات الشمس:</b>",
        "wind_title": "💨 <b>الرياح:</b>",
        "alerts_title": "⚠️ <b>تنبيهات الطقس:</b>",
        "no_alerts": "✅ لا توجد تنبيهات مهمة لليوم.",
        "dst_title": "🕒 <b>تغيير الساعة (التوقيت الصيفي)</b>",
        "dst_next": "التغيير التالي للساعة في <b>{tz}</b>:\n📅 <b>{date}</b>\n⏰ من {old} → {new}\n\n{direction}",
        "dst_none": "✅ لا يوجد تغيير للساعة في السنتين القادمتين لـ {tz}.\nقد لا يطبق هذا المنطقة الزمنية التوقيت الصيفي.",
        "btn_dst": "🕒 تغيير الساعة",
        "error": "❌ حدث خطأ ما. حاول مرة أخرى لاحقاً.",
        "lang_changed": "✅ تم تغيير اللغة!",
    },
    "zh": {
        "choose_lang": "🌐 <b>请选择您的语言：</b>",
        "welcome": (
            "👋 <b>你好！欢迎使用时间与天气机器人！</b>\n\n"
            "🌍 我显示您保存位置的当前时间和天气。\n"
            "您还可以查看预报、降雨、空气质量、紫外线指数、"
            "日出日落、风力和天气预警。\n\n"
            "📍 请先使用下方按钮分享您的位置，"
            "或发送地图上的位置点。\n\n"
            "之后使用菜单或命令。"
        ),
        "welcome_ready": (
            "👋 <b>你好！欢迎使用时间与天气机器人！</b>\n\n"
            "🌍 我显示您保存位置的当前时间和天气。\n"
            "您还可以查看预报、降雨、空气质量、紫外线指数、"
            "日出日落、风力和天气预警。\n\n"
            "✅ 您的位置已保存。\n"
            "请使用下方菜单或发送命令。"
        ),
        "help": (
            "📋 <b>可用命令：</b>\n\n"
            "/watch — 当前时间\n"
            "/weather — 当前天气\n"
            "/week — 7天预报\n"
            "/hourly — 未来24小时\n"
            "/tomorrow — 明天的预报\n"
            "/rain — 降雨概率\n"
            "/air — 空气质量\n"
            "/uv — 紫外线指数\n"
            "/sun — 日出日落\n"
            "/wind — 风力\n"
            "/alerts — 天气预警\n"
            "/dst — 下次时钟调整\n"
            "/change_location — 更改位置\n"
            "/language — 更改语言\n"
            "/help — 显示此列表\n\n"
            "或直接使用下方按钮 👇"
        ),
        "btn_change_loc": "📍 更改位置",
        "btn_help": "❓ 帮助",
        "btn_time": "🕐 显示时间",
        "btn_share": "📌 分享我的位置",
        "btn_weather": "🌤 天气命令",
        "btn_back": "⬅️ 返回主菜单",
        "btn_current": "🌡 当前天气",
        "btn_week": "📅 7天预报",
        "btn_hourly": "⏱ 每小时",
        "btn_tomorrow": "📆 明天",
        "btn_rain": "🌧 降雨预报",
        "btn_air": "🌬 空气质量",
        "btn_uv": "☀️ 紫外线指数",
        "btn_sun": "🌅 日出日落",
        "btn_wind": "💨 风力",
        "btn_alerts": "⚠️ 天气预警",
        "ask_location": "📍 请使用下方按钮分享您的位置：",
        "location_saved": "✅ 位置已保存！我将用它来显示时间和天气。",
        "no_location": "❌ 您还没有分享位置。\n请使用「分享我的位置」按钮。",
        "current_time": "🕐 <b>{tz} 的当前时间：</b>\n{time}",
        "weather_title": "🌤 <b>您位置的天气：</b>\n时区：{tz}",
        "weather_body": (
            "{desc}\n"
            "🌡 温度：{temp}°C\n"
            "🤒 体感温度：{feels}°C\n"
            "💧 湿度：{hum}%\n"
            "💨 风速：{wind} km/h"
        ),
        "week_title": "📅 <b>7天预报：</b>\n时区：{tz}",
        "hourly_title": "⏱ <b>每小时预报（24小时）：</b>",
        "tomorrow_title": "📆 <b>明天您位置的天气：</b>",
        "rain_title": "🌧 <b>今天的降雨预报：</b>",
        "air_title": "🌬 <b>空气质量：</b>",
        "uv_title": "☀️ <b>今天的紫外线指数：</b>",
        "sun_title": "🌅 <b>日出日落：</b>",
        "wind_title": "💨 <b>风力：</b>",
        "alerts_title": "⚠️ <b>天气预警：</b>",
        "no_alerts": "✅ 今天没有重要预警。",
        "dst_title": "🕒 <b>夏令时 / 冬令时切换</b>",
        "dst_next": "<b>{tz}</b> 的下一次时钟调整：\n📅 <b>{date}</b>\n⏰ 从 {old} → {new}\n\n{direction}",
        "dst_none": "✅ 未来两年内 {tz} 没有时钟调整。\n该时区可能不实行夏令时。",
        "btn_dst": "🕒 夏令时切换",
        "error": "❌ 出了点问题。请稍后再试。",
        "lang_changed": "✅ 语言已更改！",
    },
}

# Weather code descriptions (WMO)
WEATHER_CODES = {
    0: {"en": "Clear sky", "ru": "Ясно", "uk": "Ясно", "es": "Cielo despejado", "de": "Klarer Himmel", "fr": "Ciel dégagé", "pt": "Céu limpo", "tr": "Açık gökyüzü", "ar": "سماء صافية", "zh": "晴朗"},
    1: {"en": "Mainly clear", "ru": "Преимущественно ясно", "uk": "Переважно ясно", "es": "Mayormente despejado", "de": "Überwiegend klar", "fr": "Principalement dégagé", "pt": "Principalmente limpo", "tr": "Çoğunlukla açık", "ar": "صافٍ في الغالب", "zh": "大部晴朗"},
    2: {"en": "Partly cloudy", "ru": "Переменная облачность", "uk": "Мінлива хмарність", "es": "Parcialmente nublado", "de": "Teilweise bewölkt", "fr": "Partiellement nuageux", "pt": "Parcialmente nublado", "tr": "Parçalı bulutlu", "ar": "غائم جزئياً", "zh": "局部多云"},
    3: {"en": "Overcast", "ru": "Пасмурно", "uk": "Хмарно", "es": "Nublado", "de": "Bedeckt", "fr": "Couvert", "pt": "Nublado", "tr": "Kapalı", "ar": "غائم", "zh": "阴天"},
    45: {"en": "Fog", "ru": "Туман", "uk": "Туман", "es": "Niebla", "de": "Nebel", "fr": "Brouillard", "pt": "Neblina", "tr": "Sis", "ar": "ضباب", "zh": "雾"},
    48: {"en": "Depositing rime fog", "ru": "Изморозь", "uk": "Іній", "es": "Niebla con escarcha", "de": "Reifnebel", "fr": "Brouillard givrant", "pt": "Neblina com geada", "tr": "Kırağılı sis", "ar": "ضباب متجمد", "zh": "雾凇"},
    51: {"en": "Light drizzle", "ru": "Лёгкая морось", "uk": "Легка мряка", "es": "Llovizna ligera", "de": "Leichter Nieselregen", "fr": "Bruine légère", "pt": "Garoa leve", "tr": "Hafif çiseleme", "ar": "رذاذ خفيف", "zh": "小毛毛雨"},
    53: {"en": "Moderate drizzle", "ru": "Умеренная морось", "uk": "Помірна мряка", "es": "Llovizna moderada", "de": "Mäßiger Nieselregen", "fr": "Bruine modérée", "pt": "Garoa moderada", "tr": "Orta çiseleme", "ar": "رذاذ متوسط", "zh": "中等毛毛雨"},
    55: {"en": "Dense drizzle", "ru": "Сильная морось", "uk": "Густа мряка", "es": "Llovizna densa", "de": "Dichter Nieselregen", "fr": "Bruine dense", "pt": "Garoa densa", "tr": "Yoğun çiseleme", "ar": "رذاذ كثيف", "zh": "大毛毛雨"},
    61: {"en": "Slight rain", "ru": "Небольшой дождь", "uk": "Невеликий дощ", "es": "Lluvia ligera", "de": "Leichter Regen", "fr": "Pluie légère", "pt": "Chuva leve", "tr": "Hafif yağmur", "ar": "مطر خفيف", "zh": "小雨"},
    63: {"en": "Moderate rain", "ru": "Умеренный дождь", "uk": "Помірний дощ", "es": "Lluvia moderada", "de": "Mäßiger Regen", "fr": "Pluie modérée", "pt": "Chuva moderada", "tr": "Orta yağmur", "ar": "مطر متوسط", "zh": "中雨"},
    65: {"en": "Heavy rain", "ru": "Сильный дождь", "uk": "Сильний дощ", "es": "Lluvia fuerte", "de": "Starker Regen", "fr": "Pluie forte", "pt": "Chuva forte", "tr": "Şiddetli yağmur", "ar": "مطر غزير", "zh": "大雨"},
    71: {"en": "Slight snow", "ru": "Небольшой снег", "uk": "Невеликий сніг", "es": "Nieve ligera", "de": "Leichter Schnee", "fr": "Neige légère", "pt": "Neve leve", "tr": "Hafif kar", "ar": "ثلج خفيف", "zh": "小雪"},
    73: {"en": "Moderate snow", "ru": "Умеренный снег", "uk": "Помірний сніг", "es": "Nieve moderada", "de": "Mäßiger Schnee", "fr": "Neige modérée", "pt": "Neve moderada", "tr": "Orta kar", "ar": "ثلج متوسط", "zh": "中雪"},
    75: {"en": "Heavy snow", "ru": "Сильный снег", "uk": "Сильний сніг", "es": "Nieve fuerte", "de": "Starker Schnee", "fr": "Neige forte", "pt": "Neve forte", "tr": "Yoğun kar", "ar": "ثلج كثيف", "zh": "大雪"},
    80: {"en": "Slight rain showers", "ru": "Небольшие ливни", "uk": "Невеликі зливи", "es": "Chubascos ligeros", "de": "Leichte Regenschauer", "fr": "Averses légères", "pt": "Pancadas leves", "tr": "Hafif sağanak", "ar": "زخات مطر خفيفة", "zh": "小阵雨"},
    81: {"en": "Moderate rain showers", "ru": "Умеренные ливни", "uk": "Помірні зливи", "es": "Chubascos moderados", "de": "Mäßige Regenschauer", "fr": "Averses modérées", "pt": "Pancadas moderadas", "tr": "Orta sağanak", "ar": "زخات مطر متوسطة", "zh": "中阵雨"},
    82: {"en": "Violent rain showers", "ru": "Сильные ливни", "uk": "Сильні зливи", "es": "Chubascos fuertes", "de": "Heftige Regenschauer", "fr": "Averses violentes", "pt": "Pancadas fortes", "tr": "Şiddetli sağanak", "ar": "زخات مطر عنيفة", "zh": "强阵雨"},
    95: {"en": "Thunderstorm", "ru": "Гроза", "uk": "Гроза", "es": "Tormenta", "de": "Gewitter", "fr": "Orage", "pt": "Tempestade", "tr": "Gök gürültülü fırtına", "ar": "عاصفة رعدية", "zh": "雷暴"},
    96: {"en": "Thunderstorm with slight hail", "ru": "Гроза с небольшим градом", "uk": "Гроза з невеликим градом", "es": "Tormenta con granizo ligero", "de": "Gewitter mit leichtem Hagel", "fr": "Orage avec grêle légère", "pt": "Tempestade com granizo leve", "tr": "Hafif dolu ile fırtına", "ar": "عاصفة رعدية مع برد خفيف", "zh": "雷暴伴小冰雹"},
    99: {"en": "Thunderstorm with heavy hail", "ru": "Гроза с сильным градом", "uk": "Гроза з сильним градом", "es": "Tormenta con granizo fuerte", "de": "Gewitter mit starkem Hagel", "fr": "Orage avec grêle forte", "pt": "Tempestade com granizo forte", "tr": "Yoğun dolu ile fırtına", "ar": "عاصفة رعدية مع برد كثيف", "zh": "雷暴伴大冰雹"},
}

tf = TimezoneFinder()

# ==================== HELPERS ====================
def get_lang(user_id: int) -> str:
    return user_data.get(user_id, {}).get("lang", "en")

def t(user_id: int, key: str) -> str:
    lang = get_lang(user_id)
    return TEXTS.get(lang, TEXTS["en"]).get(key, TEXTS["en"].get(key, key))

def get_weather_desc(code: int, lang: str) -> str:
    return WEATHER_CODES.get(code, {}).get(lang, WEATHER_CODES.get(code, {}).get("en", "Unknown"))

def main_keyboard(user_id: int) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [t(user_id, "btn_change_loc"), t(user_id, "btn_help"), t(user_id, "btn_time")],
            [t(user_id, "btn_share"), t(user_id, "btn_weather")],
            [t(user_id, "btn_dst")],
        ],
        resize_keyboard=True,
    )

def weather_keyboard(user_id: int) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [t(user_id, "btn_current"), t(user_id, "btn_week")],
            [t(user_id, "btn_hourly"), t(user_id, "btn_tomorrow")],
            [t(user_id, "btn_rain"), t(user_id, "btn_air")],
            [t(user_id, "btn_uv"), t(user_id, "btn_sun")],
            [t(user_id, "btn_wind"), t(user_id, "btn_alerts")],
            [t(user_id, "btn_back")],
        ],
        resize_keyboard=True,
    )

def lang_keyboard() -> InlineKeyboardMarkup:
    buttons = []
    row = []
    for code, info in LANGUAGES.items():
        row.append(InlineKeyboardButton(f"{info['flag']} {info['name']}", callback_data=f"lang_{code}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(buttons)

async def fetch_weather(lat: float, lon: float) -> Optional[dict]:
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m,wind_direction_10m"
        "&hourly=temperature_2m,precipitation_probability,weather_code,wind_speed_10m"
        "&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,sunrise,sunset,uv_index_max,wind_speed_10m_max,wind_direction_10m_dominant"
        "&timezone=auto"
        "&forecast_days=7"
    )
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(url)
            r.raise_for_status()
            return r.json()
    except Exception as e:
        logging.error(f"Weather fetch error: {e}")
        return None

async def fetch_air(lat: float, lon: float) -> Optional[dict]:
    url = (
        "https://air-quality-api.open-meteo.com/v1/air-quality"
        f"?latitude={lat}&longitude={lon}"
        "&current=european_aqi,pm2_5,pm10,uv_index"
        "&timezone=auto"
    )
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(url)
            r.raise_for_status()
            return r.json()
    except Exception as e:
        logging.error(f"Air quality fetch error: {e}")
        return None

def get_user_location(user_id: int) -> Optional[tuple]:
    data = user_data.get(user_id, {})
    if "lat" in data and "lon" in data:
        return data["lat"], data["lon"]
    return None

# ==================== HANDLERS ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_data:
        user_data[user_id] = {}
    await update.message.reply_text(
        t(user_id, "choose_lang"),
        reply_markup=lang_keyboard(),
        parse_mode="HTML",
    )

async def language_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text(
        t(user_id, "choose_lang"),
        reply_markup=lang_keyboard(),
        parse_mode="HTML",
    )

async def lang_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    lang_code = query.data.replace("lang_", "")
    if user_id not in user_data:
        user_data[user_id] = {}
    user_data[user_id]["lang"] = lang_code
    save_user_data()

    has_loc = get_user_location(user_id) is not None
    text = t(user_id, "welcome_ready") if has_loc else t(user_id, "welcome")
    await query.edit_message_text(text, parse_mode="HTML")
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text="👇",
        reply_markup=main_keyboard(user_id),
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text(t(user_id, "help"), parse_mode="HTML", reply_markup=main_keyboard(user_id))

async def change_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    kb = ReplyKeyboardMarkup(
        [[KeyboardButton(t(user_id, "btn_share"), request_location=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    await update.message.reply_text(t(user_id, "ask_location"), reply_markup=kb)

async def location_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    loc = update.message.location
    if user_id not in user_data:
        user_data[user_id] = {}
    user_data[user_id]["lat"] = loc.latitude
    user_data[user_id]["lon"] = loc.longitude
    tz_name = tf.timezone_at(lat=loc.latitude, lng=loc.longitude) or "UTC"
    user_data[user_id]["tz"] = tz_name
    save_user_data()
    await update.message.reply_text(t(user_id, "location_saved"), reply_markup=main_keyboard(user_id))

async def show_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    loc = get_user_location(user_id)
    if not loc:
        await update.message.reply_text(t(user_id, "no_location"), reply_markup=main_keyboard(user_id))
        return
    tz_name = user_data[user_id].get("tz", "UTC")
    try:
        tz = pytz.timezone(tz_name)
        now = datetime.now(tz)
        time_str = now.strftime("%A, %d %B %Y at %H:%M:%S %Z")
    except Exception:
        time_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        tz_name = "UTC"
    await update.message.reply_text(
        t(user_id, "current_time").format(tz=tz_name, time=time_str),
        parse_mode="HTML",
        reply_markup=main_keyboard(user_id),
    )

async def current_weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    loc = get_user_location(user_id)
    if not loc:
        await update.message.reply_text(t(user_id, "no_location"), reply_markup=main_keyboard(user_id))
        return
    data = await fetch_weather(*loc)
    if not data:
        await update.message.reply_text(t(user_id, "error"), reply_markup=main_keyboard(user_id))
        return
    lang = get_lang(user_id)
    cur = data["current"]
    tz = data.get("timezone", user_data[user_id].get("tz", "UTC"))
    desc = get_weather_desc(cur["weather_code"], lang)
    text = t(user_id, "weather_title").format(tz=tz) + "\n\n" + t(user_id, "weather_body").format(
        desc=desc,
        temp=cur["temperature_2m"],
        feels=cur["apparent_temperature"],
        hum=cur["relative_humidity_2m"],
        wind=cur["wind_speed_10m"],
    )
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=weather_keyboard(user_id))

async def week_forecast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    loc = get_user_location(user_id)
    if not loc:
        await update.message.reply_text(t(user_id, "no_location"), reply_markup=main_keyboard(user_id))
        return
    data = await fetch_weather(*loc)
    if not data:
        await update.message.reply_text(t(user_id, "error"), reply_markup=main_keyboard(user_id))
        return
    lang = get_lang(user_id)
    daily = data["daily"]
    tz = data.get("timezone", "")
    lines = [t(user_id, "week_title").format(tz=tz), ""]
    for i in range(min(7, len(daily["time"]))):
        date = daily["time"][i]
        code = daily["weather_code"][i]
        tmax = daily["temperature_2m_max"][i]
        tmin = daily["temperature_2m_min"][i]
        rain = daily["precipitation_probability_max"][i]
        desc = get_weather_desc(code, lang)
        lines.append(f"<b>{date}</b>: {desc}, {tmin}°…{tmax}°C, rain {rain}%")
    await update.message.reply_text("\n".join(lines), parse_mode="HTML", reply_markup=weather_keyboard(user_id))

async def hourly_forecast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    loc = get_user_location(user_id)
    if not loc:
        await update.message.reply_text(t(user_id, "no_location"), reply_markup=main_keyboard(user_id))
        return
    data = await fetch_weather(*loc)
    if not data:
        await update.message.reply_text(t(user_id, "error"), reply_markup=main_keyboard(user_id))
        return
    lang = get_lang(user_id)
    hourly = data["hourly"]
    lines = [t(user_id, "hourly_title"), ""]
    now = datetime.utcnow()
    count = 0
    for i, tstr in enumerate(hourly["time"]):
        if count >= 24:
            break
        try:
            dt = datetime.fromisoformat(tstr)
            if dt < now - timedelta(hours=1):
                continue
        except Exception:
            continue
        temp = hourly["temperature_2m"][i]
        rain = hourly["precipitation_probability"][i]
        code = hourly["weather_code"][i]
        desc = get_weather_desc(code, lang)
        lines.append(f"<b>{tstr[11:16]}</b>: {desc}, {temp}°C, rain {rain}%")
        count += 1
    await update.message.reply_text("\n".join(lines), parse_mode="HTML", reply_markup=weather_keyboard(user_id))

async def tomorrow_forecast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    loc = get_user_location(user_id)
    if not loc:
        await update.message.reply_text(t(user_id, "no_location"), reply_markup=main_keyboard(user_id))
        return
    data = await fetch_weather(*loc)
    if not data:
        await update.message.reply_text(t(user_id, "error"), reply_markup=main_keyboard(user_id))
        return
    lang = get_lang(user_id)
    daily = data["daily"]
    if len(daily["time"]) < 2:
        await update.message.reply_text(t(user_id, "error"), reply_markup=weather_keyboard(user_id))
        return
    i = 1
    date = daily["time"][i]
    code = daily["weather_code"][i]
    tmax = daily["temperature_2m_max"][i]
    tmin = daily["temperature_2m_min"][i]
    rain = daily["precipitation_probability_max"][i]
    desc = get_weather_desc(code, lang)
    text = (
        t(user_id, "tomorrow_title") + f"\n\n"
        f"<b>{date}</b>\n"
        f"{desc}\n"
        f"🌡 {tmin}° … {tmax}°C\n"
        f"🌧 Rain chance: {rain}%"
    )
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=weather_keyboard(user_id))

async def rain_forecast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    loc = get_user_location(user_id)
    if not loc:
        await update.message.reply_text(t(user_id, "no_location"), reply_markup=main_keyboard(user_id))
        return
    data = await fetch_weather(*loc)
    if not data:
        await update.message.reply_text(t(user_id, "error"), reply_markup=main_keyboard(user_id))
        return
    daily = data["daily"]
    rain = daily["precipitation_probability_max"][0]
    text = t(user_id, "rain_title") + f"\n\n🌧 Maximum chance: <b>{rain}%</b>"
    if rain >= 60:
        text += "\n⚠️ High chance of rain today!"
    elif rain >= 30:
        text += "\n🌦 Rain is possible."
    else:
        text += "\n☀️ Low chance of rain."
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=weather_keyboard(user_id))

async def air_quality(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    loc = get_user_location(user_id)
    if not loc:
        await update.message.reply_text(t(user_id, "no_location"), reply_markup=main_keyboard(user_id))
        return
    data = await fetch_air(*loc)
    if not data or "current" not in data:
        await update.message.reply_text(t(user_id, "error"), reply_markup=weather_keyboard(user_id))
        return
    cur = data["current"]
    aqi = cur.get("european_aqi", "N/A")
    pm25 = cur.get("pm2_5", "N/A")
    pm10 = cur.get("pm10", "N/A")
    text = (
        t(user_id, "air_title") + f"\n\n"
        f"European AQI: <b>{aqi}</b>\n"
        f"PM2.5: {pm25} µg/m³\n"
        f"PM10: {pm10} µg/m³"
    )
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=weather_keyboard(user_id))

async def uv_index(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    loc = get_user_location(user_id)
    if not loc:
        await update.message.reply_text(t(user_id, "no_location"), reply_markup=main_keyboard(user_id))
        return
    data = await fetch_weather(*loc)
    if not data:
        await update.message.reply_text(t(user_id, "error"), reply_markup=main_keyboard(user_id))
        return
    uv = data["daily"]["uv_index_max"][0]
    level = "Low"
    if uv >= 8:
        level = "Very High"
    elif uv >= 6:
        level = "High"
    elif uv >= 3:
        level = "Moderate"
    text = t(user_id, "uv_title") + f"\n\n☀️ Maximum UV index: <b>{uv}</b> ({level})"
    if uv >= 3:
        text += "\n🧴 Sun protection is recommended."
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=weather_keyboard(user_id))

async def sun_times(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    loc = get_user_location(user_id)
    if not loc:
        await update.message.reply_text(t(user_id, "no_location"), reply_markup=main_keyboard(user_id))
        return
    data = await fetch_weather(*loc)
    if not data:
        await update.message.reply_text(t(user_id, "error"), reply_markup=main_keyboard(user_id))
        return
    sunrise = data["daily"]["sunrise"][0][11:16]
    sunset = data["daily"]["sunset"][0][11:16]
    tz = data.get("timezone", "")
    text = t(user_id, "sun_title") + f"\n\n🌅 Sunrise: <b>{sunrise}</b>\n🌇 Sunset: <b>{sunset}</b>\nTimezone: {tz}"
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=weather_keyboard(user_id))

async def wind_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    loc = get_user_location(user_id)
    if not loc:
        await update.message.reply_text(t(user_id, "no_location"), reply_markup=main_keyboard(user_id))
        return
    data = await fetch_weather(*loc)
    if not data:
        await update.message.reply_text(t(user_id, "error"), reply_markup=main_keyboard(user_id))
        return
    cur = data["current"]
    daily = data["daily"]
    text = (
        t(user_id, "wind_title") + f"\n\n"
        f"Now: <b>{cur['wind_speed_10m']} km/h</b>\n"
        f"Today's max: {daily['wind_speed_10m_max'][0]} km/h\n"
        f"Dominant direction: {daily['wind_direction_10m_dominant'][0]}°"
    )
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=weather_keyboard(user_id))

async def alerts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    loc = get_user_location(user_id)
    if not loc:
        await update.message.reply_text(t(user_id, "no_location"), reply_markup=main_keyboard(user_id))
        return
    data = await fetch_weather(*loc)
    if not data:
        await update.message.reply_text(t(user_id, "error"), reply_markup=main_keyboard(user_id))
        return
    rain = data["daily"]["precipitation_probability_max"][0]
    code = data["daily"]["weather_code"][0]
    text = t(user_id, "alerts_title") + "\n\n"
    has_alert = False
    if rain >= 70:
        text += f"🌧 Heavy rain is possible ({rain}% chance).\n"
        has_alert = True
    if code in (95, 96, 99):
        text += "⛈ Thunderstorm possible.\n"
        has_alert = True
    if code in (71, 73, 75):
        text += "❄️ Snow expected.\n"
        has_alert = True
    if not has_alert:
        text += t(user_id, "no_alerts")
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=weather_keyboard(user_id))

async def dst_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    loc = get_user_location(user_id)
    if not loc:
        await update.message.reply_text(t(user_id, "no_location"), reply_markup=main_keyboard(user_id))
        return

    tz_name = user_data[user_id].get("tz", "UTC")
    try:
        tz = pytz.timezone(tz_name)
    except Exception:
        await update.message.reply_text(t(user_id, "error"), reply_markup=main_keyboard(user_id))
        return

    now = datetime.now(tz)
    # Look for next DST transition in the next ~2 years
    next_transition = None
    try:
        # pytz transition info
        transitions = getattr(tz, "_utc_transition_times", None)
        if transitions:
            for ut in transitions:
                if ut.tzinfo is None:
                    ut = pytz.UTC.localize(ut)
                local_ut = ut.astimezone(tz)
                if local_ut > now:
                    # Find the offset change
                    before = (local_ut - timedelta(hours=1)).astimezone(tz)
                    after = local_ut
                    old_offset = before.strftime("%z")
                    new_offset = after.strftime("%z")
                    old_str = f"{before.strftime('%H:%M')} (UTC{old_offset})"
                    new_str = f"{after.strftime('%H:%M')} (UTC{new_offset})"
                    direction = "➡️ Clocks go FORWARD (spring)" if after.utcoffset() > before.utcoffset() else "⬅️ Clocks go BACK (autumn)"
                    # Localize direction by language roughly
                    lang = get_lang(user_id)
                    if lang == "ru":
                        direction = "➡️ Часы переводят ВПЕРЁД (весна)" if after.utcoffset() > before.utcoffset() else "⬅️ Часы переводят НАЗАД (осень)"
                    elif lang == "uk":
                        direction = "➡️ Годинники переводять ВПЕРЕД (весна)" if after.utcoffset() > before.utcoffset() else "⬅️ Годинники переводять НАЗАД (осінь)"
                    next_transition = {
                        "date": local_ut.strftime("%A, %d %B %Y"),
                        "old": old_str,
                        "new": new_str,
                        "direction": direction,
                    }
                    break
    except Exception as e:
        logging.error(f"DST calculation error: {e}")

    if next_transition:
        text = t(user_id, "dst_title") + "\n\n" + t(user_id, "dst_next").format(
            tz=tz_name,
            date=next_transition["date"],
            old=next_transition["old"],
            new=next_transition["new"],
            direction=next_transition["direction"],
        )
    else:
        text = t(user_id, "dst_title") + "\n\n" + t(user_id, "dst_none").format(tz=tz_name)

    await update.message.reply_text(text, parse_mode="HTML", reply_markup=main_keyboard(user_id))

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    # Main menu buttons
    if text == t(user_id, "btn_change_loc"):
        await change_location(update, context)
    elif text == t(user_id, "btn_help"):
        await help_cmd(update, context)
    elif text == t(user_id, "btn_time"):
        await show_time(update, context)
    elif text == t(user_id, "btn_share"):
        await change_location(update, context)
    elif text == t(user_id, "btn_weather"):
        await update.message.reply_text("🌤", reply_markup=weather_keyboard(user_id))
    elif text == t(user_id, "btn_dst"):
        await dst_info(update, context)
    elif text == t(user_id, "btn_back"):
        await update.message.reply_text("🏠", reply_markup=main_keyboard(user_id))
    # Weather buttons
    elif text == t(user_id, "btn_current"):
        await current_weather(update, context)
    elif text == t(user_id, "btn_week"):
        await week_forecast(update, context)
    elif text == t(user_id, "btn_hourly"):
        await hourly_forecast(update, context)
    elif text == t(user_id, "btn_tomorrow"):
        await tomorrow_forecast(update, context)
    elif text == t(user_id, "btn_rain"):
        await rain_forecast(update, context)
    elif text == t(user_id, "btn_air"):
        await air_quality(update, context)
    elif text == t(user_id, "btn_uv"):
        await uv_index(update, context)
    elif text == t(user_id, "btn_sun"):
        await sun_times(update, context)
    elif text == t(user_id, "btn_wind"):
        await wind_info(update, context)
    elif text == t(user_id, "btn_alerts"):
        await alerts(update, context)
    else:
        await update.message.reply_text(t(user_id, "help"), parse_mode="HTML", reply_markup=main_keyboard(user_id))

def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("language", language_cmd))
    app.add_handler(CommandHandler("watch", show_time))
    app.add_handler(CommandHandler("weather", current_weather))
    app.add_handler(CommandHandler("wether", current_weather))  # typo support
    app.add_handler(CommandHandler("week", week_forecast))
    app.add_handler(CommandHandler("weekwether", week_forecast))
    app.add_handler(CommandHandler("hourly", hourly_forecast))
    app.add_handler(CommandHandler("tomorrow", tomorrow_forecast))
    app.add_handler(CommandHandler("rain", rain_forecast))
    app.add_handler(CommandHandler("air", air_quality))
    app.add_handler(CommandHandler("uv", uv_index))
    app.add_handler(CommandHandler("sun", sun_times))
    app.add_handler(CommandHandler("wind", wind_info))
    app.add_handler(CommandHandler("alerts", alerts))
    app.add_handler(CommandHandler("dst", dst_info))
    app.add_handler(CommandHandler("change_location", change_location))

    app.add_handler(CallbackQueryHandler(lang_callback, pattern="^lang_"))
    app.add_handler(MessageHandler(filters.LOCATION, location_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    # For Render: use webhook if RENDER_EXTERNAL_URL is set, otherwise polling
    render_url = os.environ.get("RENDER_EXTERNAL_URL")
    if render_url:
        port = int(os.environ.get("PORT", 10000))
        app.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path=TOKEN,
            webhook_url=f"{render_url}/{TOKEN}",
        )
    else:
        app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
