# InfoBot — Time & Weather Telegram Bot

Multi-language Time & Weather bot with 10 languages.

## Features

- 10 languages with flag selection on `/start`
- Beautiful welcome message in chosen language
- Current time, weather, 7-day & hourly forecast
- Rain, air quality, UV index, sunrise/sunset, wind, alerts
- Location sharing
- Full emoji support
- Ready for Render.com

## Languages

English, Русский, Українська, Español, Deutsch, Français, Português, Türkçe, العربية, 中文

## Setup

1. Create a bot with [@BotFather](https://t.me/BotFather) and get the token
2. Put the token in environment variable `BOT_TOKEN`
3. Deploy to Render (Web Service)

### Render settings

- **Runtime**: Python 3
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python main.py`
- **Environment Variable**: `BOT_TOKEN` = your bot token

The bot automatically uses webhook when `RENDER_EXTERNAL_URL` is present (Render provides it).

## Local run

```bash
export BOT_TOKEN=your_token_here
python main.py
```

## Commands

- `/start` — choose language + welcome
- `/language` — change language
- `/watch` — current time
- `/weather` — current weather
- `/week` — 7-day forecast
- `/hourly` — next 24 hours
- `/tomorrow` — tomorrow
- `/rain` — rain probability
- `/air` — air quality
- `/uv` — UV index
- `/sun` — sunrise & sunset
- `/wind` — wind
- `/alerts` — weather alerts
- `/change_location` — new location
- `/help` — help
