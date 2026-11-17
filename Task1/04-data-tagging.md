# 4. Механизм тегирования данных

## 4.1. Зачем

Тег — это машиночитаемая метка на поле, таблице, документе, топике или параметре API, по которой
автоматика (а не человек) решает: кому показать, что замаскировать, куда можно передать, когда удалить,
где искать при запросе субъекта. Теги закрывают R-06, R-07, R-11, R-15 и являются фундаментом для
целевого состояния «релиз проверяется автоматически на работу с тегированными данными».

## 4.2. Таксономия

Тег состоит из **категории** (что это за данные) и **атрибутов** (как с ними обращаться).
Категории — иерархические, в нотации `pii.med`, чтобы политика на `pii` применялась ко всем дочерним.

| Категория | Описание | Уровень чувствительности по умолчанию |
|---|---|---|
| `pii.basic` | ФИО, дата рождения, пол | confidential |
| `pii.contact` | телефон, e-mail, адрес | confidential |
| `pii.id` | паспорт, СНИЛС, ИНН, полис | restricted |
| `pii.social` | место работы/учёбы, семейное положение | confidential |
| `pii.med` | любые сведения о здоровье (спец. категория, врачебная тайна) | restricted |
| `pii.employee` | ПДн сотрудника (кадровый контекст) | confidential |
| `pii.minor` | данные несовершеннолетнего / законного представителя | restricted |
| `fin` | суммы, платежи, реквизиты; `fin.card` — платёжные карты (не хранить) | confidential |
| `biz` | коммерческая информация без ПДн | internal |
| `audit` | журналы доступа | restricted, неизменяемые |
| `public` | открытые данные (прайс, расписание специалистов без ПДн) | public |

Атрибуты (ключ=значение), обязательные для `pii.*`:

| Атрибут | Значения | Назначение |
|---|---|---|
| `subject` | `patient`, `employee`, `representative`, `contractor` | чей это субъект ПДн |
| `legal_basis` | `consent`, `contract`, `law`, `medical` (ст. 10 ч. 2 п. 4 152-ФЗ) | основание обработки |
| `retention` | класс: `med-25y`, `contract-5y`, `fin-5y`, `hr-50y`, `consent` (до отзыва), `session` | срок и триггер удаления |
| `protection` | `encrypt-column`, `encrypt-volume`, `hash-index`, `mask:phone`, `pseudonymize` | требуемая техническая мера |
| `residency` | `ru` | локализация (152-ФЗ ст. 18 ч. 5) |
| `domain` | `identity`, `clinical`, `billing`, `hr`, `analytics` | владеющий домен; `pii.basic/contact/id` допустимы только в `identity` |
| `owner` | роль владельца данных | кто утверждает изменения |

Пример полного тега: `pii.med; subject=patient; legal_basis=medical; retention=med-25y; protection=pseudonymize; domain=clinical; owner=chief-doctor`.

## 4.3. Где теги живут (слои)

Принцип: **один источник истины — каталог данных**, остальные слои синхронизируются с ним и
проверяются на расхождение.

```
                 ┌────────────────────────────┐
                 │  Каталог данных OpenMetadata │  ← источник истины: классификации, глоссарий,
                 │  (теги, владельцы, lineage)  │     lineage из Airflow/dbt/Kafka, PII-классификатор
                 └──────┬───────────┬──────────┘
        sync / policy   │           │  lineage, scan
   ┌────────────────────┼───────────┼─────────────────────┬──────────────────┐
   ▼                    ▼           ▼                     ▼                  ▼
PostgreSQL          OpenAPI /     Java-код             Kafka Schema      S3 / файлы
COMMENT, SECURITY   x-data-       @Sensitive,          Registry          object tags,
LABEL, RLS,         classification логгер-фильтр       field props       MIP-метки
pg_anon маски       → CI-проверка  → маска в логах      → ACL топиков     → DLP
```

### 4.3.1. Каталог данных (OpenMetadata)

* Классификация `Medikamente` с тегами из таксономии; атрибуты — как свойства тега.
* Автообнаружение: профилировщик + PII-классификатор по именам колонок и образцам значений
  (регулярные выражения для телефона, СНИЛС, паспорта; словарь МКБ для `pii.med`). Найденное
  без тега — задача владельцу домена.
* Lineage: ingestion из PostgreSQL, ClickHouse, Airflow, Kafka; тег **наследуется по lineage** —
  колонка витрины, построенная из `pii.med`, получает `pii.med`, пока не доказано обезличивание
  (явный тег `anonymized=true`, выставляемый ETL-шагом с k-анонимностью).
* API каталога используется CI-проверками и сервисом политик.

### 4.3.2. PostgreSQL

```sql
-- комментарий-тег (машиночитаемый JSON), читается каталогом и миграциями
COMMENT ON COLUMN identity.patient.phone IS
  '{"tag":"pii.contact","subject":"patient","legal_basis":"consent",
    "retention":"consent","protection":"encrypt-column,hash-index","domain":"identity"}';

-- маскирование по роли через PostgreSQL Anonymizer (pg_anon)
SECURITY LABEL FOR anon ON COLUMN identity.patient.phone
  IS 'MASKED WITH FUNCTION anon.partial(phone, 2, $$*******$$, 2)';
SECURITY LABEL FOR anon ON ROLE analyst IS 'MASKED';

-- запрет прямых идентификаторов вне домена identity (проверка в миграциях)
-- CI падает, если в схеме clinical.* появилась колонка с тегом pii.basic/pii.contact/pii.id

-- row-level security: врач видит только своих пациентов
ALTER TABLE clinical.encounter ENABLE ROW LEVEL SECURITY;
CREATE POLICY doctor_own ON clinical.encounter
  USING (doctor_id = current_setting('app.user_id')::uuid
         OR current_setting('app.role') = 'chief-doctor');
```

