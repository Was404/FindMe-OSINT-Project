from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import datetime
import logging
import time

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_registration_date(user_id):
    """
    Получает дату регистрации пользователя VK с сайта regvk.com с помощью Selenium и BeautifulSoup.

    Args:
        user_id (str): ID пользователя VK.

    Returns:
        datetime.datetime: Дата регистрации пользователя или None в случае ошибки.
    """
    try:
        # Инициализация WebDriver
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")  # Запуск в фоновом режиме
        driver = webdriver.Chrome(options=options)
        driver.get("https://regvk.com")
        logger.info(f"Открыт сайт regvk.com для пользователя {user_id}")

        # Ввод ID пользователя в поле <input id="enter">
        input_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "enter"))
        )
        input_field.send_keys(user_id)

        # Нажатие на кнопку <button value="Определить дату регистрации">
        button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@value='Определить дату регистрации']"))
        )
        button.click()

        # Задержка для полной загрузки страницы
        time.sleep(3)

        # Проверка на наличие ошибки на странице
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        error_message = soup.find(string=lambda text: text and ("ошибка" in text.lower() or "не найдена" in text.lower()))
        if error_message:
            logger.error(f"Ошибка на странице regvk.com: {error_message}")
            driver.quit()
            return None

        # Попытка найти дату через XPath
        try:
            date_text = driver.find_element(By.XPATH, "/html/body/div/div/div/div[1]/div[2]/table/tbody/tr[2]/td").text.strip()
        except Exception as e:
            logger.error(f"Ошибка при получении даты через XPath: {e}")
            # Попытка через BeautifulSoup
            date_element = soup.find(string="Дата регистрации")
            if date_element:
                date_text = date_element.find_next('td')
                if date_text:
                    date_text = date_text.text.strip()
                    logger.info(f"Найден текст даты (BeautifulSoup): {date_text}")
                else:
                    logger.error("Элемент <td> с датой регистрации не найден")
                    driver.quit()
                    return None
            else:
                logger.error("Текст 'Дата регистрации' не найден на странице")
                driver.quit()
                return None

        # Извлечение и преобразование даты (формат: "Дата регистрации: 23 июля 2013 года")
        if ": " not in date_text:
            logger.error(f"Некорректный формат даты: {date_text}")
            driver.quit()
            return None

        date_str = date_text.split(": ")[1].strip()
        months = {
            "января": 1, "февраля": 2, "марта": 3, "апреля": 4, "мая": 5, "июня": 6,
            "июля": 7, "августа": 8, "сентября": 9, "октября": 10, "ноября": 11, "декабря": 12
        }
        try:
            # Удаляем слово "года", если оно есть
            date_parts = date_str.split()
            if date_parts[-1].lower() == "года":
                date_parts = date_parts[:-1]
            day, month_name, year = date_parts
            month = months[month_name]
            date_obj = datetime.datetime.strptime(f"{day} {month} {year}", "%d %m %Y")
            logger.info(f"Дата регистрации для {user_id}: {date_obj}")
            driver.quit()
            return date_obj
        except (ValueError, KeyError, IndexError) as e:
            logger.error(f"Ошибка преобразования даты '{date_str}': {e}")
            driver.quit()
            return None

    except Exception as e:
        logger.error(f"Ошибка при получении даты регистрации для пользователя {user_id}: {e}")
        driver.quit()
        return None

def calculate_fake_probability(registration_date):
    """
    Рассчитывает вероятность фейковости профиля на основе возраста аккаунта.

    Args:
        registration_date (datetime.datetime): Дата регистрации пользователя.

    Returns:
        float: Вероятность фейковости (от 0.0 до 1.0).
    """
    if registration_date is None:
        return 0.4  # Высокая вероятность фейка, если дата не получена

    today = datetime.datetime.now()
    account_age = (today - registration_date).days / 365.25  # Возраст в годах

    fake_score = 0.0
    if account_age < 1:
        fake_score += 0.4  # Аккаунт младше 1 года
    elif account_age < 3:
        fake_score += 0.2  # Аккаунт младше 3 лет

    return min(fake_score, 1.0)