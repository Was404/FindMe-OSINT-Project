# VK-OK-TG OSINT Addons

### Описание
Является дополнением проекта [OSINT-HUNTER](https://github.com/cryptdefender323/OSINT-Hunter/tree/main)

> [!Note] Расширения OSINT, позволяющие проводить поиск открытых источников на сайтах vk, ok, telegram.



- `vk_parser.py`
поиск по vk id, поиск постов юзера с ключевыми словами, загрузка фото. 

---

### 📚Оглавление
- [📚Оглавление](#📚оглавление)
- [TODO](#todo)
- [📦Установка](#📦установка)
- [⛓️Описание-модулей](#⛓️описание-модулей)
    - [VK Парсер](#vk-парсер)
- [❌Troubleshooting](#❌troubleshooting)
- [📣Прочее](#📣прочее)

---


### TODO

- [x] стратегии для сайтов 
- [x] Использовать vk API
- [ ] OK Парсер(не готов)
- [ ] TGstat Парсер()
- [ ] Использовать сторонние ТГ боты?
- [ ] Поиск родственников?
- [x] Измени requirements, я добавил костыль))0)
- [ ] было бы прикольно как-то по поиску картинки в поисковике определить фейк ли страница


### 📦Установка 

1. **Скачайте** главный [проект](https://github.com/cryptdefender323/OSINT-Hunter/tree/main) используя git: `git clone https://github.com/cryptdefender323/OSINT-Hunter.git`

2. Далее в этом же каталоге, где храниться проект, **скачайте наш репозиторий** с модулями: `git clone https://github.com/Was404/FindMe-OSINT-Project.git` 

3. После того, как скачали, **запустите скрипт установки:**
    - *Для Windows:* `install-modules.ps1`
    - *Для Linux\MacOS:* `install-modules.sh`

> **NOTE:** Скрипт установки добавляет необходимые зависимости в зависимости главного проекта. Также *модифицирует главный проект* для корректного запуска новых модулей.

4. После успешной установки, **следуем инструкциям:**
    ```bash
    bash install.sh
    python3 -m pip install --break-system-packages -r requirements.txt
    ```
5. **Для виртуализации(необязательно):**

    ```bash
    python -m venv env
    ```

    - На Linux: `source env/bin/activate`
    - На Windows: `.\env\Scripts\activate`

    ```bash
    # install-modules добавляет необходимые зависимости, поэтому смело выполняем общие зависимости
    python3 -m pip install --break-system-packages -r requirements.txt
    ```

##### И готово!

##### **ВАЖНО!**

В этом проекте есть модуль `vk_parser.py` который использует для работы **VK API** из файла `config.py`. Чтобы использовать `vk_parser.py`, добавьте **ваш VK API** в файл `config.py`.

---

### ⛓️Описание модулей

#### VK Парсер

##### Пример структуры пользователя

```json
{
    "user_id": 1,
    "profile": {
        "first_name": "Павел",
        "last_name": "Дуров",
        "sex": 2,
        "bdate": "10.10.1984",
        "city": {"id": 1, "title": "Москва"},
        "country": {"id": 1, "title": "Россия"},
        "home_town": "Санкт-Петербург",
        "photo_max_orig": "[invalid url, do not cite]",
        "domain": "durov",
        "education": [...],
        "status": "Статус пользователя",
        "followers_count": 1000000,
        "occupation": {...},
        "relatives": [],
        "relation": 1,
        "personal": {...}
    },
    "liked_posts": [
        {"id": 123, "owner_id": -1, "text": "Текст поста", ...},
        ...
    ],
    "universities": [
        {
            "name": "Московский Государственный Университет",
            "group": {
                "id": 12345,
                "name": "МГУ - официальная страница"
            },
            "posts_with_keywords": [
                {"id": 678, "owner_id": -12345, "text": "Пост с ключевым словом", ...},
                ...
            ]
        },
        ...
    ],
    "note": "Посты, которые пользователь прокомментировал, не могут быть получены из-за ограничений VK API."
}
```
---

### ❌Troubleshooting

- ***Добавил VK API в config, но не работает***

    - Убедитесь что файл `config.py` находится по такому пути:  
    ```bash
        > where config.py
        OSINT-HUNTER/config.py
    ```
    - `config.py` должен выглядеть следующим образом:
    ```bash
        > cat config.py
        TOKEN_VK="<ваш токен vk api>"
    ```

---

### 📣Прочее

