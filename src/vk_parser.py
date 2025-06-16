from rich.console import Console
import requests
from vk_api import VkApi
import os
from datetime import datetime
import json
import time
import unicodedata
import re
from config import TOKEN_VK, KEYWORDS
from vk_registration_checker import get_registration_date, calculate_fake_probability

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

def get_vk_api():
    """Инициализирует VK API с использованием токена."""
    try:
        vk_session = VkApi(token=TOKEN_VK)
        return vk_session.get_api()
    except Exception as e:
        console.print(f"[red]Ошибка инициализации VK API: {e}[/red]")
        return None

def resolve_screen_name(vk, screen_name):
    """Разрешает screen_name в object_id и тип (user или group)."""
    try:
        response = vk.utils.resolveScreenName(screen_name=screen_name)
        if 'object_id' in response:
            return response['object_id'], response['type']
        else:
            return None, None
    except Exception as e:
        console.print(f"[red]Ошибка разрешения screen_name: {e}[/red]")
        return None, None

def get_profile_info(vk, user_id):
    """Получает информацию о профиле пользователя с указанными полями."""
    fields = "first_name,last_name,sex,bdate,city,country,home_town,photo_max_orig,domain,education,status,followers_count,occupation,relatives,relation,personal,friends"
    try:
        response = vk.users.get(user_ids=user_id, fields=fields)
        if response:
            return response[0]
    except Exception as e:
        console.print(f"[red]Ошибка получения информации о профиле: {e}[/red]")
        return None

def get_friends_cities(vk, user_id):
    """Получает города друзей пользователя и вычисляет вероятности."""
    try:
        friends = vk.friends.get(user_id=user_id, fields='city')
        cities = [friend['city']['title'] for friend in friends['items'] if 'city' in friend]
        city_counts = {}
        for city in cities:
            city_counts[city] = city_counts.get(city, 0) + 1
        total_friends_with_city = len(cities)
        if total_friends_with_city > 0:
            city_probabilities = {city: count / total_friends_with_city for city, count in city_counts.items()}
            return city_probabilities
        else:
            return {}
    except Exception as e:
        console.print(f"[red]Ошибка получения городов друзей: {e}[/red]")
        return {}

def find_group_for_university(vk, university_name):
    """Находит сообщество VK, связанное с университетом."""
    try:
        groups = vk.groups.search(q=university_name, type=2, count=10, fields='members_count')
        if groups['items']:
            top_group = max(groups['items'], key=lambda x: x.get('members_count', 0))
            return top_group
    except Exception as e:
        console.print(f"[red]Ошибка поиска группы для университета: {e}[/red]")
    return None

def get_posts_with_keywords(vk, group_id):
    """Получает посты из сообщества и фильтрует по ключевым словам."""
    try:
        posts = vk.wall.get(owner_id=-group_id, count=100, filter='owner')
        filtered_posts = [post for post in posts['items'] if any(keyword.lower() in post.get('text', '').lower() for keyword in KEYWORDS)]
        return filtered_posts
    except Exception as e:
        console.print(f"[red]Ошибка получения постов из группы: {e}[/red]")
        return []

def get_liked_posts(vk, user_id):
    """Получает список постов, которые пользователь лайкнул."""
    try:
        liked_posts = vk.likes.getList(type='post', count=1000)
        return liked_posts['items']
    except Exception as e:
        console.print(f"[red]Ошибка получения лайкнутых постов: {e}[/red]")
        return []

def calculate_combined_fake_probability(profile, registration_date):
    """
    Вычисляет вероятность того, что профиль является фейком на основе доступных данных и даты регистрации.
    """
    fake_score = 0.0
    # Проверка количества друзей
    if 'friends' in profile and profile['friends']['count'] < 10:
        fake_score += 0.5
    # Проверка фото профиля
    if 'photo_max_orig' not in profile or profile['photo_max_orig'] == 'https://vk.com/images/camera_200.png':
        fake_score += 0.3
    # Проверка статуса
    if 'status' not in profile or not profile['status']:
        fake_score += 0.2
    # Проверка даты регистрации
    reg_fake_score = calculate_fake_probability(registration_date)
    fake_score += reg_fake_score

    return min(fake_score, 1.0)

