from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
import time
from config import SITES, KEYWORDS, OUTPUT_FILE

# Настройка WebDriver
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless")  # Фоновый режим
chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # Обход обнаружения ботов
chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])  # Скрыть автоматизацию
driver = None

# Попытка инициализации WebDriver
try:
    print("Попытка инициализации Chrome...")
    driver = webdriver.Chrome(options=chrome_options)
    print("Chrome успешно инициализирован")
except Exception as e:
    print(f"Ошибка Chrome: {str(e)}")
    try:
        print("Попытка инициализации Firefox...")
        driver = webdriver.Firefox()
        print("Firefox успешно инициализирован")
    except Exception as e:
        print(f"Ошибка Firefox: {str(e)}")
        try:
            print("Попытка инициализации IE...")
            driver = webdriver.Ie()
            print("IE успешно инициализирован")
        except Exception as e:
            print(f"Ошибка IE: {str(e)}")
            try:
                print("Попытка инициализации Safari...")
                driver = webdriver.Safari()
                print("Safari успешно инициализирован")
            except Exception as e:
                print(f"Ошибка Safari: {str(e)}")
                raise Exception("Не удалось инициализировать ни один браузер")

def scroll_page(driver, scroll_pause_time=2, max_scrolls=10):
    """Прокрутка страницы до конца"""
    last_height = driver.execute_script("return document.body.scrollHeight")
    scrolls = 0
    while scrolls < max_scrolls:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_pause_time)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
        scrolls += 1

def normalize_url(url):
    """Добавляет https://, если схема отсутствует"""
    if not url.startswith(('http://', 'https://')):
        return f"https://{url}"
    return url

def find_posts_with_keywords():
    results = {}
    
    for site in SITES:
        if "vk.com" not in site:
            continue
        
        try:
            site = normalize_url(site)  # Исправляем URL
            print(f"Обрабатывается: {site}")
            driver.get(site)
            
            # Проверка на страницу логина
            try:
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='login']"))
                )
                print("Требуется авторизация. Пропускаем сайт.")
                continue
            except TimeoutException:
                pass
            
            # Ожидание загрузки постов
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.wall_item"))
                )
            except TimeoutException:
                print("Посты не загрузились. Пропускаем сайт.")
                continue
            
            scroll_page(driver)
            posts = driver.find_elements(By.CSS_SELECTOR, "div.wall_item")
            site_results = []
            
            for post in posts:
                try:
                    text = post.text.lower()
                    if any(keyword.lower() in text for keyword in KEYWORDS):
                        link_element = post.find_element(By.CSS_SELECTOR, "a[href*='wall']")
                        link = link_element.get_attribute("href")
                        if link.startswith("https://vk.com/wall"):
                            site_results.append(link)
                except NoSuchElementException:
                    continue
            
            results[site] = site_results
            print(f"Найдено постов: {len(site_results)}")
        
        except WebDriverException as e:
            print(f"Ошибка на {site}: {str(e)}")
            continue
    
    return results

# Запуск поиска
try:
    found_links = find_posts_with_keywords()
finally:
    if driver:
        driver.quit()

# Сохранение результатов
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    for site, links in found_links.items():
        f.write(f"\n--- {site} ---\n")
        for link in links:
            f.write(link + "\n")

print(f"Результаты сохранены в {OUTPUT_FILE}")