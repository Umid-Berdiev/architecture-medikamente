"""Generate the Task 2 target-state C4 diagrams (system context and container) as draw.io files.

    python3 tools/diagram/gen_c4.py Task2

Colour code (see legend on each page): blue — domain/functional containers, green — Privacy by Design
blocks, purple — analytics layer, grey — existing (legacy) and external systems. The yellow "MVP"
badge marks what is needed for the intermediate state (self-service booking visible to reception).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from c4_lib import C4Diagram  # noqa: E402

OUT = sys.argv[1] if len(sys.argv) > 1 else "Task2"
os.makedirs(OUT, exist_ok=True)

LEGEND = ("<b>Легенда.</b> Синий — функциональные системы/контейнеры; <font color='#2E8B57'><b>зелёный</b></font> — "
          "новые блоки Privacy by Design; <font color='#7B5EA7'><b>фиолетовый</b></font> — аналитический слой; "
          "серый — внешние и унаследованные системы; тёмно-синий человек — сотрудник, серый — внешний пользователь. "
          "Жёлтая метка <b>MVP</b> — блок нужен уже для промежуточного состояния (самостоятельная запись через портал, "
          "видимая ресепшену); пунктирная связь — планируется после MVP.")


# ============================================================================ context
def context():
    d = C4Diagram()
    p = d.page("context")
    p.title("TO-BE: Диаграмма контекста C4 — «Медикаменте»", w=1500)
    p.text("<i>Целевое состояние (горизонт 12 месяцев). Privacy by Design: границы доверия, минимальные контракты, "
           "единая платформа безопасности и приватности, аналитика только на обезличенных данных.</i>", 20, 42, 1500, 20)

    # people
    p.person("pat", "Пациент", "Запись, ЛК, свои документы; законный представитель — от имени ребёнка",
             40, 300, external=True)
    p.person("rec", "Администратор ресепшена", "Регистрация, запись, напоминания", 480, 90)
    p.person("doc", "Врач", "Приём, медкарта, направления", 760, 90)
    p.person("cash", "Кассир", "Оплата услуг, договоры", 1040, 90)
    p.person("acc", "Бухгалтер", "Платежи, зарплата, кадры", 60, 700)
    p.person("sec", "Офицер безопасности (ответственный за ПДн)", "Политики, аудит, запросы субъектов, инциденты",
             700, 1300)
    p.person("ana", "Бизнес-аналитик / DS", "BI, ML — только обезличенные данные", 1360, 1310)

    # core and supporting internal systems
    p.system("core", "Платформа «Медикаменте»",
             "ЛК и запись, портал ресепшена и врача, медкарта, оплата, CRM, интеграции. Домены Identity / Clinical / "
             "Billing, теги данных, согласия", 700, 400, w=320, h=170, badge="MVP")
    p.system("priv", "Платформа безопасности и приватности",
             "SSO + MFA, политики доступа по тегам (ABAC), согласия, каталог данных и lineage, KMS, аудит и SIEM, "
             "DLP, запросы субъектов и удаление", 700, 800, w=320, h=150, kind="privacy", badge="MVP")
    p.system("dl", "Аналитическая платформа",
             "Data Lake (raw / curated), конвейер обезличивания, витрины ClickHouse, BI, JupyterHub / ML, "
             "LLM на обезличенных данных", 1200, 1080, w=320, h=150, kind="analytics")

    # legacy
    p.system("c1", "1С:Бухгалтерия предприятия", "Клиент-серверный режим (PostgreSQL), роли, аудит", 60, 940,
             kind="legacy", badge="MVP")
    p.system("c2", "1С:Торговля и склад", "Клиент-серверный режим, учёт ТМЦ", 60, 1120, kind="legacy")
    p.system("kkm", "ККМ", "Контрольно-кассовая машина", 380, 1300, kind="legacy")
    p.system("corp", "Корпоративные сервисы: AD, Exchange", "Учётные записи, служебная почта за DLP-шлюзом",
             1000, 1300, kind="legacy")

    # external
    p.system("lab", "Лаборатория анализов", "Внешняя организация, API-партнёр", 1650, 300, external=True, badge="MVP")
    p.system("prt", "Партнёры: ДМС, клиники", "Планируется; тот же контракт по тегам", 1650, 460, external=True)
    p.system("pay", "Платёжный провайдер / банк-эквайер", "Онлайн-оплата, POS; карта не хранится", 1650, 620,
             external=True)
    p.system("ntf", "Провайдер уведомлений", "SMS, push, голосовой робот", 1650, 780, external=True, badge="MVP")
    p.system("egisz", "ЕГИСЗ (РЭМД, ФРМО)", "Планируется: обязательные мед. сведения", 1650, 940, external=True)
    p.system("ofd", "ОФД → ФНС", "Фискальные данные чеков", 380, 1480, external=True)
    p.system("gov", "ФНС, СФР", "Налоговая и кадровая отчётность", 380, 1120, external=True)

    # relationships: people
    p.rel("pat", "core", "Запись, подтверждение/отмена, ЛК: только свои данные", "HTTPS/TLS 1.3, OIDC + MFA",
          exit_=(1, 0.5), entry=(0, 0.5))
    p.rel("rec", "core", "Регистрация, запись, напоминания; ПДн маскированы", "HTTPS, SSO, роль Reception",
          exit_=(0.5, 1), entry=(0.15, 0), lab=(-0.8, 0))
    p.rel("doc", "core", "Медкарта только своих пациентов", "HTTPS, SSO, ABAC «лечащий врач»",
          exit_=(0.5, 1), entry=(0.5, 0))
    p.rel("cash", "core", "Оплата, договоры, чек", "HTTPS, SSO, роль Cashier", exit_=(0.5, 1), entry=(0.85, 0),
          lab=(-0.7, 0))
    p.rel("acc", "c1", "Учёт, зарплата, кадры", "1С-клиент, SSO, роли 1С", exit_=(0.5, 1), entry=(0.5, 0))
    p.rel("sec", "priv", "Политики, расследования, запросы субъектов, уведомления РКН", "HTTPS, SSO, PAM",
          exit_=(0.5, 0), entry=(0.3, 1))
    p.rel("ana", "dl", "Запросы к витринам, ноутбуки внутри контура", "HTTPS, SSO, роль Analyst",
          exit_=(0.5, 0), entry=(0.8, 1))

    # relationships: internal platforms
    p.rel("core", "priv", "Аутентификация, авторизация по тегам, согласия, ключи, события аудита",
          "OIDC/OAuth2, OPA, mTLS", exit_=(0.5, 1), entry=(0.5, 0))
    p.rel("core", "dl", "События домена и CDC: patient_id вместо ФИО, теги в схемах", "Kafka, mTLS",
          exit_=(1, 0.9), entry=(0, 0.3), points=[(1100, 553), (1100, 1125)], lab=(0.3, 0))
    p.rel("dl", "priv", "Политики доступа, lineage, ключи псевдонимизации", "mTLS", exit_=(0, 0.7), entry=(1, 0.8),
          points=[(1060, 1185), (1060, 920)], lab=(-0.3, 0))
    p.rel("priv", "corp", "Федерация учётных записей; DLP на почте", "LDAPS, SMTP-коннектор", exit_=(0.8, 1),
          entry=(0.5, 0), points=[(956, 1260), (1120, 1260)], lab=(0.8, 0))

    # relationships: legacy
    p.rel("core", "c1", "Платежи и договоры: patient_id, код услуги, сумма", "веб-сервисы 1С, TLS",
          exit_=(0, 0.6), entry=(1, 0.5), points=[(640, 502), (640, 1000)], lab=(0.6, 0))
    p.rel("core", "kkm", "Фискализация: обобщённое наименование услуги", "TLS", exit_=(0, 0.9), entry=(0.5, 0),
          points=[(660, 553), (660, 1270), (500, 1270)], lab=(0.9, 0))
    p.rel("kkm", "ofd", "Фискальные данные чека", "протокол ОФД, TLS", exit_=(0.5, 1), entry=(0.5, 0))
    p.rel("c1", "c2", "Взаиморасчёты, документы ТМЦ", "веб-сервисы, TLS", exit_=(0.5, 1), entry=(0.5, 0))
    p.rel("c1", "gov", "Отчётность с ПДн сотрудников", "ЭДО, КЭП", exit_=(1, 0.75), entry=(0.5, 0),
          points=[(500, 1030)])

    # relationships: external
    p.rel("core", "lab", "Заказы и результаты без ФИО: order_id, пол, возраст, код", "REST/JSON, mTLS, OAuth2",
          exit_=(1, 0.1), entry=(0, 0.5), points=[(1150, 417), (1150, 360)], lab=(0.45, 0))
    p.rel("core", "prt", "API по контракту с тегами, с согласия пациента", "REST, mTLS, OAuth2",
          exit_=(1, 0.3), entry=(0, 0.5), dashed=True, points=[(1190, 451), (1190, 520)], lab=(0.6, 0))
    p.rel("core", "pay", "Оплата: токен платежа, карта не хранится", "HTTPS, 3-D Secure",
          exit_=(1, 0.5), entry=(0, 0.5), points=[(1230, 485), (1230, 680)], lab=(0.6, 0))
    p.rel("core", "ntf", "Напоминания: шаблоны без мед. сведений", "HTTPS/TLS",
          exit_=(1, 0.7), entry=(0, 0.5), points=[(1270, 519), (1270, 840)], lab=(0.6, 0))
    p.rel("core", "egisz", "Мед. документы, подписанные КЭП", "СМЭВ / веб-сервисы, КЭП",
          exit_=(1, 0.8), entry=(0, 0.5), dashed=True, points=[(1310, 536), (1310, 1000)], lab=(0.6, 0))

    p.text(LEGEND, 20, 1640, 1500, 60)
    d.write(os.path.join(OUT, "Medikamente_C4_context_to-be.drawio"))
    print("context written")


context()

# ============================================================================ container
def container():
    d = C4Diagram()
    p = d.page("container")
    p.title("TO-BE: Диаграмма контейнеров C4 — Платформа «Медикаменте», платформа приватности и аналитический слой",
            w=2000)
    p.text("<i>Целевое состояние. Зелёные контейнеры — новые блоки Privacy by Design, которые обслуживают все "
           "доменные сервисы; фиолетовые — аналитический слой, работающий только с псевдонимизированными и "
           "обезличенными данными.</i>", 20, 42, 2000, 20)

    # ---- people
    p.person("pat", "Пациент", "Моб. приложение и ЛК: запись, подтверждение, свои документы", 380, 60, external=True)
    p.person("rec", "Администратор ресепшена", "Портал сотрудника, роль Reception", 700, 60)
    p.person("doc", "Врач", "Портал сотрудника, роль Doctor", 940, 60)
    p.person("cash", "Кассир", "Рабочее место кассы, роль Cashier", 1180, 60)
    p.person("sec", "Офицер безопасности", "Ответственный за ПДн: политики, аудит, запросы субъектов", 1800, 60)
    p.person("acc", "Бухгалтер", "Работает в 1С, роли 1С", 1300, 1480)
    p.person("ana", "Бизнес-аналитик / DS", "Только обезличенные витрины и ноутбуки внутри контура", 2020, 2120)

    # ---- channels
    p.boundary("b_ch", "Каналы", "Container boundary", 360, 280, 1180, 200)
    p.container("mob", "Мобильное приложение", "iOS / Android", "ЛК пациента: только свои данные; биометрия устройства, "
                "push-подтверждения", 380, 320, w=210, h=100, kind="channel")
    p.container("web", "Портал пациента", "SPA, TypeScript", "Запись, ЛК, документы по защищённой ссылке", 620, 320,
                w=210, h=100, kind="channel", badge="MVP")
    p.container("staff", "Портал сотрудника", "SPA, TypeScript", "Ресепшен и врач; маскирование по роли, «раскрыть» "
                "журналируется", 860, 320, w=210, h=100, kind="channel", badge="MVP")
    p.container("pos", "Рабочее место кассы", "SPA + POS", "Оплата, договоры; карта не касается системы", 1100, 320,
                w=210, h=100, kind="channel")
    p.container("api", "API Gateway + WAF", "Kong / APISIX", "Единая точка входа: OAuth2/OIDC, mTLS для партнёров, "
                "схемная валидация, rate limit, фильтрация ответов по тегам, журнал запросов", 380, 530, w=930, h=80,
                kind="privacy", badge="MVP")

    # ---- core domain services
    p.boundary("b_core", "Платформа «Медикаменте» — доменные сервисы", "Software System", 360, 650, 1180, 700)
    cols = [380, 610, 840, 1070, 1300]
    p.container("idn", "Identity Service", "Java, Spring Boot", "Реестр пациентов и сотрудников-субъектов: ФИО, паспорт, "
                "контакты. Токенизация: выдаёт patient_id, единственный владелец прямых идентификаторов", cols[0], 690,
                w=210, h=120, badge="MVP")
    p.container("sch", "Scheduling Service", "Java, Spring Boot", "Расписание, записи, подтверждения, напоминания. "
                "Хранит patient_id и код услуги, без повода обращения", cols[1], 690, w=210, h=120, badge="MVP")
    p.container("cli", "Clinical Records Service", "Java, Spring Boot", "Медкарта: приёмы, диагнозы, заключения, "
                "направления и результаты (order_id). ABAC «лечащий врач»", cols[2], 690, w=210, h=120)
    p.container("bil", "Billing Service", "Java, Spring Boot", "Договоры, услуги, платежи по patient_id; обобщённое "
                "наименование услуги для чека", cols[3], 690, w=210, h=120)
    p.container("crm", "CRM Service", "Java, Spring Boot", "Коммуникации и история взаимодействий по patient_id; "
                "только при согласии на коммуникации", cols[4], 690, w=210, h=120)
    p.container("idn_db", "Identity DB", "PostgreSQL", "Шифрование колонок, HMAC-индексы, RLS, pgaudit", cols[0] + 30, 850, w=150, h=120, db=True, badge="MVP")
    p.container("sch_db", "Scheduling DB", "PostgreSQL", "patient_id, врач, время, код услуги", cols[1] + 30, 850,
                w=150, h=120, db=True, badge="MVP")
    p.container("cli_db", "Clinical DB + документы", "PostgreSQL + S3", "Без ФИО; документы в S3 с SSE-KMS, тег pii.med", cols[2] + 30, 850, w=150, h=120, db=True)
    p.container("bil_db", "Billing DB", "PostgreSQL", "Платежи, договоры; тег fin", cols[3] + 30, 850, w=150, h=120,
                db=True)
    p.container("crm_db", "CRM DB", "PostgreSQL", "Согласия на коммуникации, история", cols[4] + 30, 850, w=150,
                h=120, db=True)
    p.container("kafka", "Шина событий", "Apache Kafka + Schema Registry", "События домена с patient_id; теги в схемах "
                "Avro; ACL на топики с pii.med; mTLS", 380, 1030, w=1130, h=70, badge="MVP")
    p.container("lab", "Lab Integration Service", "Java, Spring Boot", "Заказы и результаты анализов: order_id, пол, "
                "возраст, код исследования; валидация схем, подпись результатов", cols[0], 1150, w=210, h=120)
    p.container("ntf", "Notification Service", "Java, Spring Boot", "SMS / push / голосовой робот по шаблонам без мед. "
                "сведений; подтверждение/отмена записи; проверка согласия", cols[1], 1150, w=210, h=120, badge="MVP")
    p.container("payad", "Payment & Fiscal Adapter", "Java, Spring Boot", "Эквайринг по токену, фискализация через ККМ "
                "с обобщённым наименованием услуги", cols[2], 1150, w=210, h=120)
    p.container("docs", "Document Service", "Java, Spring Boot", "Генерация договоров и заключений (PDF), подпись КЭП, "
                "водяные знаки, учёт печати и выдачи", cols[3], 1150, w=210, h=120)
    p.container("c1ad", "1С Adapter", "Java, Spring Boot", "Передача платежей и договоров в 1С по patient_id; "
                "обратный поток статусов", cols[4], 1150, w=210, h=120)

    # ---- privacy platform
    p.boundary("b_priv", "Платформа безопасности и приватности (сквозные блоки Privacy by Design)", "Software System",
               1700, 280, 560, 1020, stroke="#2E8B57")
    P = dict(kind="privacy", w=240, h=130)
    L, R = 1720, 1990
    p.container("iam", "IAM / SSO", "Keycloak + AD federation", "OIDC/OAuth2, MFA для всех, роли и атрибуты в токене, "
                "сессии, PAM-интеграция", L, 320, badge="MVP", **P)
    p.container("cons", "Consent Service", "Java + PostgreSQL", "Согласия по целям и категориям, версии, отзыв; "
                "проверяется сервисами перед обработкой", R, 320, badge="MVP", **P)
    p.container("pdp", "Policy Decision Point", "OPA", "ABAC-политики по ролям, атрибутам и тегам данных; одна точка "
                "решений для API, BI и витрин. Политики по тегам — из каталога", L, 480, badge="MVP", **P)
    p.container("cat", "Каталог данных и теги", "OpenMetadata", "Классификация pii.*, lineage, владельцы, "
                "retention; источник истины для политик и CI", R, 480, badge="MVP", **P)
    p.container("kms", "KMS / Secrets", "HashiCorp Vault", "Ключи шифрования колонок и документов, per-patient DEK, "
                "ключи псевдонимизации, ротация, crypto-shredding", L, 640, badge="MVP", **P)
    p.container("siem", "Аудит и SIEM", "Elastic / OpenSearch + правила", "Неизменяемый журнал доступа к тегированным "
                "данным, корреляция, UEBA-правила, алерты, уведомление об инциденте", R, 640, badge="MVP", **P)
    p.container("dsar", "Запросы субъектов и retention", "Java + Airflow jobs", "Доступ, исправление, ограничение, "
                "удаление по lineage; сроки хранения по тегам", L, 800, **P)
    p.container("dlp", "DLP + VDI", "DLP-шлюз, VDI", "Блокировка вывода restricted-данных: почта, USB, печать; "
                "рабочие места без локальных копий", R, 800, **P)
    p.container("ci", "Privacy Gate в CI/CD", "GitLab CI + Spectral + контрактные тесты", "Проверка схем и OpenAPI на "
                "теги из каталога, BOLA-тесты, SAST/DAST; релиз блокируется", L, 960, **P)
    p.container("mon", "Мониторинг и алертинг", "Victoria Metrics + Alertmanager", "Метрики безопасности и "
                "приватности, SLO, алерты в дежурную смену", R, 960, **P)
    p.container("pam", "PAM", "Teleport / аналог", "Привилегированный доступ администраторов: JIT-права, запись "
                "сессий, разделение обязанностей", L, 1120, **P)

    # ---- legacy
    p.boundary("b_leg", "Корпоративная инфраструктура", "Existing systems", 2320, 280, 280, 700)
    p.container("ad", "Active Directory", "Windows Server", "Учётные записи сотрудников; федерация в IAM", 2340, 320,
                w=240, h=130, kind="legacy", badge="MVP")
    p.container("exch", "Exchange", "Mail server", "Служебная почта за DLP-шлюзом; без вложений с ПДн", 2340, 800,
                w=240, h=130, kind="legacy")

    # ---- external and legacy at the bottom
    p.system("x_lab", "Лаборатория анализов", "Внешний API-партнёр", cols[0], 1720, w=210, h=110, external=True)
    p.system("x_ntf", "Провайдер уведомлений", "SMS, push, голосовой робот", cols[1], 1720, w=210, h=110,
             external=True)
    p.system("x_pay", "Платёжный провайдер", "Эквайринг, 3-D Secure", cols[2], 1720, w=210, h=110, external=True)
    p.system("kkm", "ККМ", "Фискальный регистратор", cols[3], 1720, w=210, h=110, kind="legacy")
    p.system("c1", "1С:Бухгалтерия", "Клиент-сервер, PostgreSQL", cols[4], 1720, w=210, h=110, kind="legacy",
             badge="MVP")
    p.system("ofd", "ОФД → ФНС", "Фискальные данные", cols[3], 1880, w=210, h=110, external=True)
    p.system("c2", "1С:Торговля и склад", "Клиент-сервер", cols[4], 1880, w=210, h=110, kind="legacy")

    # ---- analytics layer
    p.boundary("b_an", "Аналитическая платформа (Privacy by Design: raw-зона закрыта, аналитика на обезличенных данных)",
               "Software System", 360, 2060, 1620, 420, stroke="#7B5EA7")
    A = dict(kind="analytics", w=220, h=120)
    p.container("ing", "Ingest / CDC", "Debezium, Kafka Connect", "Потоковая загрузка событий и CDC из БД доменов; "
                "patient_id, без прямых идентификаторов", 380, 2110, **A)
    p.container("raw", "Raw-зона озера", "S3, SSE-KMS", "Псевдонимизированные сырые данные; доступ только у конвейера; "
                "retention по тегам", 620, 2110, db=True, **A)
    p.container("anon", "Конвейер обезличивания", "Airflow + dbt + Presidio", "Обобщение, k-анонимность ≥ 5, "
                "l-разнообразие диагнозов, маскирование; ставит тег anonymized", 860, 2110, **A)
    p.container("cur", "Curated-зона озера", "S3 / Iceberg", "Обезличенные наборы для BI, ML и LLM; lineage в каталоге",
                1100, 2110, db=True, **A)
    p.container("marts", "Витрины", "ClickHouse", "Агрегаты и обезличенные детальные таблицы; row policies по роли",
                1340, 2110, db=True, **A)
    p.container("bi", "BI-портал", "Superset / DataLens", "P&L, ABC, загрузка врачей; доступ через PDP, без экспорта "
                "сырых данных", 1580, 2110, **A)
    p.container("ml", "Платформа ML и LLM", "JupyterHub, MLflow, локальная LLM (RAG)", "Ноутбуки и модели внутри "
                "контура; обучение и RAG только на curated-зоне; выгрузка на устройство запрещена", 1100, 2290, **A)
    p.container("dgw", "Шлюз доступа к данным", "Trino + OPA", "Единая точка SQL-доступа к витринам и curated-зоне: "
                "политики по тегам, маскирование на лету, журнал запросов", 1580, 2290, **A)

    # ---- relationships: people and channels
    p.rel("pat", "mob", "", "HTTPS, OIDC + MFA", exit_=(0.25, 1), entry=(0.5, 0))
    p.rel("pat", "web", "Запись, ЛК", "HTTPS, OIDC + MFA", exit_=(0.75, 1), entry=(0.5, 0))
    p.rel("rec", "staff", "", "HTTPS, SSO", exit_=(0.5, 1), entry=(0.3, 0))
    p.rel("doc", "staff", "Роли Reception / Doctor", "HTTPS, SSO", exit_=(0.5, 1), entry=(0.7, 0))
    p.rel("cash", "pos", "", "HTTPS, SSO", exit_=(0.5, 1), entry=(0.5, 0))
    for k in ("mob", "web", "staff", "pos"):
        p.rel(k, "api", "REST/JSON, access token" if k == "web" else "", "HTTPS" if k == "web" else "",
              exit_=(0.5, 1), entry=((cols[["mob", "web", "staff", "pos"].index(k)] + 105 - 380) / 930, 0))
    p.rel("api", "iam", "Проверка токена", "OIDC", exit_=(1, 0.3), entry=(0, 0.5))
    p.rel("api", "pdp", "Решение о доступе: роль, атрибуты, теги", "OPA REST", exit_=(1, 0.7), entry=(0, 0.5))
    p.rel("sec", "b_priv", "Политики, расследования, запросы субъектов", "HTTPS, SSO, PAM", exit_=(0.5, 1),
          entry=(0.3, 0))
    p.rel("acc", "c1", "Учёт, зарплата, кадры", "1С-клиент, SSO", exit_=(0.5, 1), entry=(0.5, 0))
    p.rel("ana", "bi", "Отчёты", "HTTPS, SSO", exit_=(0, 0.5), entry=(1, 0.5))
    p.rel("ana", "dgw", "Ноутбуки и SQL — только обезличенное", "HTTPS, SSO, роль Analyst", exit_=(0.5, 1),
          entry=(1, 0.5), points=[(2120, 2345)])

    # ---- relationships: gateway -> services, services -> stores -> bus
    for k, x in zip(("idn", "sch", "cli", "bil", "crm"), cols):
        p.rel("api", k, "mTLS" if k == "idn" else "", "gRPC / REST" if k == "idn" else "",
              exit_=((x + 105 - 380) / 930, 1), entry=(0.5, 0))
    p.rel("idn", "idn_db", "JDBC/TLS; шифрование колонок", "", exit_=(0.5, 1), entry=(0.5, 0))
    p.rel("sch", "sch_db", "", "", exit_=(0.5, 1), entry=(0.5, 0))
    p.rel("cli", "cli_db", "Без ФИО: patient_id", "", exit_=(0.5, 1), entry=(0.5, 0))
    p.rel("bil", "bil_db", "", "", exit_=(0.5, 1), entry=(0.5, 0))
    p.rel("crm", "crm_db", "", "", exit_=(0.5, 1), entry=(0.5, 0))
    for k, x in zip(("idn", "sch", "cli", "bil", "crm"), cols):
        p.rel(k, "kafka", "События домена: patient_id, теги в схемах" if k == "sch" else "",
              "Kafka, mTLS, ACL" if k == "sch" else "", exit_=(0.95, 1),
              entry=((x + 200 - 380) / 1130, 0), points=[(x + 200, 1000)], lab=(0.75, 0))
    for k, x in zip(("lab", "ntf", "payad", "docs", "c1ad"), cols):
        p.rel("kafka", k, "Команды и события" if k == "ntf" else "", "", exit_=((x + 105 - 380) / 1130, 1),
              entry=(0.5, 0))

    # ---- relationships: integrations
    p.rel("lab", "x_lab", "order_id, пол, возраст, код; результаты с подписью", "REST/JSON, mTLS, OAuth2",
          exit_=(0.5, 1), entry=(0.5, 0))
    p.rel("ntf", "x_ntf", "Шаблоны без мед. сведений", "HTTPS/TLS", exit_=(0.5, 1), entry=(0.5, 0))
    p.rel("payad", "x_pay", "Токен платежа", "HTTPS, 3-D Secure", exit_=(0.3, 1), entry=(0.5, 0),
          points=[(903, 1600), (945, 1600)])
    p.rel("payad", "kkm", "Чек: обобщённое наименование", "TLS", exit_=(0.8, 1), entry=(0.5, 0),
          points=[(1008, 1640), (1175, 1640)])
    p.rel("kkm", "ofd", "Фискальные данные", "протокол ОФД", exit_=(0.5, 1), entry=(0.5, 0))
    p.rel("c1ad", "c1", "Платежи, договоры по patient_id", "веб-сервисы 1С, TLS", exit_=(0.5, 1), entry=(0.5, 0))
    p.rel("c1", "c2", "Взаиморасчёты", "веб-сервисы", exit_=(0.5, 1), entry=(0.5, 0))

    # ---- relationships: core <-> privacy platform (drawn from the boundary: applies to every service)
    p.rel("b_core", "cons", "Согласия", "gRPC, mTLS", exit_=(1, 0.08), entry=(0.3, 1),
          points=[(1620, 706), (1620, 465), (2062, 465)], lab=(-0.3, 0))
    p.rel("b_core", "kms", "Ключи", "Vault API, mTLS", exit_=(1, 0.2), entry=(0, 0.5))
    p.rel("b_core", "siem", "Аудит", "OTLP, mTLS", exit_=(1, 0.33), entry=(0.3, 1),
          points=[(1640, 881), (1640, 785), (2062, 785)], lab=(-0.6, 0))
    p.rel("cat", "b_core", "Теги, lineage", "JDBC, Kafka", exit_=(0.2, 1), entry=(1, 0.45), dashed=True,
          points=[(2038, 625), (1660, 625), (1660, 965)], lab=(0.3, 0))
    p.rel("pdp", "cat", "", "", exit_=(1, 0.5), entry=(0, 0.5))
    p.rel("dsar", "kms", "Crypto-shredding", "", exit_=(0.5, 0), entry=(0.5, 1))
    p.rel("ci", "cat", "", "", exit_=(1, 0.5), entry=(1, 0.5), points=[(2250, 1025), (2250, 545)])
    p.rel("ad", "iam", "Федерация учётных записей", "LDAPS", exit_=(0.5, 0), entry=(0.5, 0),
          points=[(2460, 255), (1840, 255)], lab=(-0.7, 0))
    p.rel("exch", "dlp", "Вложения", "SMTP", exit_=(0, 0.5), entry=(1, 0.5))

    # ---- relationships: analytics
    p.rel("kafka", "ing", "CDC и события: patient_id, теги; без прямых идентификаторов", "Kafka Connect, mTLS",
          exit_=(1, 0.5), entry=(0.5, 0), points=[(1570, 1065), (1570, 2020), (490, 2020)], lab=(0.6, 0))
    p.rel("ing", "raw", "", "", exit_=(1, 0.5), entry=(0, 0.5))
    p.rel("raw", "anon", "Только конвейер", "", exit_=(1, 0.5), entry=(0, 0.5))
    p.rel("anon", "cur", "anonymized=true", "", exit_=(1, 0.5), entry=(0, 0.5))
    p.rel("cur", "marts", "", "", exit_=(1, 0.5), entry=(0, 0.5))
    p.rel("marts", "bi", "", "", exit_=(1, 0.5), entry=(0, 0.5))
    p.rel("cur", "ml", "Обучение, RAG", "", exit_=(0.5, 1), entry=(0.5, 0))
    p.rel("dgw", "marts", "SQL с маскированием", "", exit_=(0, 0.3), entry=(0.75, 1), points=[(1505, 2326)])
    p.rel("b_an", "b_priv", "Политики доступа по тегам, lineage, ключи псевдонимизации, аудит запросов", "mTLS",
          exit_=(0.95, 0), entry=(0.55, 1))

    p.text(LEGEND, 20, 2520, 2000, 60)
    d.write(os.path.join(OUT, "Medikamente_C4_container_to-be.drawio"))
    print("container written")


container()
