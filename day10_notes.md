# День 10 — Burp Suite: Proxy, Intercept, Repeater, Intruder, Decoder

## 📌 Что прошли сегодня
Полный практический разбор Burp Suite Community Edition на DVWA (Damn Vulnerable Web Application).

---

## 🔧 Модуль 1: Proxy + Intercept

### Как работает
Burp Suite стоит между браузером и сервером — перехватывает каждый HTTP запрос.

```
Браузер → [Burp Proxy :8080] → Сервер
```

### Настройка Firefox
- Settings → Network Settings → Manual proxy
- HTTP Proxy: `127.0.0.1` Port: `8080`
- ✅ Also use this proxy for HTTPS
- Очистить поле "No proxy for"

### Важный параметр about:config
```
network.proxy.allow_hijacking_localhost = true
```
Без этого Firefox не проксирует localhost (127.0.0.1)!

### CA Сертификат
- Перейти на `http://127.0.0.1:8080` → скачать `cacert.der`
- Firefox → Settings → Certificates → Import → доверять при идентификации сайтов
- Без этого HTTPS трафик не перехватывается

### Кнопки Intercept
| Кнопка | Действие |
|---|---|
| Intercept is ON | Замораживает каждый запрос |
| Forward | Отправить запрос дальше на сервер |
| Drop | Выбросить запрос, сервер не получит |

### Практика
Перехватили POST запрос логина DVWA:
```
username=admin&password=password&Login=Login
```
Изменили `password=password` → `password=WRONGPASS` → Forward  
Результат: **Login failed** — сервер получил изменённый запрос!

---

## 🔁 Модуль 2: Repeater

### Что делает
Берёт один запрос и позволяет отправлять его многократно, меняя параметры вручную.

### Горячая клавиша
```
Ctrl + R  →  Send to Repeater
```

### Практика — ручное тестирование SQLi
Тестировали параметр `id=` на странице `/dvwa/vulnerabilities/sqli/`

| Payload | Ответ | Вывод |
|---|---|---|
| `id=1` | 200 OK, Length: 4732 | Нормальный запрос |
| `id=1'` | 500 Internal Server Error | SQL запрос сломан — уязвимость есть! |
| `id=1+OR+1=1--+` | 200 OK, Length: 4661 | Инъекция выполнена! |

### Важное замечание
- В GET параметрах пробелы заменяются на `+`
- Cookie `security=low` обязательна для работы уязвимостей
- Если PHPSESSID истёк — нужно войти заново и взять свежую куку

---

## 🎯 Модуль 3: Intruder

### Что делает
Автоматически подставляет список значений (payloads) в выбранные позиции запроса.

### Типы атак
| Тип | Описание | Когда использовать |
|---|---|---|
| **Sniper** | 1 список, 1 позиция | Знаешь логин, перебираешь пароли |
| **Battering Ram** | 1 список, все позиции одновременно | Логин = Пароль |
| **Pitchfork** | Несколько списков параллельно | Готовые пары логин:пароль |
| **Cluster Bomb** | Все комбинации | Не знаешь ни логин ни пароль |

### Горячая клавиша
```
Ctrl + I  →  Send to Intruder
```

### Настройка позиций
В Positions выделить нужное значение → нажать **Add §**
```
username=admin&password=§test123§&Login=Login
```

### Как читать результаты
- Все неверные пароли → одинаковый **Length**
- Верный пароль → **отличающийся Length**
- `302 Location: login.php` = неверный пароль
- `302 Location: index.php` = верный пароль ✅

### Важное про CSRF токен
DVWA использует `user_token` — его нужно удалить из запроса в Intruder иначе все запросы будут отклонены.

### Burp Community Edition
Intruder в бесплатной версии работает медленно (throttled).  
Альтернативы для реального брутфорса: `hydra`, `ffuf`, `medusa`

---

## 🔓 Модуль 4: Decoder

### Что делает
Кодирует и декодирует данные в разных форматах прямо внутри Burp.

### Поддерживаемые форматы
| Формат | Пример |
|---|---|
| Base64 | `admin` → `YWRtaW4=` |
| URL encoding | `<script>` → `%3Cscript%3E` |
| HTML encoding | `<script>` → `&#x3c;&#x73;&#x63;&#x72;&#x69;&#x70;&#x74;&#x3e;` |
| Hex | `admin` → `61646d696e` |
| MD5 Hash | `password` → `5f4dcc3b5aa765d61d8327deb882cf99` |

### Практика
```
admin     → Base64  → YWRtaW4=
YWRtaW4= → Decode  → admin

<script>alert(1)</script> → HTML encoding → &#x3c;&#x73;&#x63;&#x72;...
password → MD5 → 5f4dcc3b5aa765d61d8327deb882cf99
```

### Зачем кодировать XSS payload?
Фильтры ищут текст `<script>` — не находят закодированную версию и пропускают.  
Браузер декодирует обратно и **выполняет как HTML**. Это обход WAF/фильтров!

---

## 🧠 Ключевые концепции

### MD5 — не шифрование!
- Это **односторонняя хэш-функция**
- Из текста → хэш: легко
- Из хэша → текст: **невозможно математически**
- Взлом через **радужные таблицы** — базы готовых пар `текст:хэш`
- `password` всегда даёт `5f4dcc3b5aa765d61d8327deb882cf99`

### Типичный рабочий процесс пентестера
```
1. Proxy ON → browse сайт → собираем запросы в HTTP History
2. Находим интересный параметр
3. Ctrl+R → Repeater → тестируем вручную (SQLi, XSS, IDOR)
4. Ctrl+I → Intruder → если нужен автоперебор
5. Decoder → если видим закодированные данные
```

---

## ⚙️ Установка и запуск DVWA (пришлось устанавливать заново)

```bash
# Запуск сервисов
sudo service apache2 start
sudo service mysql start

# Клонирование DVWA
cd /var/www/html/
sudo git clone https://github.com/digininja/DVWA.git dvwa

# Конфиг
cd /var/www/html/dvwa/config/
sudo cp config.inc.php.dist config.inc.php

# Создание БД
sudo mysql -u root
CREATE DATABASE dvwa;
CREATE USER 'dvwa'@'127.0.0.1' IDENTIFIED BY 'p@ssw0rd';
GRANT ALL PRIVILEGES ON dvwa.* TO 'dvwa'@'127.0.0.1';
FLUSH PRIVILEGES;
EXIT;

# Инициализация
# Открыть: http://127.0.0.1/dvwa/setup.php
# Нажать: Create / Reset Database
```

---

## 📚 Полезные ссылки
- [PortSwigger Web Security Academy](https://portswigger.net/web-security)
- [DVWA GitHub](https://github.com/digininja/DVWA)
- [Burp Suite Documentation](https://portswigger.net/burp/documentation)

---

*День 10 завершён ✅ | Следующий: День 11*
