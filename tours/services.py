import requests
from django.core.cache import cache

STATUS_MAP = {
    'visa free': 'Віза не потрібна',
    'visa on arrival': 'Віза після прибуття (VoA)',
    'visa on arrival (including eta)': 'Віза після прибуття (або eTA)',
    'visa required': 'Потрібна віза',
    'e-visa': 'Електронна віза (e-Visa)',
}

def get_visa_requirement(passport_iso2, destination_iso2):
    if not passport_iso2 or not destination_iso2:
        return None

    passport_iso2 = passport_iso2.upper()
    destination_iso2 = destination_iso2.upper()

    cache_key = f"visa_req_{passport_iso2}_{destination_iso2}"
    cached_res = cache.get(cache_key)
    if cached_res:
        return cached_res

    url = f"https://rough-sun-2523.fly.dev/visa/{passport_iso2}/{destination_iso2}"

    try:
        response = requests.get(url, timeout=4)
        if response.status_code == 200:
            data = response.json()

            category_code = data.get('category', {}).get('code', 'VR')
            raw_name = data.get('category', {}).get('name', '')
            category_name_clean = raw_name.lower().strip()
            
            translated_status = STATUS_MAP.get(category_name_clean, raw_name or 'Потрібна віза')
            duration = data.get('dur')

            result = {
                'status_code': category_code,
                'status_name': raw_name,
                'status': translated_status,
                'duration_days': duration,
                'is_free': category_code in ['VF', 'VOA'],
            }

            cache.set(cache_key, result, 86400)
            return result

    except (requests.RequestException, ValueError):
        pass

    return None