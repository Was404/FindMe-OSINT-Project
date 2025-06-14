from rich.console import Console
import requests
from vk_api import VkApi
import os
from datetime import datetime
import json
import unicodedata
from config import TOKEN_VK

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

def get_profile_info(vk, object_id, obj_type):
    """Получает информацию о профиле в зависимости от типа (user или group)."""
    try:
        if obj_type == 'user':
            response = vk.users.get(user_ids=object_id, fields='photo_max_orig,first_name,last_name,bdate,city,country,about,activities,interests,education,career,contacts,connections,relation,sex,verified')
            if response:
                return response[0]
        elif obj_type == 'group':
            response = vk.groups.getById(group_ids=object_id, fields='photo_200,description,members_count,activity,contacts,city,country,verified')
            if response:
                return response[0]
        return None
    except Exception as e:
        console.print(f"[red]Ошибка получения информации о профиле: {e}[/red]")
        return None

def download_profile_picture(photo_url, filename):
    """Скачивает профильную картинку по URL и сохраняет ее в файл."""
    try:
        response = requests.get(photo_url)
        if response.status_code == 200:
            with open(filename, 'wb') as f:
                f.write(response.content)
            return True
        else:
            console.print(f"[yellow]Не удалось скачать фото: {response.status_code}[/yellow]")
            return False
    except Exception as e:
        console.print(f"[red]Ошибка скачивания фото: {e}[/red]")
        return False

def save_json(data, filename):
    """Сохраняет данные в JSON-файл."""
    os.makedirs("logs", exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    console.print(f"[green]Данные сохранены в {filename}[/green]")

def run():
    """Основная функция модуля для извлечения данных из VK-профилей и их постов."""
    console.print(f"\n[bold cyan]:: VK OSINT SCRAPER MODULE[/bold cyan]")
    console.print("[yellow]Примечание: screen_name в VK должны быть на латинице, например, 'durov' вместо 'Дуров'.[/yellow]")
    screen_names_input = input("Введите VK screen_names через запятую: ").strip()
    screen_names = [name.strip() for name in screen_names_input.split(',')]

    # Проверка на кириллические символы
    for name in screen_names:
        if contains_cyrillic(name):
            console.print(f"[yellow]Предупреждение: '{name}' содержит кириллические символы. VK screen_names должны быть на латинице. Пожалуйста, проверьте и введите корректно.[/yellow]")

    timestamp = datetime.now().strftime("%Y%m%d%H%M")
    vk = get_vk_api()
    if vk is None:
        return

    valid_object_ids = []
    for screen_name in screen_names:
        console.print(f"[cyan]→ Обработка профиля: https://vk.com/{screen_name}[/cyan]")
        object_id, obj_type = resolve_screen_name(vk, screen_name)
        if object_id and obj_type:
            profile_info = get_profile_info(vk, object_id, obj_type)
            if profile_info:
                json_filename = f"logs/vk_summary_{object_id}_{timestamp}.json"
                save_json(profile_info, json_filename)
                photo_url = profile_info.get('photo_max_orig') if obj_type == 'user' else profile_info.get('photo_200')
                if photo_url:
                    image_filename = f"logs/vk_profile_{object_id}_{timestamp}.jpg"
                    if download_profile_picture(photo_url, image_filename):
                        console.print(f"[green]✔ Профильная картинка сохранена в {image_filename}[/green]")
                else:
                    console.print("[yellow]Профильная картинка не найдена[/yellow]")
                valid_object_ids.append(object_id)
            else:
                console.print(f"[red]Не удалось получить информацию о профиле для {screen_name}[/red]")
        else:
            console.print(f"[red]Не удалось разрешить screen_name: {screen_name}[/red]")

    # Поиск постов выполняется последним
    for object_id in valid_object_ids:
        console.print(f"[cyan]→ Загрузка постов для object_id: {object_id}[/cyan]")
        try:
            response = vk.wall.get(owner_id=object_id, count=100, filter='owner')
            posts = response.get('items', [])
            posts_filename = f"logs/vk_posts_{object_id}_{timestamp}.json"
            save_json(posts, posts_filename)
            console.print(f"[green]✔ Посты сохранены в {posts_filename}[/green]")
        except Exception as e:
            console.print(f"[red]Не удалось загрузить посты для object_id {object_id}: {e}[/red]")
        time.sleep(0.4)  # Задержка для соблюдения лимитов API

    console.print(f"[bold green]✓ Все профили и посты обработаны[/bold green]")

#if __name__ == "__main__":
#    run()