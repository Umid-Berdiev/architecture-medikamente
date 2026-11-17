"""Generate the Task 4 Ishikawa (fishbone) diagram of migration bottlenecks as a draw.io file.

    python3 tools/diagram/gen_ishikawa.py Task4

Layout: a horizontal spine ending in the effect box; seven category bones (four above, three below);
every primary cause is a horizontal tick on its bone with the cause text and its sub-causes.
"""
import html
import os
import sys
import xml.etree.ElementTree as ET
from xml.dom import minidom

OUT = sys.argv[1] if len(sys.argv) > 1 else "Task4"
os.makedirs(OUT, exist_ok=True)

EFFECT = ("Деградация производительности и доступности новой платформы «Медикаменте» в ходе и после миграции "
          "с файлового ландшафта (Excel, сканы, файловые базы 1С) на микросервисную платформу")

# (category, colour, [(cause, [sub-causes])])
CATEGORIES = [
    ("Инфраструктура", "#B85450", [
        ("Единственный физический сервер в офисе", ["нет ресурсов для параллельной работы старой и новой систем",
                                                  "нет горячего резерва и DR-площадки"]),
        ("Каналы связи офис ↔ площадка", ["узкая полоса и задержка до ЦОД/облака",
                                         "ГОСТ VPN-шлюзы ограничивают пропускную способность"]),
        ("Kubernetes без лимитов и автомасштабирования", ["шумные соседи, OOM-kill", "нет HPA и cluster autoscaler"]),
        ("Дисковая подсистема", ["медленные диски под PostgreSQL и Kafka",
                                 "шифрование томов без AES-NI, S3 на одном узле"]),
        ("Нет среды, идентичной продуктиву", ["нагрузочные тесты на «уменьшенной копии»",
                                             "сюрпризы при переключении"]),
        ("Резервное копирование и восстановление", ["восстановление занимает часы",
                                                     "бэкапы конкурируют за IOPS в рабочее время"]),
    ]),
    ("Данные и базы данных", "#D79B00", [
        ("Качество исходных данных Excel", ["дубликаты пациентов, разные форматы ФИО и дат",
                                            "пустые и «свободные» поля, ручная выверка"]),
        ("Объём и формат документов", ["тысячи сканов и PDF «любого формата»",
                                       "долгая загрузка в S3, OCR и классификация"]),
        ("Зашифрованные поля нельзя индексировать", ["поиск по ФИО/телефону только через HMAC",
                                                    "LIKE и сортировка по ПДн невозможны"]),
        ("Разделение доменов Identity / Clinical", ["нет JOIN между сервисами → N+1 вызовов",
                                                    "агрегаты собираются из нескольких БД"]),
        ("Конвертация файловых баз 1С", ["перевод в клиент-сервер, блокировки, регламентные операции"]),
        ("Двойная запись во время dual-run", ["расхождения Excel ↔ БД, конфликты правок", "нет эталона данных"]),
        ("Рост данных ×5", ["нет партиционирования, bloat и vacuum", "журнал аудита растёт быстрее данных"]),
    ]),
    ("Программное обеспечение и архитектура", "#0E7DAD", [
        ("Распределённый монолит", ["синхронные цепочки gateway → сервис → сервис",
                                    "каскадные таймауты, нет circuit breaker"]),
        ("«Болтливые» вызовы Identity", ["токенизация patient_id на каждый запрос",
                                        "нет кэша и пакетных операций"]),
        ("Нет идемпотентности и backpressure", ["retry storm при сбое", "дубли платежей и уведомлений"]),
        ("Service mesh и sidecar", ["задержка и CPU на mTLS в каждом поде", "неверные таймауты mesh"]),
        ("Kafka настроена по умолчанию", ["мало партиций, большие сообщения с документами",
                                          "consumer lag, нет exactly-once"]),
        ("Доступ к данным", ["N+1 в ORM, нет PgBouncer", "нет лимитов на выборки"]),
        ("Контракты API без версий", ["ломающие изменения во время миграции",
                                      "legacy OLE-обмен 1С остаётся в пути"]),
    ]),
    ("Интеграции", "#6C8EBF", [
        ("Лаборатория", ["партнёр не готов к API, свои форматы вместо FHIR", "нет SLA и тестового стенда"]),
        ("1С и ККМ", ["синхронные веб-сервисы 1С медленны", "адаптер ККМ — единая точка отказа"]),
        ("Провайдер уведомлений", ["лимиты отправки и блокировки", "нет очереди и повторов"]),
        ("Платёжный провайдер", ["таймауты 3-D Secure", "идемпотентность платежей не обеспечена"]),
        ("ЕГИСЗ, СМЭВ, ЭДО", ["ГОСТ TLS и подписи медленны", "ограничения по частоте запросов"]),
        ("AD и Keycloak", ["задержки аутентификации", "недоступность AD блокирует вход"]),
    ]),
    ("Персонал", "#82B366", [
        ("IT-отдел из трёх человек", ["нет опыта Kubernetes, Kafka, Vault в продуктиве", "нет DBA"]),
        ("Перегрузка во время dual-run", ["сотрудники ведут Excel и новую систему параллельно",
                                          "ошибки и задержки ввода"]),
        ("Сопротивление изменениям", ["врачи и ресепшен держатся за Excel", "обход новых процедур"]),
        ("Нет дежурств 24/7", ["мобильное приложение и портал без on-call", "инциденты ночью и в выходные"]),
        ("Массовый найм без обучения", ["десятки новых сотрудников", "ошибки доступа и ввода данных"]),
        ("Bus factor", ["администратор сети «может всё»", "знания не задокументированы"]),
    ]),
    ("Процессы", "#9673A6", [
        ("Нет стратегии миграции", ["big bang вместо поэтапного перехода", "нет критериев готовности и отката"]),
        ("Нет нагрузочного тестирования и SLO", ["нет capacity planning под ×5", "целевые показатели не заданы"]),
        ("Релизы без canary и feature flags", ["изменения в часы приёма", "нет быстрого отката"]),
        ("Нет регламента dual-run", ["кто и когда выверяет данные", "нет владельца данных"]),
        ("Нет управления инцидентами", ["мониторинг не видит бизнес-метрики (время записи)",
                                        "нет эскалации"]),
        ("Согласования и аттестация", ["аттестация ИСПДн и закупка СКЗИ/HSM затягивают сроки",
                                       "спешка в конце"]),
    ]),
    ("Безопасность и приватность", "#2E8B57", [
        ("Шифрование полей через Vault Transit", ["сетевой вызов на каждое поле", "Vault — узкое место и SPOF"]),
        ("PDP на каждый запрос", ["задержка решения OPA", "нет кэша политик и решений"]),
        ("Аудит каждого чтения", ["объём логов, нагрузка на OpenSearch", "диск аудита заполняется"]),
        ("WAF и DLP-инспекция", ["задержка на проверке", "ложные срабатывания блокируют работу"]),
        ("VDI для врачей и ресепшена", ["нехватка ресурсов VDI", "лаги при приёме пациентов"]),
        ("Ротация ключей и сертификатов", ["истёкший mTLS-сертификат роняет сервис",
                                           "простои при ошибках ротации"]),
    ]),
]

