# День 9 — HTTP протокол + Python requests для пентеста
**Дата:** 08.04.2026
**Результат теста:** 4/5 ✅ (13/13 в дневном тесте + 4/5 по requests)
**GitHub:** muhammadjumazoda06-design/cybersec-journey

---

## 🧠 HTTP методы

| Метод | Для чего | Пентест-угол |
|-------|----------|--------------|
| GET | Получить страницу/данные | Параметры в URL → SQLi, XSS |
| POST | Отправить форму | Тело запроса → брутфорс, SQLi |
| PUT | Полная замена объекта | IDOR — замени чужой объект |
| DELETE | Удалить объект | IDOR — удали чужое |
| PATCH | Изменить частично | Изменение отдельных полей |
| HEAD | Только заголовки | Проверить существование файла без скачивания |

**Структура HTTP запроса:**
```
МЕТОД /путь HTTP/1.1
Host: target.com
User-Agent: Mozilla/5.0
Cookie: session=abc123
[пустая строка]
[тело — только у POST/PUT]
```

---

## 📊 HTTP статус-коды

| Код | Значение | Пентест-действие |
|-----|----------|-----------------|
| 200 | OK — успех | Страница существует |
| 201 | Created | POST создал объект |
| 302 | Redirect | После успешного логина |
| 400 | Bad Request | Неверный запрос |
| 401 | Unauthorized | Нужно залогиниться |
| 403 | Forbidden | Авторизован но нет прав → попробуй bypass |
| 404 | Not Found | Ресурс не существует |
| 429 | Too Many Requests | Rate limiting → добавь задержку |
| 500 | Server Error | Ошибка сервера → может раскрыть инфо |

> **Важно:** 401 ≠ 403. При 401 — нужно войти. При 403 — ты уже вошёл, но доступ закрыт.

---

## 🍪 Cookies и сессии

### Зачем нужны cookies
HTTP — протокол без состояния (stateless). Каждый запрос независим. Cookie говорит серверу "это я, уже залогинен".

### Как работает сессия
```
1. Логин → сервер создаёт session_id
2. Ответ: Set-Cookie: session=abc123; HttpOnly; Secure
3. Браузер хранит и отправляет Cookie: session=abc123 с каждым запросом
```

### Флаги cookies
| Флаг | Что делает | Без флага → уязвимость |
|------|-----------|----------------------|
| HttpOnly | JS не может читать cookie | XSS крадёт session cookie |
| Secure | Только через HTTPS | Cookie утекает по HTTP |
| SameSite | Запрет отправки с других сайтов | CSRF атака |

### JWT токены
- Формат: `header.payload.signature` — всё в base64
- Payload НЕ зашифрован, только подписан
- Декодировать: `echo "eyJ1c2VyIjoiYWRtaW4ifQ" | base64 -d`
- Атаки: alg:none, брутфорс подписи

---

## 🐍 Python requests — полный разбор

### Установка
```bash
# requests уже установлен в Kali (v2.32.5)
python3 -c "import requests; print(requests.__version__)"
```

### GET запрос — каждая строка
```python
import requests                              # подключаем библиотеку

r = requests.get('http://dvwa.local/')      # отправляем GET, ответ в r

print(r.status_code)   # число: 200 = ok, 404 = не найдено
print(r.headers)       # словарь заголовков ответа сервера
print(r.text)          # HTML тело страницы (как Ctrl+U в браузере)
print(r.cookies)       # cookies которые установил сервер
print(r.url)           # финальный URL (после редиректов)

# GET с параметрами в URL (?id=1)
params = {'id': '1', 'page': '2'}
r = requests.get('http://dvwa.local/sqli/', params=params)
# итоговый URL: http://dvwa.local/sqli/?id=1&page=2 — requests сам собирает
# для SQLi: params={'id': '1 OR 1=1'} — тестируем инъекцию автоматически
```

