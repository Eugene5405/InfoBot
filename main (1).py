import os
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

import httpx
import pytz
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
    "sr": {"name": "Srpski", "flag": "🇷🇸"},
    "be": {"name": "Беларуская", "flag": "🇧🇾"},
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
    "sr": {
        "choose_lang": "🌐 <b>Molimo izaberite jezik:</b>",
        "welcome": (
            "👋 <b>Zdravo! Dobrodošli u bot Vreme i Prognoza!</b>\n\n"
            "🌍 Prikazujem trenutno vreme i vreme za sačuvanu lokaciju.\n"
            "Takođe možete proveriti prognoze, kišu, kvalitet vazduha, UV indeks, "
            "izlazak i zalazak sunca, vetar i upozorenja.\n\n"
            "📍 Prvo podelite svoju lokaciju dugmetom ispod "
            "ili pošaljite tačku na mapi.\n\n"
            "Nakon toga koristite meni ili komande."
        ),
        "welcome_ready": (
            "👋 <b>Zdravo! Dobrodošli u bot Vreme i Prognoza!</b>\n\n"
            "🌍 Prikazujem trenutno vreme i vreme za sačuvanu lokaciju.\n"
            "Takođe možete proveriti prognoze, kišu, kvalitet vazduha, UV indeks, "
            "izlazak i zalazak sunca, vetar i upozorenja.\n\n"
            "✅ Vaša lokacija je već sačuvana.\n"
            "Koristite meni ispod ili pošaljite komandu."
        ),
        "help": (
            "📋 <b>Dostupne komande:</b>\n\n"
            "/watch — trenutno vreme\n"
            "/weather — trenutna prognoza\n"
            "/week — prognoza za 7 dana\n"
            "/hourly — narednih 24 sata\n"
            "/tomorrow — prognoza za sutra\n"
            "/rain — verovatnoća kiše\n"
            "/air — kvalitet vazduha\n"
            "/uv — UV indeks\n"
            "/sun — izlazak i zalazak sunca\n"
            "/wind — vetar\n"
            "/alerts — upozorenja\n"
            "/dst — sledeća promena sata\n"
            "/change_location — promeni lokaciju\n"
            "/language — promeni jezik\n"
            "/help — prikaži ovu listu\n\n"
            "Ili jednostavno koristite dugmad ispod 👇"
        ),
        "btn_change_loc": "📍 Promeni lokaciju",
        "btn_help": "❓ Pomoć",
        "btn_time": "🕐 Prikaži vreme",
        "btn_share": "📌 Podeli lokaciju",
        "btn_weather": "🌤 Komande vremena",
        "btn_back": "⬅️ Nazad u meni",
        "btn_current": "🌡 Trenutno vreme",
        "btn_week": "📅 Prognoza 7 dana",
        "btn_hourly": "⏱ Po satu",
        "btn_tomorrow": "📆 Sutra",
        "btn_rain": "🌧 Prognoza kiše",
        "btn_air": "🌬 Kvalitet vazduha",
        "btn_uv": "☀️ UV indeks",
        "btn_sun": "🌅 Izlazak i zalazak",
        "btn_wind": "💨 Vetar",
        "btn_alerts": "⚠️ Upozorenja",
        "ask_location": "📍 Molimo podelite lokaciju dugmetom ispod:",
        "location_saved": "✅ Lokacija sačuvana! Koristiću je za vreme i prognozu.",
        "no_location": "❌ Još niste podelili lokaciju.\nPritisnite dugme «Podeli lokaciju».",
        "current_time": "🕐 <b>Trenutno vreme u {tz}:</b>\n{time}",
        "weather_title": "🌤 <b>Vreme na vašoj lokaciji:</b>\nVremenska zona: {tz}",
        "weather_body": (
            "{desc}\n"
            "🌡 Temperatura: {temp}°C\n"
            "🤒 Oseća se kao: {feels}°C\n"
            "💧 Vlažnost: {hum}%\n"
            "💨 Vetar: {wind} km/h"
        ),
        "week_title": "📅 <b>Prognoza za 7 dana:</b>\nVremenska zona: {tz}",
        "hourly_title": "⏱ <b>Prognoza po satu (24h):</b>",
        "tomorrow_title": "📆 <b>Sutra na vašoj lokaciji:</b>",
        "rain_title": "🌧 <b>Prognoza kiše za danas:</b>",
        "air_title": "🌬 <b>Kvalitet vazduha:</b>",
        "uv_title": "☀️ <b>UV indeks za danas:</b>",
        "sun_title": "🌅 <b>Izlazak i zalazak sunca:</b>",
        "wind_title": "💨 <b>Vetar:</b>",
        "alerts_title": "⚠️ <b>Upozorenja o vremenu:</b>",
        "no_alerts": "✅ Nema značajnih upozorenja za danas.",
        "dst_title": "🕒 <b>Promena sata (letnje/zimsko vreme)</b>",
        "dst_next": "Sledeća promena sata u <b>{tz}</b>:\n📅 <b>{date}</b>\n⏰ Sa {old} → {new}\n\n{direction}",
        "dst_none": "✅ U naredne 2 godine nema promene sata za {tz}.\nOva vremenska zona možda ne koristi letnje vreme.",
        "btn_dst": "🕒 Promena sata",
        "error": "❌ Nešto je pošlo po zlu. Pokušajte kasnije.",
        "lang_changed": "✅ Jezik promenjen!",
    },
    "be": {
        "choose_lang": "🌐 <b>Калі ласка, абярыце мову:</b>",
        "welcome": (
            "👋 <b>Прывітанне! Сардэчна запрашаем у бот Час і Надвор'е!</b>\n\n"
            "🌍 Я паказваю бягучы час і надвор'е для захаванай лакацыі.\n"
            "Таксама можна глядзець прагнозы, дождж, якасць паветра, УФ-індэкс, "
            "усход і захад сонца, вецер і папярэджанні.\n\n"
            "📍 Спачатку падзяліцеся сваёй геалакацыяй кнопкай ніжэй "
            "або дашліце кропку на карце.\n\n"
            "Пасля гэтага выкарыстоўвайце меню або каманды."
        ),
        "welcome_ready": (
            "👋 <b>Прывітанне! Сардэчна запрашаем у бот Час і Надвор'е!</b>\n\n"
            "🌍 Я паказваю бягучы час і надвор'е для захаванай лакацыі.\n"
            "Таксама можна глядзець прагнозы, дождж, якасць паветра, УФ-індэкс, "
            "усход і захад сонца, вецер і папярэджанні.\n\n"
            "✅ Ваша лакацыя ўжо захавана.\n"
            "Выкарыстоўвайце меню ніжэй або дашліце каманду."
        ),
        "help": (
            "📋 <b>Даступныя каманды:</b>\n\n"
            "/watch — бягучы час\n"
            "/weather — бягучае надвор'е\n"
            "/week — прагноз на 7 дзён\n"
            "/hourly — бліжэйшыя 24 гадзіны\n"
            "/tomorrow — прагноз на заўтра\n"
            "/rain — імавернасць дажджу\n"
            "/air — якасць паветра\n"
            "/uv — УФ-індэкс\n"
            "/sun — усход і захад\n"
            "/wind — вецер\n"
            "/alerts — папярэджанні\n"
            "/dst — наступны перавод гадзін\n"
            "/change_location — змяніць лакацыю\n"
            "/language — змяніць мову\n"
            "/help — паказаць гэты спіс\n\n"
            "Або проста выкарыстоўвайце кнопкі ніжэй 👇"
        ),
        "btn_change_loc": "📍 Змяніць лакацыю",
        "btn_help": "❓ Дапамога",
        "btn_time": "🕐 Паказаць час",
        "btn_share": "📌 Падзяліцца лакацыяй",
        "btn_weather": "🌤 Каманды надвор'я",
        "btn_back": "⬅️ Назад у меню",
        "btn_current": "🌡 Бягучае надвор'е",
        "btn_week": "📅 Прагноз на 7 дзён",
        "btn_hourly": "⏱ Па гадзінах",
        "btn_tomorrow": "📆 Заўтра",
        "btn_rain": "🌧 Прагноз дажджу",
        "btn_air": "🌬 Якасць паветра",
        "btn_uv": "☀️ УФ-індэкс",
        "btn_sun": "🌅 Усход і захад",
        "btn_wind": "💨 Вецер",
        "btn_alerts": "⚠️ Папярэджанні",
        "ask_location": "📍 Калі ласка, падзяліцеся лакацыяй кнопкай ніжэй:",
        "location_saved": "✅ Лакацыя захавана! Цяпер я буду выкарыстоўваць яе для часу і надвор'я.",
        "no_location": "❌ Вы яшчэ не ўказалі лакацыю.\nНацісніце кнопку «Падзяліцца лакацыяй».",
        "current_time": "🕐 <b>Бягучы час у {tz}:</b>\n{time}",
        "weather_title": "🌤 <b>Надвор'е ў вашай лакацыі:</b>\nЧасавы пояс: {tz}",
        "weather_body": (
            "{desc}\n"
            "🌡 Тэмпература: {temp}°C\n"
            "🤒 Адчуваецца як: {feels}°C\n"
            "💧 Вільготнасць: {hum}%\n"
            "💨 Вецер: {wind} км/г"
        ),
        "week_title": "📅 <b>Прагноз на 7 дзён:</b>\nЧасавы пояс: {tz}",
        "hourly_title": "⏱ <b>Прагноз па гадзінах (24г):</b>",
        "tomorrow_title": "📆 <b>Заўтра ў вашай лакацыі:</b>",
        "rain_title": "🌧 <b>Прагноз дажджу на сёння:</b>",
        "air_title": "🌬 <b>Якасць паветра:</b>",
        "uv_title": "☀️ <b>УФ-індэкс на сёння:</b>",
        "sun_title": "🌅 <b>Усход і захад:</b>",
        "wind_title": "💨 <b>Вецер:</b>",
        "alerts_title": "⚠️ <b>Папярэджанні аб надвор'і:</b>",
        "no_alerts": "✅ Значымых папярэджанняў на сёння няма.",
        "dst_title": "🕒 <b>Перавод гадзін (летні/зімовы час)</b>",
        "dst_next": "Наступны перавод гадзін у <b>{tz}</b>:\n📅 <b>{date}</b>\n⏰ З {old} → {new}\n\n{direction}",
        "dst_none": "✅ У бліжэйшыя 2 гады пераводу гадзін у {tz} не будзе.\nУ гэтым часавым поясе летні час можа не выкарыстоўвацца.",
        "btn_dst": "🕒 Перавод гадзін",
        "error": "❌ Нешта пайшло не так. Паспрабуйце пазней.",
        "lang_changed": "✅ Мова зменена!",
    },
}
