# День 8 — Python для ИБ + Passive Recon (OSINT)
**Дата:** 07.04.2026  
**Результат теста:** 4/5 ✅  
**GitHub:** muhammadjumazoda06-design/cybersec-journey

---

## 🧠 Ключевые концепции

### Passive vs Active Recon
| | Passive Recon | Active Recon |
|---|---|---|
| Контакт с целью | Нет — цель не знает | Да — пакеты к цели |
| Следы в логах | Не оставляет | Оставляет |
| Примеры | Shodan, WHOIS, crt.sh | nmap, ping, banner grab |
| Когда использовать | Всегда первым | После разрешения / в лабе |

### Путь Passive Recon
```
Цель: domain.com → WHOIS → DNS записи → Субдомены → Email/Сотрудники → Shodan → Attack Surface Map
```

### DNS записи — что искать
| Тип | Что хранит | Зачем пентестеру |
|-----|-----------|-----------------|
| A | IPv4 адрес | Найти IP серверов |
| AAAA | IPv6 адрес | IPv6 инфраструктура |
| MX | Почтовые серверы | Провайдер почты (Google/MS/Proofpoint) |
| TXT | Текст (SPF, DKIM) | Раскрывает используемые сервисы |
| NS | DNS серверы зоны | Нужен для zone transfer атаки |
| CNAME | Псевдоним домена | CDN провайдер (Cloudflare, Akamai) |
| SOA | Главный DNS сервер | Точка входа для AXFR |

---

## 🐍 Python инструменты

### Установка dnspython
```bash
# В ТЕРМИНАЛЕ (не в .py файле!)
pip3 install dnspython

# Если ошибка "externally-managed-environment"
pip3 install dnspython --break-system-packages

# Проверка установки
python3 -c "import dns; print(dns.__version__)"
```

### Порт-сканер на socket (без nmap)
```python
import socket
import concurrent.futures
import sys

def scan_port(host, port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.5)           # ждём 0.5 сек на порт
        result = sock.connect_ex((host, port))
        sock.close()
        return port if result == 0 else None   # 0 = порт открыт
    except:
        return None                    # ошибка — пропускаем порт

def fast_scan(host, ports):
    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as ex:
        # 100 параллельных потоков — 1000 портов за ~5 сек
        results = ex.map(lambda p: scan_port(host, p), ports)
    return [p for p in results if p]   # только открытые

host = sys.argv[1]          # python3 scanner.py 10.10.10.10
ports = range(1, 1001)
print(fast_scan(host, ports))
```

**Ключевые концепции кода:**
- `socket.AF_INET` = IPv4, `socket.SOCK_STREAM` = TCP
- `connect_ex()` возвращает 0 если открыт, иначе код ошибки
- `ThreadPoolExecutor` — параллельные потоки (в 100x быстрее)
- `with ... as` — автоматически закрывает ресурс
- `lambda p:` — анонимная функция в одну строку
- `try/except` — программа не падает при ошибке соединения

### DNS резолвер
```python
import dns.resolver
import dns.zone
import dns.query

def get_dns_records(domain):
    record_types = ['A', 'MX', 'TXT', 'NS', 'CNAME']
    for rtype in record_types:          # цикл по каждому типу
        try:
            answers = dns.resolver.resolve(domain, rtype)  # DNS запрос
            for r in answers:
                print(f"{rtype}: {r}")  # f-строка — вставляет переменные
        except:
            pass                        # нет записи — пропускаем

def zone_transfer(domain):
    ns_servers = dns.resolver.resolve(domain, 'NS')   # находим NS серверы
    for ns in ns_servers:              # пробуем каждый
        try:
            zone = dns.zone.from_xfr(  # читаем зону целиком
                dns.query.xfr(str(ns), domain)  # AXFR запрос
            )
            for name in zone.nodes.keys():
                print(f"[AXFR] {name}.{domain}")   # субдомены!
        except Exception as e:
            print(f"Zone transfer refused: {e}")    # сервер защищён
```

---

## 🔍 OSINT инструменты

### theHarvester — исправленные команды

> ⚠️ В версии 4.10+ движки `google` и `bing` УДАЛЕНЫ (стали платными)

```bash
# Установка (уже есть в Kali)
sudo apt install theharvester -y

# РАБОЧАЯ команда (v4.10+)
theHarvester -d tryhackme.com -b crtsh,dnsdumpster,hackertarget -l 200

# Все источники автоматически
theHarvester -d tryhackme.com -b all -l 100

# С сохранением отчёта
theHarvester -d hackthebox.com -b crtsh,dnsdumpster -l 500 -f report
```