### POST запрос — форма логина
```python
# data= — поля HTML формы (name="" атрибуты в HTML)
data = {
    'username': 'admin',
    'password': 'password',
    'Login': 'Login'        # имена берём из <input name="..."> в HTML
}

r = requests.post('http://dvwa.local/login.php', data=data)

print(r.url)            # куда редиректнуло? /index.php = успех, /login.php = fail
print(r.status_code)    # 200 (финальный после редиректа)

# Увидеть сам 302 редирект:
r = requests.post(url, data=data, allow_redirects=False)
print(r.status_code)    # теперь 302 — видим редирект напрямую
```

> **data= vs json=**: `data=` для HTML форм (form-encoded). `json=` для REST API (JSON). Разные форматы — сервер обрабатывает по-разному!

### Session — авторизованные запросы
```python
# ПРОБЛЕМА без Session:
requests.post(login_url, data=data)        # cookie получен
requests.get(sqli_url)                     # cookie ПОТЕРЯН → 302 на логин!

# РЕШЕНИЕ — Session:
s = requests.Session()                     # создаём сессию (запоминает cookies)

s.post('http://dvwa.local/login.php', data=data)  # логинимся — cookie сохранён

# Все следующие запросы через s — автоматически авторизованы:
r = s.get('http://dvwa.local/vulnerabilities/sqli/')
r = s.get('http://dvwa.local/vulnerabilities/xss_r/')

# Добавить cookie вручную (меняем уровень DVWA):
s.cookies.set('security', 'low')

# Посмотреть все cookies сессии:
print(s.cookies)
```

### Кастомные заголовки
```python
headers = {
    # По умолчанию requests отправляет "python-requests/2.32.5"
    # WAF блокирует такие запросы → подменяем на браузерный
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',

    # Если сервер доверяет этому заголовку → bypass IP блокировки!
    'X-Forwarded-For': '127.0.0.1',

    'Referer': 'http://dvwa.local/'
}

r = requests.get(url, headers=headers)

# Отключить проверку SSL (для локальных лаб с самоподписанным сертификатом):
r = requests.get('https://target.local', verify=False)

# Комбо: Session + headers:
r = s.get(url, headers=headers)   # и авторизован, и с нужными заголовками
```

### Полный скрипт — автоматический логин в DVWA
```python
import requests

TARGET = 'http://dvwa.local'

s = requests.Session()

# Устанавливаем уровень сложности
s.cookies.set('security', 'low')

# Логинимся
data = {'username': 'admin', 'password': 'password', 'Login': 'Login'}
s.post(f'{TARGET}/login.php', data=data)

# Проверяем что залогинены
r = s.get(f'{TARGET}/vulnerabilities/sqli/')
if 'login' not in r.url:
    print(f'[+] Авторизован! Статус: {r.status_code}')
    print(f'[+] Страница: {len(r.text)} байт')
else:
    print('[-] Логин не удался')
```

---

## 📋 Чеклист Дня 9

- [x] Знаю все HTTP методы и их пентест-применение
- [x] Понимаю разницу 401 vs 403, 302 vs 200
- [x] Знаю флаги cookies (HttpOnly, Secure, SameSite) и атаки без них
- [x] Понимаю каждую строку requests.get() — r.status_code, r.text, r.headers
- [x] Понимаю разницу data= и json= в POST запросе
- [x] Понимаю зачем Session() и как она хранит cookies
- [x] Знаю зачем подменять User-Agent и X-Forwarded-For
- [ ] Написал скрипт автологина в DVWA через requests.Session()
- [ ] Автоматически отправил SQLi payload через requests

---

## 🔗 Ресурсы

- [Python requests docs](https://docs.python-requests.org)
- [HTTP MDN Reference](https://developer.mozilla.org/en-US/docs/Web/HTTP)
- [JWT decoder](https://jwt.io) — декодировать JWT токены онлайн
- [DVWA](http://dvwa.local) — лаба для практики

---

## 💡 Что дальше — День 10

**Тема:** Burp Suite — перехват и модификация HTTP запросов
**Инструменты:** Burp Suite Community, FoxyProxy
**Задание:** Перехватить запрос логина, модифицировать параметры, найти SQLi через Repeater

---
*Прогресс: 9/60 дней · Фаза 1: Основы · Тест: 13/13 + 4/5 requests*
