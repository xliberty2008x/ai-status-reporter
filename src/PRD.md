Документ Вимог до Продукту (PRD) – Журнал змін статусів та Slack‑звіти (Notion + n8n)

Дата: 11 серпня 2025
Підготовлено: Кирило Дубовик, AI Automation Lead

⸻

1. Огляд

Цей документ описує вимоги до вдосконалення системи відстеження статусу проєктів, автоматизації у процесах розробки ігор. Мета — оптимізувати звітування про зміну статусу з Notion у Slack, використовуючи AI-агента для запитів та забезпечити масштабованість системи. Проєкт буде побудовано за допомогою Notion Automations та n8n із зберіганням у Notion.

⸻

2. Цілі
	1.	Зменшення шуму повідомлень: Заміна надмірної кількості сповіщень у Slack на стислий, структурований звіт (щотижневий/щомісячний).
	2.	Історичне відстеження: Зберігання журналу змін статусів проєктів за обмежений період (1 місяць) з регулярним очищенням.
	3.	Доступність даних: Надання можливості інтерактивних AI-запитів у Slack.

⸻

3. Функціональні вимоги

3.1 Збір даних
	•	Сховище: Notion — окрема сервісна таблиця для логування змін статусів (“журнал змін”). Логування кожної зміни: назва проєкту, платформа, версія, попередній → поточний статус, дата, команда, відповідальна особа.
	•	Ретенція: зберігати історію 1 календарний місяць. Видаляти записи, що старші за попередній календарний місяць (через n8n).

3.2 Автоматизація та звітність
	•	Звіти у Slack: щотижневі та щомісячні підсумкові апдейти з агрегованими змінами статусів по проєктах і командах, замість потоку поодиноких нотифікацій. Формат включає: шлях статусів (previous → current) з датами, платформа, версія, команда, ініціатор зміни.
	•	Агрегація змін: якщо за період було кілька змін, показувати повний шлях статусів за тиждень/місяць без дублювання заголовків.

3.3 Інтеграція зі Slack
	•	Автопостинг: регулярне публікування зведень у задані канали Slack.
	•	Інтерактивні запити: реалізуються через сценарії в n8n з використанням вбудованого LangChain як фреймворку для AI-агента, що обробляє запити та працює з логами у Notion.

3.4 Можливості AI-агента
	•	Використання LangChain для побудови AI-агента, який взаємодіє зі Slack та Notion.
	•	Підтримка узагальнення та детального виводу переліку змін за період.

⸻

4. Нефункціональні вимоги
	•	Продуктивність: Формування звітів протягом 5 секунд.
	•	Масштабованість: Підтримка понад 100 активних журналів змін.
	•	Безпека: Контроль доступу до даних відповідно до ролі/команди.
	•	Підтримуваність: Модульність скриптів автоматизації.

⸻

5. Обмеження та зауваги
	•	Первинне сховище — Notion: проєкт побудовано за допомогою Notion Automations та n8n; у разі масштабування можливе винесення історичних логів у зовнішнє сховище (опційно).
	•	Очищення історії: виконується через n8n за місячним графіком — видаляються записи, що старші за попередній календарний місяць.
	•	Обмеження Notion: відсутність системного повного audit log — використовуємо власну сервісну таблицю та автоматизації для фіксації змін.

⸻

6. Критерії успіху
	•	Зменшення кількості дубльованих сповіщень у Slack на 80%.
	•	90% AI-запитів повертають коректні та релевантні відповіді.
	•	Позитивні відгуки команд щодо якості та зрозумілості звітів.

⸻

7. Стейкхолдери
	•	Власник проєкту: Кирило Дубовик, AI Automation Lead
	•	Технічний лід: Олександр Зіменко
	•	Стейкхолдер: Павло Андрійчук
	•	Залучені сторони: Керівництво GameDev, Тімліди, Проджект-менеджери

⸻

8. Відкриті питання
	•	Підтвердити деталі можливостей API Notion для побудови запитів/фільтрацій (обмеження, ліміти).
	•	Узгодити точну модель перетворення «сирих» подій у структуровані логи (політики нормалізації).
	•	Визначити перелік Slack-каналів і формат шаблонів повідомлень (по командах/платформах).

⸻

9. Архітектура та реалізація

