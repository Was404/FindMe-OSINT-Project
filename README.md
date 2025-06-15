# FindMe - OSINT Project

---

### Описание

- `vk_parser.py`
поиск по vk id, поиск постов юзера с ключевыми словами, загрузка фото. 


### TODO

- [x] стратегии для сайтов 
- [x] Использовать vk API ?
- [ ] Использовать сторонние ТГ боты?
- [ ] Поиск родственников?

---

#### Пример структуры пользователя

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
        "photo_max_orig": "[invalid url, do not cite]
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

