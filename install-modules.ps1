# Путь к файлам
$sourceVkParser = "vk_parser.py"
$destVkParser = "OSINT-HUNTER/modules/vk_parser.py"
$mainPyPath = "OSINT-HUNTER/main.py"
$requirementsSource = "requirements.txt"
$requirementsDest = "OSINT-HUNTER/requirements.txt"
$configStr = "TOKEN_VK"
$configDest = "OSINT-HUNTER/config.py"

# 1. Копирование vk_parser.py
Copy-Item -Path $sourceVkParser -Destination $destVkParser -Force

# 2. Модификация main.py
$mainPyContent = Get-Content -Path $mainPyPath -Raw

# Добавление строки в show_menu()
$showMenuPattern = "def show_menu\(\):"
$showMenuInsert = 'console.print("[10] VK Parser")'
$mainPyContent = $mainPyContent -replace "(?s)(def show_menu\(\):.*?console\.print\(""\[9\].*?""\))", "`$1`n    $showMenuInsert"

# Добавление строки в main()
$mainPattern = 'elif choice == "9":\s+run_module\("Telegram OSINT Scraper", telegram_scraper\.run\)'
$mainInsert = 'elif choice == "10":\n        run_module("VK parser", vk_parser.run)'
$mainPyContent = $mainPyContent -replace "(?s)($mainPattern)", "`$1`n    $mainInsert"

# Запись обновленного содержимого обратно в файл
Set-Content -Path $mainPyPath -Value $mainPyContent -Force

# 3. Копирование содержимого requirements.txt
$requirementsContent = Get-Content -Path $requirementsSource -Raw
Add-Content -Path $requirementsDest -Value $requirementsContent

# 4. Копирование config.py
New-Item -Path $configDest -ItemType File -Force | Out-Null
Add-Content -Path $configDest -Value $configStr

# 5. Вывод сообщения
Write-Host "Установка завершена"