# ---------------------------------------------------------------- drawio writer
cells = []
_n = [0]


def esc(t):
    return html.escape(t, quote=False)


def nid():
    _n[0] += 1
    return f"ish-{_n[0]}"


def vertex(value, style, x, y, w, h):
    cells.append(("v", nid(), value, style, (x, y, w, h)))


def line(x1, y1, x2, y2, style):
    cells.append(("e", nid(), "", style, (x1, y1, x2, y2)))


S_LINE = "endArrow=none;html=1;strokeWidth={w};strokeColor={c};"
S_ARROW = "endArrow=block;endFill=1;html=1;strokeWidth=3;strokeColor=#333333;endSize=10;"
S_CAT = ("rounded=1;whiteSpace=wrap;html=1;fillColor={c};strokeColor={c};fontColor=#ffffff;fontStyle=1;"
         "fontSize=13;arcSize=20;")
S_CAUSE = ("text;html=1;align=left;verticalAlign=bottom;fontSize=10;strokeColor=none;fillColor=none;"
           "whiteSpace=wrap;spacing=0;spacingBottom=2;")
S_HEAD = ("rounded=1;whiteSpace=wrap;html=1;fillColor=#333333;strokeColor=#000000;fontColor=#ffffff;"
          "fontStyle=1;fontSize=12;arcSize=12;")
S_TITLE = "text;html=1;align=left;verticalAlign=top;fontSize=18;fontStyle=1;strokeColor=none;fillColor=none;"
S_TEXT = "text;html=1;align=left;verticalAlign=top;fontSize=10;strokeColor=none;fillColor=none;whiteSpace=wrap;"

