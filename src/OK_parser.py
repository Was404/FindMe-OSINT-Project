from rich.console import Console
import requests
from datetime import datetime
import json
import time
import unicodedata
import re
import sys
import os
import hashlib
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import TOKEN_OK, APPLICATION_KEY_OK, APPLICATION_SECRET_KEY_OK, KEYWORDS

console = Console()

def contains_cyrillic(text):
    """Проверяет, содержит ли текст кириллические символы."""
    for char in text:
        try:
            if 'CYRILLIC' in unicodedata.name(char).upper():
                return True
        except ValueError:
            continue
    return False

def sanitize_name(name):
    """Санитизирует имя для использования в качестве имени папки."""
    return re.sub(r'[^\w\-]', '_', name)

def calculate_signature(params, access_token, application_secret_key):
    """Вычисляет подпись для запроса к API Одноклассников."""
    sorted_params = sorted(params.items())
    params_str = ''.join([f"{k}={v}" for k, v in sorted_params])
    token_secret_md5 = hashlib.md5((access_token + application_secret_key).encode()).hexdigest()
    sig = hashlib.md5((params_str + token_secret_md5).encode()).hexdigest()
    return sig

def ok_api_request(method, params, access_token, application_key, application_secret_key):
    """Выполняет запрос к API Одноклассников с подписью."""
    base_url = "https://api.ok.ru/fb.do"
    params['application_key'] = application_key
    params['method'] = method
    params['format'] = 'json'
    params['access_token'] = access_token
    sig = calculate_signature(params, access_token, application_secret_key)
    params['sig'] = sig
    response = requests.get(base_url, params=params)
    return response.json()

def resolve_ok_screen_name(screen_name, access_token, application_key, application_secret_key):
    """Разрешает screen_name в user_id."""
    method = "users.getInfo"
    params = {"uids": screen_name}
    response = ok_api_request(method, params, access_token, application_key, application_secret_key)
    if 'error_code' in response:
        console.print(f"[red]Ошибка разрешения screen_name: {response['error_msg']}[/red]")
        return None
    else:
        if response and isinstance(response, list) and len(response) > 0:
            user_info = response[0]
            return user_info['uid']
        else:
            return None

def get_ok_profile_info(user_id, access_token, application_key, application_secret_key):
    """Получает информацию о профиле пользователя."""
    method = "users.getInfo"
    fields = "first_name,last_name,gender,birthday,location.city,location.country,pic_1,education,status,interests,friendsCount"
    params = {"uids": user_id, "fields": fields}
    response = ok_api_request(method, params, access_token, application_key, application_secret_key)
    if 'error_code' in response:
        console.print(f"[red]Ошибка получения информации о профиле: {response['error_msg']}[/red]")
        return None
    else:
        return response[0] if response else None

def get_ok_friends_cities(user_id, access_token, application_key, application_secret_key):
    """Получает города друзей пользователя и вычисляет вероятности."""
    method = "friends.get"
    params = {"uid": user_id}
    response = ok_api_request(method, params, access_token, application_key, application_secret_key)
    if 'error_code' in response:
        console.print(f"[red]Ошибка получения друзей: {response['error_msg']}[/red]")
        return {}
    friends_ids = response
    cities = []
    for i in range(0, len(friends_ids), 100):
        batch_ids = friends_ids[i:i+100]
        method = "users.getInfo"
        params = {"uids": ",".join(batch_ids), "fields": "location.city"}
        batch_response = ok_api_request(method, params, access_token, application_key, application_secret_key)
        if 'error_code' in batch_response:
            continue
        for user in batch_response:
            if 'location' in user and 'city' in user['location']:
                cities.append(user['location']['city'])
    city_counts = {}
    for city in cities:
        city_counts[city] = city_counts.get(city, 0) + 1
    total_friends_with_city = len(cities)
    if total_friends_with_city > 0:
        city_probabilities = {city: count / total_friends_with_city for city, count in city_counts.items()}
        return city_probabilities
    else:
        return {}

def find_ok_group_for_university(university_name, access_token, application_key, application_secret_key):
    """Находит сообщество Одноклассников, связанное с университетом."""
    method = "group.search"
    params = {"q": university_name, "types": "GROUP"}
    response = ok_api_request(method, params, access_token, application_key, application_secret_key)
    if 'error_code' in response:
        console.print(f"[red]Ошибка поиска группы для университета: {response['error_msg']}[/red]")
        return None
    groups = response.get('groups', [])
    if groups:
        top_group = max(groups, key=lambda x: x.get('stats', {}).get('membersCount', 0))
        return top_group
    return None

def get_ok_posts_with_keywords(group_id, access_token, application_key, application_secret_key):
    """Получает посты из сообщества и фильтрует по ключевым словам."""
    method = "mediatopic.get"
    params = {"gid": group_id, "count": 100}
    response = ok_api_request(method, params, access_token, application_key, application_secret_key)
    if 'error_code' in response:
        console.print(f"[red]Ошибка получения постов из группы: {response['error_msg']}[/red]")
        return []
    posts = response.get('mediatopics', [])
    filtered_posts = [post for post in posts if any(keyword.lower() in post.get('text', '').lower() for keyword in KEYWORDS)]
    return filtered_posts

def calculate_ok_fake_probability(profile):
    """Вычисляет вероятность того, что профиль является фейком."""
    fake_score = 0.0
    if 'friendsCount' in profile:
        friends_count = profile['friendsCount']
        if friends_count < 10 or friends_count > 150:
            fake_score += 0.5
    if 'pic_1' not in profile or not profile['pic_1']:
        fake_score += 0.3
    if 'status' not in profile or not profile['status']:
        fake_score += 0.2
    return min(fake_score, 1.0)