**Флаги theHarvester:**
| Флаг | Пример | Описание |
|------|--------|----------|
| `-d` | `-d tryhackme.com` | domain — цель |
| `-b` | `-b crtsh,dnsdumpster` | backend — источники данных |
| `-l` | `-l 200` | limit — лимит результатов |
| `-f` | `-f report` | file — сохранить в HTML/XML |
| `-n` | `-n` | DNS резолвинг найденных хостов |
| `-v` | `-v` | verbose — подробный вывод |

**Рабочие источники в v4.10:**
`crtsh` · `dnsdumpster` · `hackertarget` · `rapiddns` · `otx` · `virustotal`

### Subfinder
```bash
# Установка
sudo apt install subfinder -y

# Базовый скан
subfinder -d hackthebox.com -o subdomains.txt

# Подробный с потоками
subfinder -d hackthebox.com -v -t 50 -o subs.txt

# Комбо: найти субдомены → проверить живые
cat subs.txt | httpx -title -status-code
```

### WHOIS и dig
```bash
# WHOIS — кто владелец домена
whois tryhackme.com
whois 10.10.10.10          # работает и по IP

# dig — DNS запросы
dig tryhackme.com A        # IP адрес
dig tryhackme.com MX       # почтовые серверы
dig tryhackme.com TXT      # SPF, DKIM, верификации
dig tryhackme.com NS       # DNS серверы зоны
dig tryhackme.com ANY      # все записи сразу

# Zone Transfer (AXFR) — учебный домен
dig NS zonetransfer.me                              # шаг 1: найти NS
dig axfr @nsztm1.digi.ninja zonetransfer.me         # шаг 2: украсть зону
host -t axfr zonetransfer.me nsztm1.digi.ninja      # альтернатива
```

### Shodan CLI
```bash
# Установка и настройка
pip3 install shodan
shodan init ВАШ_API_КЛЮЧ    # бесплатный на shodan.io

# Информация по IP
shodan host 1.1.1.1

# Поиск по организации
shodan search "org:tryhackme" --fields ip_str,port

# Поиск уязвимых серверов (только в лабе!)
shodan search 'vuln:CVE-2021-44228'
```

### fierce — DNS брутфорс
```bash
sudo apt install fierce -y

# Zone transfer + брутфорс субдоменов
fierce --domain zonetransfer.me

# Свой словарь
fierce --domain hackthebox.com --subdomain-file /usr/share/wordlists/dirb/common.txt
```

---

## ⚔️ Zone Transfer (AXFR) — что это

**Суть:** Механизм репликации DNS зоны между серверами.  
**Уязвимость:** Если NS сервер не ограничивает кто может запрашивать — любой получит **ВСЕ записи** зоны.  
**Результат:** Все субдомены, внутренние IP, почтовые серверы — полная карта сети.

```
Атакующий → AXFR запрос → NS сервер → (не защищён) → Вся зона целиком
```

**Практика:** `zonetransfer.me` — специально уязвимый учебный домен. Получишь 30+ субдоменов.

---

## 📋 Чеклист Дня 8

- [x] Понимаю разницу passive vs active recon
- [x] Знаю все типы DNS записей и зачем они нужны
- [x] Установил theHarvester, исправил ошибку с google/bing источниками
- [x] Понимаю код порт-сканера (socket, ThreadPoolExecutor, try/except)
- [x] Понимаю код DNS резолвера (dns.resolver, zone transfer)
- [ ] Выполнил zone transfer на zonetransfer.me
- [ ] Нашёл субдомены через Subfinder
- [ ] Прошёл TryHackMe: Passive Reconnaissance

---

## 🔗 Ресурсы

- [crt.sh](https://crt.sh) — Certificate Transparency поиск субдоменов
- [dnsdumpster.com](https://dnsdumpster.com) — DNS карта домена онлайн
- [shodan.io](https://shodan.io) — поисковик устройств
- [zonetransfer.me](https://zonetransfer.me) — учебный домен для AXFR практики
- [TryHackMe: Passive Recon](https://tryhackme.com/room/passiverecon)

---

## 💡 Что дальше — День 9

**Тема:** Продолжение Python для ИБ — HTTP запросы, веб-скрапинг  
**Инструменты:** requests, BeautifulSoup, Burp Suite  
**Задание:** Написать Python скрипт для автоматизации веб-запросов

---
*Прогресс: 8/60 дней · Фаза 1: Основы · Тест: 4/5*
