from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import json
import os
import traceback

# Создаем директорию для логов, если ее нет
os.makedirs("logs", exist_ok=True)

# Настраиваем опции браузера (headless режим для работы без GUI)
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument('--disable-software-rasterizer')
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

# Инициализируем веб-драйвер
driver = webdriver.Chrome(options=chrome_options)

def get_channel_links():
    """Извлекает ссылки на Telegram-каналы со страницы"""
    driver.get("https://tgstat.ru/en/tag/rostov-region")
    
    # Ждем, пока страница полностью загрузится
    WebDriverWait(driver, 30).until(lambda d: d.execute_script('return document.readyState') == 'complete')
    
    # Проверяем наличие фреймов
    frames = driver.find_elements(By.TAG_NAME, "iframe")
    if frames:
        driver.switch_to.frame(frames[0])
        print("Switched to iframe")
    
    try:
        # Ждем видимости элементов
        WebDriverWait(driver, 30).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, ".peer-item-box a.text-body"))
        )
    except TimeoutException:
        print("Timeout waiting for elements")
        driver.save_screenshot("logs/error_screenshot.png")
        with open("logs/page_source.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        raise
    
    # Прокручиваем страницу для загрузки всех каналов
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        try:
            show_more_button = driver.find_element(By.CLASS_NAME, "lm-button")
            show_more_button.click()
            time.sleep(2)
        except:
            pass
        if new_height == last_height:
            break
        last_height = new_height
    
    # Извлекаем все ссылки на каналы
    channel_elements = driver.find_elements(By.CSS_SELECTOR, ".peer-item-box a.text-body")
    print(f"Found {len(channel_elements)} channel elements")
    channel_links = [elem.get_attribute('href') for elem in channel_elements][:300]
    return channel_links

def parse_channel_posts(channel_url, keywords):
    """Парсит посты канала и ищет ключевые слова"""
    driver.get(channel_url)
    
    # Ждем загрузки постов
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "post-text"))
        )
    except:
        print(f"Не удалось загрузить посты для {channel_url}")
        return []

    # Прокручиваем страницу для загрузки большего количества постов
    for _ in range(3):  # Прокручиваем 3 раза
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
    
    results = []
    post_elements = driver.find_elements(By.CLASS_NAME, "post-text")
    
    for post_elem in post_elements:
        try:
            post_text = post_elem.text.strip()
            if not post_text:
                continue
                
            # Ищем ключевые слова в тексте поста
            found_keywords = [kw for kw in keywords if kw.lower() in post_text.lower()]
            if found_keywords:
                # Пытаемся найти ссылку на пост
                try:
                    post_link_elem = post_elem.find_element(By.XPATH, "./ancestor::a[@href]")
                    post_link = post_link_elem.get_attribute('href')
                except:
                    post_link = "No link available"
                
                results.append({
                    "channel": channel_url,
                    "post_link": post_link,
                    "text": post_text,
                    "keywords_found": found_keywords
                })
        except Exception as e:
            print(f"Ошибка при обработке поста в {channel_url}: {e}")
    
    return results

def run():
    # Определяем ключевые слова для поиска
    keywords_input = input("Введите ключевые слова через запятую: ")
    keywords = [kw.strip() for kw in keywords_input.split(',')]
    
    try:
        # Получаем ссылки на каналы
        print("Извлекаем ссылки на каналы...")
        channel_links = get_channel_links()
        print(f"Найдено {len(channel_links)} каналов")
        
        all_results = []
        
        # Обрабатываем каждый канал
        for i, channel_url in enumerate(channel_links, 1):
            print(f"Обрабатываем канал {i}/{len(channel_links)}: {channel_url}")
            try:
                channel_results = parse_channel_posts(channel_url, keywords)
                all_results.extend(channel_results)
            except Exception as e:
                print(f"Ошибка при обработке канала {channel_url}: {e}")
            time.sleep(1)  # Задержка для снижения нагрузки на сервер
        
        # Сохраняем результаты в JSON
        with open("logs/results.json", "w", encoding="utf-8") as f:
            json.dump(all_results, f, indent=4, ensure_ascii=False)
        print(f"Результаты сохранены в logs/results.json. Найдено постов: {len(all_results)}")
        
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        traceback.print_exc()
    finally:
        driver.quit()


run()