def get_ok_user_data(user_id, access_token, application_key, application_secret_key):
    """Собирает всю информацию о пользователе."""
    profile = get_ok_profile_info(user_id, access_token, application_key, application_secret_key)
    if not profile:
        return None

    city = profile.get('location', {}).get('city', 'Не указан')
    if city == 'Не указан':
        city_probabilities = get_ok_friends_cities(user_id, access_token, application_key, application_secret_key)
        if city_probabilities:
            console.print("[yellow]Город не указан. Вероятности по городам друзей:[/yellow]")
            for city_name, prob in city_probabilities.items():
                console.print(f"[yellow]{city_name}: {prob:.2f}[/yellow]")
        else:
            console.print("[yellow]Город не указан, и нет данных о городах друзей.[/yellow]")
    else:
        console.print(f"[green]Город: {city}[/green]")

    education = profile.get('education', [])
    universities_data = []
    for edu in education:
        uni_name = edu.get('name', '')
        group = find_ok_group_for_university(uni_name, access_token, application_key, application_secret_key)
        if group:
            group_id = group['uid']
            posts_with_keywords = get_ok_posts_with_keywords(group_id, access_token, application_key, application_secret_key)
            universities_data.append({
                'name': uni_name,
                'group': {
                    'id': group_id,
                    'name': group['name']
                },
                'posts_with_keywords': posts_with_keywords
            })
        else:
            universities_data.append({
                'name': uni_name,
                'group': None,
                'posts_with_keywords': []
            })
        time.sleep(0.4)

    method = "mediatopic.get"
    params = {"fid": user_id, "count": 100}
    posts_response = ok_api_request(method, params, access_token, application_key, application_secret_key)
    if 'error_code' in posts_response:
        console.print(f"[red]Ошибка получения постов пользователя: {posts_response['error_msg']}[/red]")
        posts = []
    else:
        posts = posts_response.get('mediatopics', [])

    liked_posts = []  # Заглушка, так как OK API не предоставляет метод для получения лайкнутых постов

    fake_probability = calculate_ok_fake_probability(profile)

    user_data = {
        'user_id': user_id,
        'profile': profile,
        'posts': posts,
        'liked_posts': liked_posts,
        'universities': universities_data,
        'fake_probability': fake_probability,
        'city': city if city != 'Не указан' else city_probabilities,
        'note': "Посты, которые пользователь лайкнул или прокомментировал, не могут быть получены из-за ограничений OK API."
    }
    return user_data

def download_profile_picture(url, filename):
    """Скачивает изображение профиля по URL и сохраняет в указанный файл."""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
        return True
    except Exception as e:
        console.print(f"[red]Ошибка скачивания фотографии профиля: {e}[/red]")
        return False

def run():
    """Основная функция модуля для извлечения данных из профилей Одноклассников."""
    console.print(f"\n[bold cyan]:: OK.RU OSINT SCRAPER MODULE[/bold cyan]")
    console.print("[yellow]Примечание: screen_name в Одноклассниках должны быть на латинице, например, 'dmitry.utkin'.[/yellow]")
    screen_names_input = input("Введите OK screen_names через запятую: ").strip()
    screen_names = [name.strip() for name in screen_names_input.split(',')]

    for name in screen_names:
        if contains_cyrillic(name):
            console.print(f"[yellow]Предупреждение: '{name}' содержит кириллические символы. OK screen_names должны быть на латинице.[/yellow]")

    timestamp = datetime.now().strftime("%Y%m%d%H%M")
    access_token = TOKEN_OK
    application_key = APPLICATION_KEY_OK
    application_secret_key = APPLICATION_SECRET_KEY_OK

    for screen_name in screen_names:
        console.print(f"[cyan]→ Обработка профиля: https://ok.ru/{screen_name}[/cyan]")
        user_id = resolve_ok_screen_name(screen_name, access_token, application_key, application_secret_key)
        if user_id:
            user_data = get_ok_user_data(user_id, access_token, application_key, application_secret_key)
            if user_data:
                profile = user_data['profile']
                user_name = f"{profile['first_name']}_{profile['last_name']}" if 'first_name' in profile and 'last_name' in profile else str(user_id)
                folder_name = sanitize_name(user_name)
                os.makedirs(os.path.join('logs', folder_name), exist_ok=True)

                photo_url = profile.get('pic_1')
                if photo_url:
                    image_filename = os.path.join('logs', folder_name, 'profile_picture.jpg')
                    if download_profile_picture(photo_url, image_filename):
                        console.print(f"[green]✔ Профильная картинка сохранена в {image_filename}[/green]")
                else:
                    console.print("[yellow]Профильная картинка не найдена[/yellow]")

                for post in user_data.get('posts', []):
                    post_id = post['id']
                    post_filename = os.path.join('logs', f"{user_id}_{post_id}.json")
                    with open(post_filename, 'w', encoding='utf-8') as f:
                        json.dump(post, f, indent=4, ensure_ascii=False)
                    console.print(f"[green]Пост {post_id} сохранён в {post_filename}[/green]")

                data_filename = f"logs/ok_user_data_{user_id}_{timestamp}.json"
                with open(data_filename, "w", encoding="utf-8") as f:
                    json.dump(user_data, f, indent=4, ensure_ascii=False)
                console.print(f"[green]Данные сохранены в {data_filename}[/green]")
            else:
                console.print(f"[red]Не удалось получить данные для {screen_name}[/red]")
        else:
            console.print(f"[red]Не удалось разрешить screen_name: {screen_name}[/red]")
        time.sleep(0.4)

    console.print(f"[bold green]✓ Все профили обработаны[/bold green]")

if __name__ == "__main__":
    run()