9.1 Модель даних у Notion
	•	База «Projects»: назва, команда, платформа, версія, тип релізу, статус тощо.
	•	База «Status Log (Service)»: ключ проєкту, попередній статус, поточний статус, дата зміни, користувач-ініціатор, платформа, версія, команда. Записи створюються при будь-якій зміні полів статусу/версії тощо.

9.2 Автоматизації
	•	Фіксація змін: внутрішні автоматизації Notion та сценарії n8n у зв’язці створюють запис у «Status Log» при зміні статусу/потрібних полів.
	•	Очищення історії (n8n): CRON-тригер раз на місяць; кроки: 1) отримати записи, дата яких < першого дня поточного місяця, 2) видалити їх з «Status Log».
	•	Звіти: щотижневий та щомісячний сценарії n8n формують агреговані апдейти по командах/проєктах і публікують у Slack.
	•	Інтерактивні запити: реалізовані в n8n через LangChain, що працює як AI-агент для взаємодії з користувачем та Notion.

9.3 Прийомні тести (acceptance)
	•	Після місяця роботи в «Status Log» відсутні записи старші за попередній календарний місяць.
	•	Щотижневий звіт у Slack містить консолідований шлях статусів для кожного проєкту, без дублювання заголовків, якщо змін було декілька.
	•	Інтерактивні запити через LangChain повертають коректні відповіді на фільтровані запити.

⸻

10. Технологічний стек
	•	Notion Automations — тригери змін у базах, створення записів у сервісній таблиці, запуск сценаріїв n8n через вебхуки (де потрібно).
	•	n8n — CRON-джоби для місячного очищення, побудова щотижневих/щомісячних зведень, форматування та публікація у Slack, обробка інтерактивних запитів.
	•	LangChain (вбудований у n8n) — фреймворк для побудови AI-агента, який працює з даними у Notion та відповідає у Slack.
	•	Notion API — читання/запити до таблиць, фільтрація та сортування для AI-модуля.

⸻

11. План робіт: Service Log DB для «💼All Projects»

Примітка: нижче — план. Усе, що вже зроблено або випробувано раніше, використано лише як контекст для формування плану.

11.1 Джерело даних
	•	База: «💼All Projects» у Notion — єдиний репозиторій станів і метаданих проєктів.
	•	Причина створення сервісного журналу: Notion не зберігає повний аудит кожної дії автоматично; потрібна проміжна «Service Log» таблиця для фіксації змін та подальшої аналітики. ::hiveTranscript{{timestamp=1885}} ::hiveTranscript{{timestamp=1930}}

11.2 Створення бази «Project Status Change Log» (Service Log)
	•	Місце: той самий робочий простір, секція «Ops/Automation» (або еквівалент).
	•	Призначення: централізоване логування змін статусу (і пов’язаних полів) із «💼All Projects» з можливістю подальшої агрегації для Slack‑звітів і AI‑запитів. ::hiveTranscript{{timestamp=1526}} ::hiveTranscript{{timestamp=1537}} ::hiveTranscript{{timestamp=2101}}
	•	Обов’язкові поля для фільтрації та аналітики:
	•	Date (дата/час зміни)
	•	Team (команда)
	•	Sub‑team (підкоманда)
	•	Project (назва)
	•	Project Link (Relation → «💼All Projects»)
	•	Platform (AMZ/GP/iOS/Fire TV тощо)
	•	Version
	•	Previous Status
	•	New Status
	•	Changed By (людина, що ініціювала зміну)
	•	What’s New (rich text/long text)
	•	Release Type (опційно: First Release/AB Test/Hotfix тощо)
	•	Automation Source (Notion Automations / n8n)
	•	(опційно) Week/Month/Year (для зручного групування у звітах)

Приклад запису (зразок формату)

Date: 2025‑07‑24
Team: AMZ Growth Team
Project Link: https://www.notion.so/sncrchz-Snake-Run-Crawl-Chase-23a9748bc8c28006a1dbc938be594e56
Project: sncrchz – Snake Run: Crawl Chase
Version: 1.3.13
Platform: AMZ Free A/B Test
Status change: BACKLOG → QA
Sub‑team: Growth
Changed By: (користувач)
What’s New: ребілд 1.3.8 з однією підпискою