### 4.3.3. Код и API

```java
// Java: аннотация читается Jackson-фильтром логов и сериализатором ответов
public record Patient(
    UUID id,
    @Sensitive(tag = "pii.basic") String fullName,
    @Sensitive(tag = "pii.contact", mask = Mask.PHONE) String phone,
    @Sensitive(tag = "pii.id", mask = Mask.LAST4) String passport) {}
```

```yaml
# OpenAPI: расширение x-data-classification проверяется в CI (C-19)
components:
  schemas:
    LabOrder:
      properties:
        orderId:   { type: string, x-data-classification: public }
        sex:       { type: string, x-data-classification: pii.basic, x-anonymized: true }
        ageYears:  { type: integer, x-data-classification: pii.basic, x-anonymized: true }
        testCode:  { type: string, x-data-classification: pii.med }
# правило: схема, отдаваемая внешнему клиенту (tag: partner), не может содержать
# pii.basic/pii.contact/pii.id без x-anonymized и pii.med без явного consent-scope
```

* Kafka: в Schema Registry поля помечаются свойством `classification`; ACL топиков с `pii.med`
  выдаются только сервисам домена Clinical; Kafka Connect в ClickHouse проходит через SMT-маскирование.
* ClickHouse: `COMMENT` на колонках + row policies; витрины без тега `anonymized=true` недоступны роли `analyst`.

### 4.3.4. Файлы и документы

* Объектное хранилище (S3-совместимое): object tags `tag=pii.med`, `patient_id=…`, `retention=med-25y`;
  lifecycle-политики и DLP читают теги.
* Офисные документы в Windows-среде: метки конфиденциальности (sensitivity labels) с теми же именами;
  DLP блокирует отправку наружу и копирование на USB файлов с меткой `restricted`.
* Бумага: штамп категории на бланке и запись в журнале носителей (ПП 687).

### 4.3.5. Журналы и телеметрия

* Логгер-фильтр по аннотациям маскирует значения до записи; Elastic ingest pipeline — вторая линия
  (regex на телефон/СНИЛС/паспорт) с алертом «тегированное значение в логе» (C-06).

## 4.4. Политики, управляемые тегами

| Тег / атрибут | Политика доступа (OPA / Keycloak) | Маскирование | Передача | Хранение и удаление |
|---|---|---|---|---|
| `pii.med` | роли Doctor (ABAC: лечащий/направивший), Chief-doctor, пациент (свои); остальным — deny | полное скрытие | за контур — запрет; партнёрам — только через контракт с `x-anonymized` или consent-scope | `med-25y`; по отзыву согласия — ограничение обработки |
| `pii.id` | Reception при заключении договора, HR для сотрудников; каждое раскрытие журналируется | last-4 | запрет | `contract-5y`, сканы — до сверки |
| `pii.contact` | Reception, Cashier, сервис уведомлений | partial | ОФД — только при согласии на электронный чек | `consent` |
| `pii.basic` | Reception, Doctor, Cashier | инициалы вне Identity | партнёрам — нет | по договору |
| `domain=analytics` без `anonymized=true` | deny для Analyst | — | — | — |
| `audit` | Security officer | — | — | WORM, ≥ 3 лет |

## 4.5. Процесс

1. **Назначение.** Владелец домена ставит тег при проектировании (схема БД, OpenAPI, Avro). Миграция/PR без тегов на новых колонках не проходит ревью.
2. **Проверка.** CI: линтер схем и OpenAPI; контрактные тесты «внешний эндпоинт не возвращает поля с запрещённым тегом»; тест «в логах нет значений тегированных полей».
3. **Обнаружение.** Еженедельный скан OpenMetadata по всем источникам; расхождение «в данных есть ПДн, тега нет» → инцидент владельцу.
4. **Эксплуатация.** Политики OPA, маски pg_anon, lifecycle-правила и DLP читают теги из каталога; SIEM коррелирует доступ к `restricted` с ролями и временем (нетипичные действия).
5. **Запрос субъекта.** По `patient_id` каталог через lineage выдаёт все места хранения; job удаления/ограничения проходит по ним и отчитывается.

## 4.6. Инструменты

| Задача | Инструмент | Почему |
|---|---|---|
| Каталог, классификация, lineage | **OpenMetadata** (альтернатива — DataHub) | open source, коннекторы к PostgreSQL/ClickHouse/Kafka/Airflow, встроенный PII-классификатор, API для CI; разворачивается в Kubernetes из стека CTO |
| Маскирование и теги в PostgreSQL | **PostgreSQL Anonymizer (pg_anon)**, `SECURITY LABEL`, RLS | декларативно, без изменения приложения |
| Политики доступа по тегам | **OPA / Keycloak Authorization Services** | ABAC-правила вынесены из кода, одна точка решений для API и BI |
| Автообнаружение ПДн в текстах и файлах | **Microsoft Presidio** (regex + NER, русский язык через spaCy) | сканы, заключения, письма |
| Контракты API | **OpenAPI + Spectral** (кастомные правила на `x-data-classification`) | проверка в CI |
| Файлы, DLP | метки конфиденциальности + отечественная DLP (InfoWatch / SearchInform / Solar Dozor) | сертифицированы ФСТЭК, работают с Exchange и общим диском |
| Ключи | **HashiCorp Vault / KMS** с ГОСТ-СКЗИ там, где требуется ФСБ 378 | ротация, per-patient ключи для crypto-shredding |