SPINE_Y = 760
SPINE_X0, SPINE_X1 = 60, 2080
BONE_DX, BONE_DY = 230, 520   # horizontal and vertical reach of a bone
TICK = 250                    # length of a cause tick
TOP_BASES = [560, 1060, 1560, 2060]
BOTTOM_BASES = [810, 1310, 1810]

vertex("<b>" + esc("Диаграмма Исикавы: узкие места миграции «Медикаменте»") + "</b>", S_TITLE, 20, 10, 1600, 30)
vertex("<i>" + esc("Категории — кости; жирным — первичные причины; мелким — факторы. Эффект — голова рыбы. "
                   "Приоритеты мер и обоснование — в README.md") + "</i>", S_TEXT, 20, 42, 1600, 20)

# spine and head
line(SPINE_X0, SPINE_Y, SPINE_X1, SPINE_Y, S_ARROW)
vertex(esc(EFFECT), S_HEAD, SPINE_X1 + 10, SPINE_Y - 70, 300, 140)


def cause_label(cause, subs):
    return ("<b>" + esc(cause) + "</b>" +
            "".join(f'<br><font style="font-size:9px;color:#444">• {esc(s)}</font>' for s in subs))


def draw_bone(base_x, top, cat, color, causes):
    tip_x = base_x - BONE_DX
    tip_y = SPINE_Y - BONE_DY if top else SPINE_Y + BONE_DY
    line(tip_x, tip_y, base_x, SPINE_Y, S_LINE.format(w=2.5, c=color))
    # category box at the tip
    cw, ch = 230, 44
    cy = tip_y - ch if top else tip_y
    vertex(esc(cat), S_CAT.format(c=color), tip_x - cw / 2, cy, cw, ch)
    n = len(causes)
    for j, (cause, subs) in enumerate(causes):
        t = (j + 1) / (n + 1)
        px = base_x - BONE_DX * t
        py = SPINE_Y - BONE_DY * t if top else SPINE_Y + BONE_DY * t
        line(px - TICK, py, px, py, S_LINE.format(w=1, c=color))
        h = 16 + 13 * len(subs)
        if top:
            vertex(cause_label(cause, subs), S_CAUSE, px - TICK, py - h, TICK - 4, h)
        else:
            vertex(cause_label(cause, subs), S_CAUSE.replace("verticalAlign=bottom", "verticalAlign=top")
                   .replace("spacingBottom=2", "spacingTop=2"), px - TICK, py, TICK - 4, h)


for (cat, color, causes), bx in zip(CATEGORIES[:4], TOP_BASES):
    draw_bone(bx, True, cat, color, causes)
for (cat, color, causes), bx in zip(CATEGORIES[4:], BOTTOM_BASES):
    draw_bone(bx, False, cat, color, causes)

# serialise
mxfile = ET.Element("mxfile", host="app.diagrams.net", type="device")
diagram = ET.SubElement(mxfile, "diagram", name="ishikawa", id="ishikawa")
model = ET.SubElement(diagram, "mxGraphModel", dx="1400", dy="900", grid="1", gridSize="10", guides="1",
                      tooltips="1", connect="1", arrows="1", fold="1", page="1", pageScale="1",
                      pageWidth="1654", pageHeight="1169", math="0", shadow="0")
root = ET.SubElement(model, "root")
ET.SubElement(root, "mxCell", id="0")
ET.SubElement(root, "mxCell", id="1", parent="0")
for kind, cid, value, style, geo in cells:
    if kind == "v":
        c = ET.SubElement(root, "mxCell", id=cid, value=value, style=style, vertex="1", parent="1")
        ET.SubElement(c, "mxGeometry", x=str(geo[0]), y=str(geo[1]), width=str(geo[2]), height=str(geo[3]),
                      **{"as": "geometry"})
    else:
        c = ET.SubElement(root, "mxCell", id=cid, value=value, style=style, edge="1", parent="1")
        g = ET.SubElement(c, "mxGeometry", relative="1", **{"as": "geometry"})
        ET.SubElement(g, "mxPoint", x=str(geo[0]), y=str(geo[1]), **{"as": "sourcePoint"})
        ET.SubElement(g, "mxPoint", x=str(geo[2]), y=str(geo[3]), **{"as": "targetPoint"})
path = os.path.join(OUT, "Medikamente_migration_ishikawa.drawio")
with open(path, "wb") as f:
    f.write(minidom.parseString(ET.tostring(mxfile, encoding="unicode")).toprettyxml(indent=" ", encoding="utf-8"))
print(path)