def get_user_data(vk, user_id):
    """Собирает всю информацию о пользователе, включая вероятность фейка и предсказание города."""
    profile = get_profile_info(vk, user_id)
    if not profile:
        return None

    # 1. Получение даты регистрации
    registration_date = get_registration_date(str(user_id))
    if registration_date:
        console.print(f"[green]Дата регистрации: {registration_date.strftime('%d.%m.%Y')}[/green]")
    else:
        console.print("[yellow]Не удалось определить дату регистрации[/yellow]")

    # 2. Определяем вероятность фейка
    fake_probability = calculate_combined_fake_probability(profile, registration_date)
    console.print(f"[yellow]Вероятность фейкового профиля: {fake_probability:.2f}[/yellow]")

    # 3. Проверяем город и предсказываем, если не указан
    city = profile.get('city', {}).get('title', 'Не указан')
    if city == 'Не указан':
        city_probabilities = get_friends_cities(vk, user_id)
        if city_probabilities:
            console.print("[yellow]Город не указан. Вероятности по городам друзей:[/yellow]")
            for city_name, prob in city_probabilities.items():
                console.print(f"[yellow]{city_name}: {prob:.2f}[/yellow]")
        else:
            console.print("[yellow]Город не указан, и нет данных о городах друзей.[/yellow]")
    else:
        console.print(f"[green]Город: {city}[/green]")

    # Обработка университетов
    universities = profile.get('education', []) if isinstance(profile.get('education'), list) else []
    universities_data = []
    for uni in universities:
        uni_name = uni.get('name', '')
        group = find_group_for_university(vk, uni_name)
        if group:
            group_id = group['id']
            posts_with_keywords = get_posts_with_keywords(vk, group_id)
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
        time.sleep(0.4)  # Задержка для соблюдения лимитов API

    liked_posts = get_liked_posts(vk, user_id)

    # Получение постов пользователя
    try:
        posts_response = vk.wall.get(owner_id=user_id, count=100, filter='owner')
        posts = posts_response['items']
    except Exception as e:
        console.print(f"[red]Ошибка получения постов пользователя: {e}[/red]")
        posts = []

    user_data = {
        'user_id': user_id,
        'profile': profile,
        'posts': posts,
        'liked_posts': liked_posts,
        'universities': universities_data,
        'fake_probability': fake_probability,
        'city': city if city != 'Не указан' else city_probabilities,
        'registration_date': registration_date.strftime('%d.%m.%Y') if registration_date else None,
        'note': "Посты, которые пользователь прокомментировал, не могут быть получены из-за ограничений VK API."
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
    """Основная функция модуля для извлечения данных из VK-профилей."""
    console.print(f"\n[bold cyan]:: VK OSINT SCRAPER MODULE[/bold cyan]")
    console.print("[yellow]Примечание: screen_name в VK должны быть на латинице, например, 'durov' вместо 'Дуров'.[/yellow]")
    screen_names_input = input("Введите VK screen_names через запятую: ").strip()
    screen_names = [name.strip() for name in screen_names_input.split(',')]

    for name in screen_names:
        if contains_cyrillic(name):
            console.print(f"[yellow]Предупреждение: '{name}' содержит кириллические символы. VK screen_names должны быть на латинице.[/yellow]")

    timestamp = datetime.now().strftime("%Y%m%d%H%M")
    vk = get_vk_api()
    if vk is None:
        return

    for screen_name in screen_names:
        console.print(f"[cyan]→ Обработка профиля: https://vk.com/{screen_name}[/cyan]")
        user_id, obj_type = resolve_screen_name(vk, screen_name)
        if user_id and obj_type == 'user':
            user_data = get_user_data(vk, user_id)
            if user_data:
                profile = user_data['profile']
                user_name = f"{profile['first_name']}_{profile['last_name']}" if 'first_name' in profile and 'last_name' in profile else str(user_id)
                folder_name = sanitize_name(user_name)
                os.makedirs(os.path.join('logs', folder_name), exist_ok=True)

                # Сохранение фотографии профиля
                photo_url = profile.get('photo_max_orig')
                if photo_url:
                    image_filename = os.path.join('logs', folder_name, 'profile_picture.jpg')
                    if download_profile_picture(photo_url, image_filename):
                        console.print(f"[green]✔ Профильная картинка сохранена в {image_filename}[/green]")
                else:
                    console.print("[yellow]Профильная картинка не найдена[/yellow]")

                # Сохранение постов пользователя
                for post in user_data.get('posts', []):
                    post_id = post['id']
                    post_filename = os.path.join('logs', f"{user_id}_{post_id}.json")
                    with open(post_filename, 'w', encoding='utf-8') as f:
                        json.dump(post, f, indent=4, ensure_ascii=False)
                    console.print(f"[green]Пост {post_id} сохранён в {post_filename}[/green]")

                # Сохранение данных в JSON
                data_filename = f"logs/vk_user_data_{user_id}_{timestamp}.json"
                with open(data_filename, "w", encoding="utf-8") as f:
                    json.dump(user_data, f, indent=4, ensure_ascii=False)
                console.print(f"[green]Данные сохранены в {data_filename}[/green]")
            else:
                console.print(f"[red]Не удалось получить данные для {screen_name}[/red]")
        else:
            console.print(f"[red]Не удалось разрешить screen_name: {screen_name} или это не пользователь[/red]")
        time.sleep(0.4)  # Задержка для соблюдения лимитов API

    console.print(f"[bold green]✓ Все профили обработаны[/bold green]")

if __name__ == "__main__":
    run()