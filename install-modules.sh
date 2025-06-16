#!/bin/bash

# Пути к файлам
source_vk_parser="vk_parser.py"
dest_vk_parser="OSINT-HUNTER/modules/vk_parser.py"
main_py_path="OSINT-HUNTER/main.py"
requirements_source="requirements.txt"
requirements_dest="OSINT-HUNTER/requirements.txt"
config_str=" VK_API="" "
config_dest="OSINT-HUNTER/config.py"

# 1. Копирование vk_parser.py
cp "$source_vk_parser" "$dest_vk_parser"

# 2. Модификация main.py
# Добавление строки в show_menu()
sed -i '/def show_menu():/,/console.print("\[9\]/ {
  /console.print("\[9\]/ a\
    console.print("[10] VK Parser")
}' "$main_py_path"

# Добавление строки в main()
sed -i '/elif choice == "9":/,/run_module("Telegram OSINT Scraper", telegram_scraper.run)/ {
  /run_module("Telegram OSINT Scraper", telegram_scraper.run)/ a\
        elif choice == "10":\
            run_module("VK parser", vk_parser.run)
}' "$main_py_path"

# 3. Копирование содержимого requirements.txt
cat "$requirements_source" >> "$requirements_dest"

# 4. Копирование config.py
touch "$config_dest"
cat "$config_str" >> "$config_dest"

# 5. Вывод сообщения
echo "Установка завершена"