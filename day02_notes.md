# День 2 — Python для ИБ + OSINT и разведка

**Дата:** 30 марта 2026
**Платформа:** Kali Linux + Python3
**Статус:** ✅ Завершён

---

## Python модули для ИБ

| Модуль | Для чего | Пример |
|---|---|---|
| socket | Работа с сетью на низком уровне | Порт-сканер, banner grabbing |
| requests | HTTP запросы | Автоматизация веб-атак |
| subprocess | Запуск системных команд | Обернуть nmap в скрипт |
| os | Файлы и директории | Читать wordlist из файла |
| sys | Аргументы командной строки | python3 scan.py 192.168.1.1 |

---

## socket — как работает

```python
import socket

s = socket.socket()       # создаём "трубку"
s.settimeout(0.5)         # ждём максимум 0.5 сек
result = s.connect_ex(("192.168.1.1", 80))
# 0 = порт открыт, всё остальное = закрыт
if result == 0:
    print("Открыт")
s.close()
```

**Важно:**
- `connect_ex()` возвращает 0 = открыт, не 0 = закрыт
- `settimeout()` критически важен — без него сканер висит 30 сек на каждом порту
- `s.close()` обязателен — иначе кончатся файловые дескрипторы (~1024)

---

## try / except — обработка ошибок

```python
try:
    ip = socket.gethostbyname("google.com")
    print(f"IP: {ip}")
except socket.gaierror:
    print("Домен не найден")
```

- Без try/except — скрипт падает при первой ошибке
- С try/except — ловит ошибку и продолжает работу
- `socket.gaierror` — домен не существует в DNS

---

## Написанные скрипты

### port_scanner.py — порт-сканер

```python
import socket
import time

host = "scanme.nmap.org"
start = time.time()

print(f"Сканирую {host}...")

for port in range(1, 101):
    s = socket.socket()
    s.settimeout(0.5)
    if s.connect_ex((host, port)) == 0:
        print(f"[+] Порт {port} ОТКРЫТ")
    s.close()

print(f"Готово за {time.time()-start:.1f} секунд")
```

**Результат на scanme.nmap.org:**
- [+] Порт 22 ОТКРЫТ (SSH)
- [+] Порт 80 ОТКРЫТ (HTTP)
- Готово за 74 секунды

### dns_resolver.py — DNS резолвер

```python
import socket, sys, time

domains = open(sys.argv[1]).read().splitlines()
start = time.time()

for domain in domains:
    try:
        ip = socket.gethostbyname(domain.strip())
        print(f"[+] {domain:<30} → {ip}")
    except socket.gaierror:
        print(f"[-] {domain:<30} → не резолвится")

print(f"Готово за {time.time()-start:.2f} секунд")
```

**Результат на domains.txt:**
- [+] google.com → 64.233.165.102
- [+] github.com → 140.82.121.3
- [+] tryhackme.com → 104.20.29.66
- [+] asu.tut.tj → 185.194.199.34

---

## OSINT — разведка по открытым источникам

**OSINT** = Open Source Intelligence — сбор данных из открытых источников.

### Passive vs Active Recon

| | Passive Recon | Active Recon |
|---|---|---|
| Контакт с целью | Нет | Да |
| Следы в логах | Нет | Да |
| Примеры | DNS, Whois, Google | nmap, ping, sqlmap |
| Юридически | Безопасно | Нужно разрешение |

### Инструменты OSINT

**theHarvester** — сбор email и поддоменов:
```bash
theHarvester -d tryhackme.com -b google
```

**Whois** — владелец домена:
```bash
whois google.com
```

**dig** — DNS записи:
```bash
dig google.com ANY
dig axfr @ns1.zonetransfer.me zonetransfer.me
```

**Shodan** — поисковик устройств в интернете:
```
org:"Company Name"
port:22 country:TJ
```

**Google Dorks:**
```
site:company.com filetype:pdf
site:company.com inurl:admin
site:company.com filetype:xls
```

### DNS записи — типы

| Тип | Что содержит | Зачем пентестеру |
|---|---|---|
| A | IPv4 адрес | Реальный IP цели для nmap |
| MX | Почтовый сервер | Цель для фишинга |
| NS | DNS серверы | Zone transfer (AXFR) |
| TXT | SPF, DKIM | Анализ защиты почты |
| CNAME | Псевдоним | Раскрывает инфраструктуру |

---

## Что сделал сегодня

- [x] Написал порт-сканер на Python (без nmap) — нашёл порты 22 и 80
- [x] Написал DNS резолвер — проверил 4 реальных домена
- [x] Понял разницу passive vs active recon
- [x] Изучил OSINT инструменты
- [x] Все скрипты загружены на GitHub

---

## Завтра — День 3

- OWASP Top 10
- Установка DVWA
- SQL Injection вручную
- Burp Suite — перехват HTTP запросов