11.3 Автоматизація в «💼All Projects» (Notion Automations)
	•	Тригер: при зміні поля Status (та, за потреби, Version/інших критичних полів) у записі «💼All Projects» — створювати новий запис у «Project Status Change Log» із мапінгом полів, перелічених у §11.2. (Налаштовується вручну у Notion Automations.) ::hiveTranscript{{timestamp=1537}} ::hiveTranscript{{timestamp=1554}}
	•	Мінімізація шуму: подієве логування використовується для побудови зведених щотижневих/щомісячних апдейтів замість потоку одиночних повідомлень у Slack. ::hiveTranscript{{timestamp=1610}} ::hiveTranscript{{timestamp=1619}}
	•	Агрегація шляху статусів: якщо за період було кілька змін, у звітах відображати повний шлях (наприклад: Backlog → QA → Dev → Live). ::hiveTranscript{{timestamp=1665}} ::hiveTranscript{{timestamp=1678}}

11.4 Сценарії n8n (план)
	1.	Monthly Cleanup (ретенція): раз на місяць видаляти з Service Log записи, що старші за попередній календарний місяць. ::hiveTranscript{{timestamp=2154}} ::hiveTranscript{{timestamp=2206}}
	2.	Weekly Digest → Slack: раз на тиждень агрегувати зміни з Service Log за командами/платформами/проєктами і публікувати у відповідні канали Slack. ::hiveTranscript{{timestamp=1526}} ::hiveTranscript{{timestamp=1537}} ::hiveTranscript{{timestamp=1720}}
	3.	Monthly Digest → Slack: аналогічно щотижневому, але за календарний місяць.
	4.	On‑Demand Q&A (LangChain у n8n): обробляти запити у Slack (фільтри за датою/командою/підкомандою/платформою/проєктом) поверх Service Log. ::hiveTranscript{{timestamp=2101}} ::hiveTranscript{{timestamp=2135}} ::hiveTranscript{{timestamp=2128}}

11.5 Перевірка покриття полів (check‑list)
	•	Дата події (Date)
	•	Команда (Team)
	•	Підкоманда (Sub‑team)
	•	Посилання на проєкт (Relation)
	•	Назва проєкту
	•	Платформа (Platform)
	•	Версія (Version)
	•	Попередній статус (Previous Status)
	•	Новий статус (New Status)
	•	Хто змінив (Changed By)
	•	Що нового (What’s New)
	•	Тип релізу (Release Type, за потреби)
	•	Джерело автоматизації (Automation Source)

11.6 Заплановані представлення (views) у Service Log
	•	All Entries: основна таблиця, сортування за Date ↓.
	•	Last 30 Days / Recent: фільтр останніх 30 днів.
	•	By Team: групування за Team; окремо — By Sub‑team.
	•	Timeline: хронологічний перегляд змін.
	•	By Platform / By Project: додаткові зрізи для операційних питань.

11.7 Звітні формати (для Slack)
	•	Структура блоку по проєкту: Назва/посилання → Платформа/Версія → Зміна статусів (previous → current + дата) → Команда/Підкоманда → Хто змінив → What’s New. ::hiveTranscript{{timestamp=1720}}
	•	Групування: спочатку за Team, далі — за Project. Це зменшує шум і підвищує оглядовість. ::hiveTranscript{{timestamp=1610}} ::hiveTranscript{{timestamp=1619}}

11.8 Додатковий контекст → уточнений план (тільки план)
	1.	Service Log як цільова БД
	•	Створити базу Project Status Change Log (Service Log) у робочому просторі.
	•	Джерело подій: «💼All Projects».
	2.	Автоматизація в «💼All Projects» (налаштовується вручну)
	•	Тригер: on Status change у карточці проєкту.
	•	Дія: Create page у «Project Status Change Log» з мапінгом полів.
	3.	Мапінг полів (All Projects → Service Log)
	•	Project (title) → Project
	•	Project (page URL) → Project Link (Relation/URL)
	•	Team → Team
	•	Sub‑team → Sub‑team
	•	Platform → Platform
	•	Version → Version
	•	Status (previous) → Previous Status
	•	Status (new) → New Status
	•	Last edited by / Actor → Changed By
	•	Changelog / Notes → What’s New
	•	(опц.) Release Type → Release Type
	•	Now() → Date
	•	Константа/системне: Automation Source = Notion Automations
	4.	Перевірка покриття критично важливих полів для запитів
	•	Date (тимчасова фільтрація)
	•	Team / Sub‑team (аналітика по командах)
	•	Platform (зріз по платформах)
	•	Project / Project Link (навігація)
	•	Previous Status / New Status (шлях змін)
	•	Version (вплив релізу)
	•	Changed By (відповідальний)
	•	What’s New (деталі змін)
	5.	Зразок запису (формат для наповнення)

