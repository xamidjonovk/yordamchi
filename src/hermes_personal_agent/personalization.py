"""Validated owner preferences shared by web, text tasks and voice prompts."""
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from .voice_common import CONFIG, save_config

FIELDS = {'owner_name': 80, 'language': 12, 'timezone': 80, 'owner_style': 2000,
          'introduction': 300, 'personal_context': 6000, 'hermes_model': 120}

def profile():
    return {key: CONFIG.get(key, '') for key in FIELDS}

def introduction():
    return CONFIG.get('introduction') or f"Men {CONFIG['owner_name']}ning shaxsiy AI yordamchisiman."

def context():
    return (f"Owner: {CONFIG['owner_name']}. Language: {CONFIG['language']}. "
            f"Introduce yourself as: {introduction()} Always be honest that you are AI. "
            f"Communication preferences: {CONFIG.get('owner_style', '')}\n"
            f"Owner-provided background and goals: {CONFIG.get('personal_context', '')}\n")

def update(values):
    if not isinstance(values, dict) or set(values) - FIELDS.keys():
        raise ValueError('Noma’lum profil maydoni')
    for key, value in values.items():
        if not isinstance(value, str) or len(value) > FIELDS[key] or '\x00' in value:
            raise ValueError(f'{key}: matn uzunligi yoki qiymatini tekshiring')
        if key in {'owner_name', 'language', 'timezone', 'hermes_model'} and not value.strip():
            raise ValueError(f'{key}: bo‘sh qoldirmang')
    if 'timezone' in values:
        try: ZoneInfo(values['timezone'])
        except (ZoneInfoNotFoundError, ValueError): raise ValueError('Vaqt zonasi noto‘g‘ri, masalan Asia/Tashkent') from None
    save_config({k:v.strip() for k,v in values.items()})
    return profile()
