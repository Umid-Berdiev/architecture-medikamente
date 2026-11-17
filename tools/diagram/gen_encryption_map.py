"""Generate the Task 3 encryption map: trust zones of the target architecture with the at-rest
protection written on every store and the in-transit protection written on every hop.

    python3 tools/diagram/gen_encryption_map.py Task3
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from c4_lib import C4Diagram  # noqa: E402

OUT = sys.argv[1] if len(sys.argv) > 1 else "Task3"
os.makedirs(OUT, exist_ok=True)

d = C4Diagram()
p = d.page("encryption-map")
p.title("Карта шифрования «Медикаменте» (to-be): защита при хранении — на блоках, при передаче — на связях",
        w=1900)

# ---- external parties (left column)
p.person("pat", "Пациент", "Браузер, мобильное приложение", 40, 60, external=True)
p.system("prt", "Партнёры и лаборатория", "Внешние API-клиенты", 40, 320, w=200, h=100, external=True)
p.system("gos", "ЕГИСЗ, ФНС, СФР, ЭДО", "Государственные системы", 40, 560, w=200, h=100, external=True)
p.system("pay", "Платёжный провайдер", "Эквайринг, 3-D Secure", 40, 700, w=200, h=100, external=True)
p.system("mailx", "Внешняя почта", "Пациенты, контрагенты", 40, 840, w=200, h=100, external=True)

# ---- DMZ
p.boundary("b_dmz", "DMZ", "терминация внешнего TLS, выпуск внутреннего mTLS", 330, 60, 300, 920, stroke="#B85450")
p.container("api", "API Gateway + WAF", "TLS 1.3, HSTS, mTLS партнёров", "Kong/APISIX; OAuth2; схемная валидация; "
            "сертификаты cert-manager", 350, 100, w=260, h=110, kind="privacy")
p.container("ngate", "ГОСТ TLS-шлюз", "КриптоПро NGate / CSP", "Для контрагентов и госсистем, требующих ГОСТ; "
            "КЭП документов", 350, 440, w=260, h=100, kind="privacy")
p.container("dlp", "Почтовый DLP-шлюз", "TLS-коннекторы, S/MIME", "Инспекция вложений, блокировка класса R",
            350, 660, w=260, h=100, kind="privacy")
p.container("vpn", "Криптошлюз ГОСТ VPN", "ViPNet / Континент, КС2–КС3", "Туннели к филиалам и резервной площадке",
            350, 800, w=260, h=100, kind="privacy")

# ---- ISPDn contour
p.boundary("b_core", "Контур ИСПДн (Kubernetes, аттестуемый сегмент)", "mTLS между всеми компонентами, "
           "зашифрованные тома, deny-by-default", 700, 60, 1100, 900, stroke="#0E7DAD")
p.container("svc", "Доменные сервисы", "mesh mTLS STRICT, Vault Agent", "Identity, Scheduling, Clinical, Billing, "
            "CRM, интеграции; секреты только в памяти; ПДн не пишутся в логи", 720, 100, w=300, h=120)
p.container("pg", "PostgreSQL доменов", "LUKS PV + Vault Transit (колонки)", "HMAC-индексы, pgaudit, "
            "динамические учётные записи Vault", 1140, 90, w=260, h=150, db=True)
p.container("s3", "Документы и озеро", "S3 SSE-KMS, object lock", "Per-patient DEK; raw-зона — отдельный ключ; "
            "версии", 1480, 90, w=260, h=150, db=True)
p.container("kafka", "Kafka", "SASL_SSL / mTLS, ACL", "E2E-шифрование полей pii.med; зашифрованные тома; "
            "retention 7 дней", 720, 330, w=300, h=120)
p.container("vault", "Vault + HSM", "auto-unseal через HSM (ФСБ), PKI, Transit", "Ключи доменов, per-patient DEK, "
            "ротация, аудит; доли Shamir у 2 лиц", 1140, 330, w=260, h=120, kind="privacy")
p.container("os", "OpenSearch: аудит и логи", "зашифрованный PV, WORM-индексы", "Журнал доступа, Vault audit, "
            "SIEM-правила", 1480, 320, w=260, h=140, db=True)
p.container("pam", "PAM-бастион", "SSH/TLS, MFA с аппаратным токеном", "JIT-доступ, запись сессий "
            "администраторов", 1140, 560, w=260, h=100, kind="privacy")
p.container("bak", "Резервные копии", "pgBackRest AES-256, Velero, object lock", "Ключ бэкапов отделён от "
            "продакшена; проверка восстановления", 1480, 550, w=260, h=150, db=True)
p.container("c1", "1С + PostgreSQL", "TLS клиент–сервер, зашифрованный том", "Веб-сервисы по HTTPS; файловый "
            "доступ закрыт", 1140, 720, w=260, h=110, kind="legacy")
p.container("anal", "Аналитический контур", "зашифрованные диски ClickHouse, S3 SSE", "Обезличивание → curated → "
            "витрины; выход через Trino + OPA; JupyterHub и LLM внутри", 720, 760, w=380, h=120, kind="analytics")

# ---- office and branches
p.boundary("b_off", "Офис и филиалы", "контролируемая зона", 330, 1020, 1470, 220, stroke="#9673A6")
p.container("vdi", "Рабочие места и VDI", "BitLocker (TPM + PIN), VDI для ролей с доступом к R", "Ресепшен, врачи, "
            "касса, аналитики; USB заблокирован; print-сервер с учётом", 350, 1070, w=300, h=120, kind="channel")
p.container("lan", "ЛВС и Wi-Fi", "802.1X (EAP-TLS), WPA3-Enterprise, NAC", "Гостевая сеть изолирована; ККМ в "
            "отдельном VLAN", 700, 1070, w=300, h=120, kind="channel")
p.container("exch", "Exchange", "TLS-коннекторы, зашифрованное хранилище", "Служебная почта; вложения класса R "
            "запрещены", 1050, 1070, w=260, h=120, kind="legacy")
p.container("brvpn", "Криптошлюз филиала", "ViPNet / Континент", "ГОСТ VPN к DMZ", 1360, 1070, w=300, h=120,
            kind="privacy")

# ---- off-site and administrator
p.boundary("b_off2", "Резервная площадка / off-site", "", 1880, 440, 260, 260, stroke="#666666")
p.container("offsite", "Off-site хранилище", "object lock (WORM), шифрование клиентским ключом", "Копии БД, S3; "
            "резерв ключей HSM в сейфе", 1900, 500, w=220, h=140, db=True)
p.person("adm", "Администратор", "Только через PAM, аппаратный токен", 1900, 60)

# ---- hops
p.rel("pat", "api", "TLS 1.3, HSTS, pinning", "HTTPS", exit_=(1, 0.5), entry=(0, 0.3))
p.rel("prt", "api", "mTLS + OAuth2", "HTTPS", exit_=(1, 0.5), entry=(0, 0.8), points=[(300, 370), (300, 188)],
      lab=(0.3, 0))
p.rel("ngate", "gos", "ГОСТ TLS, КЭП", "КриптоПро", exit_=(0, 0.5), entry=(1, 0.5), points=[(300, 490), (300, 610)],
      lab=(0.5, 0))
p.rel("svc", "pay", "TLS 1.2+, токен карты", "HTTPS", exit_=(0, 0.9), entry=(1, 0.5), dashed=True,
      points=[(670, 208), (670, 800), (300, 800), (300, 750)], lab=(-0.55, 0))
p.rel("dlp", "mailx", "Enforced TLS, S/MIME", "SMTP", exit_=(0, 0.5), entry=(1, 0.5), points=[(300, 710), (300, 890)],
      lab=(0.5, 0))
p.rel("api", "svc", "mTLS (mesh), JWT", "gRPC / REST", exit_=(1, 0.5), entry=(0, 0.4))
p.rel("ngate", "svc", "mTLS", "", exit_=(1, 0.5), entry=(0, 0.7), points=[(690, 490), (690, 184)])
p.rel("svc", "pg", "TLS verify-full", "JDBC", exit_=(1, 0.3), entry=(0, 0.4))
p.rel("svc", "vault", "TLS, JWT", "", exit_=(1, 0.5), entry=(0, 0.5), points=[(1110, 160), (1110, 390)],
      lab=(0.55, 0))
p.rel("svc", "s3", "HTTPS, SigV4", "S3 API", exit_=(1, 0.8), entry=(0.5, 1),
      points=[(1080, 196), (1080, 265), (1610, 265)], lab=(0.2, 0))
p.rel("svc", "os", "TLS", "OTLP", exit_=(1, 0.9), entry=(0, 0.5),
      points=[(1060, 208), (1060, 285), (1460, 285), (1460, 390)], lab=(0.6, 0))
p.rel("svc", "kafka", "SASL_SSL (OAUTHBEARER)", "", exit_=(0.5, 1), entry=(0.5, 0))
p.rel("pg", "bak", "pgBackRest, шифрование до записи", "", exit_=(1, 0.9), entry=(0.25, 0),
      points=[(1420, 225), (1420, 520), (1545, 520)], lab=(0.5, 0))
p.rel("s3", "bak", "Velero", "HTTPS", exit_=(1, 0.8), entry=(1, 0.25), points=[(1770, 210), (1770, 587)],
      lab=(0.5, 0))
p.rel("bak", "offsite", "ГОСТ VPN / TLS", "", exit_=(1, 0.75), entry=(0, 0.5),
      points=[(1820, 662), (1820, 570)], lab=(0.5, 0))
p.rel("kafka", "anal", "SASL_SSL, Kafka Connect; только patient_id", "", exit_=(0.5, 1), entry=(0.4, 0))
p.rel("c1", "kafka", "HTTPS веб-сервисы (1С Adapter)", "", exit_=(0, 0.5), entry=(1, 0.5), dashed=True,
      points=[(1060, 775), (1060, 390)], lab=(0.3, 0))
p.rel("adm", "pam", "SSH/TLS через бастион, MFA", "", exit_=(0.5, 1), entry=(1, 0.5),
      points=[(2000, 540), (1420, 540), (1420, 610)], lab=(0.3, 0))
p.rel("vdi", "api", "TLS 1.3; VDI-сессии внутри ЦОД", "HTTPS", exit_=(0.5, 0), entry=(0.5, 1),
      points=[(500, 1000), (640, 1000), (640, 230), (480, 230)], lab=(0.5, 0))
p.rel("exch", "dlp", "TLS", "SMTP", exit_=(0.5, 0), entry=(1, 0.5), points=[(1180, 990), (690, 990), (690, 710)],
      lab=(0.6, 0))
p.rel("brvpn", "vpn", "ГОСТ VPN КС2–КС3 (IPsec)", "", exit_=(0.5, 0), entry=(0.5, 1),
      points=[(1510, 1040), (480, 1040)])
p.rel("lan", "vdi", "802.1X", "", exit_=(0, 0.5), entry=(1, 0.5))

p.text("<b>Легенда.</b> Зелёный — средства криптографии и контроля доступа; синий — сервисы и хранилища контура; "
       "фиолетовый — аналитика; серый — внешние и унаследованные системы. Технология в скобках на блоке — защита при "
       "хранении; подпись связи — защита при передаче. Красная зона — DMZ, синяя — контур ИСПДн, фиолетовая — офис и "
       "филиалы (зоны из 01-data-classification.md § 1.6).", 20, 1270, 1900, 40)

d.write(os.path.join(OUT, "Medikamente_encryption_map.drawio"))
print("encryption map written")