Date: Jul 24
Team: AMZ Growth Team
Project Link: https://www.notion.so/sncrchz-Snake-Run-Crawl-Chase-23a9748bc8c28006a1dbc938be594e56
Project: sncrchz - Snake Run: Crawl Chase
Version: 1.3.13
Platform: AMZ Free A/B Test
Status change: BACKLOG → QA
Sub-team: Growth
Changed By: (користувач)
What’s New: ребілд 1.3.8 з однією підпискою

	6.	Views (план)
	•	All Log Entries (таблиця, сортування за Date ↓).
	•	Status Changes Timeline (хронологія).
	•	Changes by Team (дошка/групування за Team).
	•	Recent Changes (Last 30 Days) (фільтр по даті).
	•	By Sub‑team (групування за Sub‑team).
	7.	n8n (план інтеграції, без впроваджених кроків)
	•	Monthly Cleanup: видалення логів, старших за попередній календарний місяць.
	•	Weekly/Monthly Digest → Slack: агреговані апдейти за командами/проєктами/платформами.
	•	On‑Demand Q&A (LangChain у n8n): запити зі Slack з фільтрами по Date/Team/Sub‑team/Platform/Project поверх Service Log.

⸻

Project Status Change Log Database Schema

Database Information
	•	Database Name: Project Status Change Log
	•	Database URL: https://www.notion.so/d94056721a9b4a4fa836743010fafec7
	•	Data Source: collection://55fc4c6e-08dc-4c5c-abdc-32441fba8d65
	•	Purpose: Track status changes from the All Projects database via automation

Properties

Core Fields

Property	Type	Description
Log Entry	Title	The title/description of the log entry (primary field)
Date	Date	When the status change occurred
Automation Source	Checkbox	Whether this entry was created by automation

Project Information

Property	Type	Description
Project Link	Relation	One-way relation to All Projects database (collection://f6dd2c85-ab31-4ad8-b08e-11accd21f73a)
Project Name	Text	Name of the project for easy reference
Version	Text	Version number of the project
Platform	Select	Target platform (GP, AMZ, iOS, Fire TV)
Release Type	Select	Type of release (CTR Setting Test, First Release, Update, Full Game, A/B Test, Remote A/B Test, Remote Update Subscription, Re-build)

Status Tracking

Property	Type	Description
Previous Status	Status	Project status before the change
New Status	Status	Project status after the change

Status Options (Both Previous & New Status)

To Do Group:
	•	BACKLOG

In Progress Group:
	•	GD CTR TEST
	•	CTR TEST
	•	CTR TEST DONE
	•	CTR ARCHIVE
	•	WAITING FOR DEV
	•	DEVELOPMENT
	•	QA
	•	WAITING RELEASE
	•	RELEASE POOL

Complete Group:
	•	CREO PRODUCTION
	•	CREO DONE
	•	UA TOP SPENDERRS
	•	LIVE
	•	UA TEST
	•	UA BOOST
	•	UA SETUP
	•	UA
	•	AUTO UA
	•	PAUSED
	•	UA PAUSED
	•	SHADOW BAN
	•	BLOCKED
	•	ARCHIVE
	•	SUSPENDED
	•	REJECTED
	•	Complete

Team & Organization

Property	Type	Description
Team	Select	Team associated with the project (AMZ Production Team, AMZ Integration and Port Team, AMZ Growth Team, Tools Team)
Sub-team	Select	Sub-team within the organization (25+ options including Growth, KHACHAPURI, FUJI, etc.)
Changed By	Person	Who made the status change

Additional Details

Property	Type	Description
What’s New	Text	Description of what changed or notes about the update

Views Available
	1.	All Log Entries - Main table view with all fields, sorted by date descending
	2.	Status Changes Timeline - Timeline view for chronological visualization
	3.	Changes by Team - Board view grouped by team
	4.	Recent Changes - Filtered to show last 30 days only
	5.	By Sub-team - Table grouped by sub-team for performance analysis

Database Usage

This database is designed to be populated by automation that monitors the All Projects database (https://www.notion.so/ce823eac36804227b10d43a2127b0289) for status changes and creates corresponding log entries for tracking and analysis purposes.