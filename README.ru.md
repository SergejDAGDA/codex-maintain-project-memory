# Maintain Project Memory

[English version](README.md)

Переносимый навык Codex для создания, обновления, аудита, подключения и передачи долговременной памяти проекта. Он разделяет постоянные правила, текущее состояние, решения, хронологию работы и контекст незавершённого этапа.

## Возможности

- создаёт память проекта на основе пакета документов и фактов из репозитория;
- подключает текущий протокол памяти к существующим проектам без автоматического переписывания истории;
- выполняет лёгкую проверку свежести памяти в начале существенной работы;
- обновляет текущий снимок после значимых проверенных этапов;
- фиксирует важные решения, не превращая предложения в одобренные решения;
- готовит компактную передачу работы новой сессии или агенту;
- проверяет файлы, заголовки, плейсхолдеры, даты, protocol markers и типичные lifecycle drift-проблемы;
- отделяет первоначальный baseline от последующей согласованной эволюции проекта;
- обнаруживает старые/неверсионированные локальные memory protocols и вложенные копии памяти;
- делает optimistic revalidation перед записью Checkpoint/Handoff, чтобы не перезаписать более новое состояние из устаревшей сессии;
- использует граф кода при наличии и переходит к точечному поиску без него.

Для основного workflow не требуются MCP-серверы, коннекторы, внешние сервисы или другие навыки.

## Protocol v2

Локальный memory protocol теперь содержит независимые markers:

```text
Project memory protocol: `maintain-project-memory/v2`
Project memory schema: `project-memory/v1`
Canonical project-memory root: `docs/project-memory`
```

Версия protocol описывает lifecycle/routing и не равна версии установленного skill. Версия schema описывает долговременную модель файлов. Отсутствующий или старый marker — сигнал для adoption review, а не разрешение автоматически переписать существующую память.

Protocol v2 добавляет:

- bounded freshness check в начале substantial work;
- read-only adoption report для старых проектов;
- явное владение canonical project-memory;
- pre-write revalidation перед Checkpoint/Handoff;
- разделение repository HEAD, implementation/deployed identity и documentation/project-memory revision, когда они различаются;
- provenance для существенных external/runtime claims, когда важно понимать источник проверки.

Назначение основных файлов не меняется: `STATUS.md` остаётся заменяемым current snapshot, `SESSION_LOG.md` — append-only историей, `HANDOFF.md` — только контекстом активной незавершённой работы.

## Структура репозитория

```text
skills/
└── maintain-project-memory/
    ├── SKILL.md
    ├── agents/openai.yaml
    ├── assets/templates/
    ├── references/
    │   ├── lifecycle-protocol.md
    │   └── update-policy.md
    └── scripts/
        ├── audit_memory_proposal.py
        ├── audit_project_memory.py
        ├── init_project_memory.py
        └── memory_snapshot.py
```

Устанавливаемым навыком является только `skills/maintain-project-memory/`. README и tests расположены уровнем выше и не входят в runtime package навыка.

## Требования

- Codex с поддержкой локальных навыков;
- Python 3.9 или новее для детерминированных скриптов из комплекта;
- Git рекомендуется как источник данных о состоянии репозитория, но не является обязательным;
- MCP-серверы, коннекторы, внешние сервисы и другие навыки не требуются.

## Установка

Для установки из GitHub передайте Codex skill installer адрес репозитория и путь `skills/maintain-project-memory`.

При ручной установке скопируйте эту папку в:

```text
~/.codex/skills/maintain-project-memory
```

Если новый навык не появился в текущей сессии, перезапустите Codex или создайте новую задачу.

## Активация

Для первого запуска надёжнее вызвать навык явно:

```text
Используй $maintain-project-memory и создай память проекта по документам из docs/context.
```

После установки Codex также может подключать его автоматически к подходящим запросам:

- «Создай память проекта по этим документам».
- «Обнови checkpoint после завершённого этапа».
- «Подготовь handoff для новой задачи».
- «Проверь проектные инструкции на устаревшие сведения».
- «Проверь, не требует ли старый project-memory protocol обновления».

Явный вызов гарантирует выбор нужного workflow, но не требуется в каждой последующей задаче: правила чтения и обновления сохраняются в проектном `AGENTS.md`.

## Начало новой сессии

Перед существенной работой в уже инициализированном проекте локальный `AGENTS.md` должен заставлять каждый новый чат/agent стартовать с одной и той же модели проекта: прочитать `PROJECT.md`, `STATUS.md`, `DECISIONS.md` и активный `HANDOFF.md`, после чего сверить этот coordination state с актуальными task-relevant фактами из repository/runtime.

Это лёгкий preflight, а не полный Audit и не новая пятая операция. `SESSION_LOG.md` читается только когда история нужна для объяснения текущего состояния.

Если Git отсутствует или `.git` не является валидным репозиторием, workflow продолжается. VCS freshness нужно обозначить как unavailable, а не выдумывать revision.

## Подключение к существующему проекту

Инициализатор по умолчанию неразрушающий:

```powershell
python ~/.codex/skills/maintain-project-memory/scripts/init_project_memory.py C:\path\to\project
```

На macOS или Linux:

```bash
python3 ~/.codex/skills/maintain-project-memory/scripts/init_project_memory.py /path/to/project
```

Он создаёт только отсутствующие файлы в `docs/project-memory/` и пропускает существующие. `AGENTS.md` автоматически не меняется. Попросите Codex аккуратно объединить `assets/templates/AGENTS.memory.fragment.md` с действующими проектными правилами.

Если project-memory уже существует, это adoption/migration, а не новый Bootstrap. Сначала запустите read-only report:

```powershell
python ~/.codex/skills/maintain-project-memory/scripts/audit_project_memory.py C:\path\to\project --adoption
```

Он показывает protocol/schema markers, наличие валидного VCS, состояние handoff и вложенные `docs/project-memory` copies. Никакая миграция автоматически не выполняется. Существующая update policy (`notify`, `approve-decisions` или `strict`) сохраняется, пока пользователь явно не изменит её.

Не используйте `--overwrite`, пока существующие файлы памяти не проверены и их замена не подтверждена.

## Optimistic revalidation

Для длинных или multi-chat workstreams можно снять read-only fingerprint памяти/VCS в начале сессии:

```powershell
python ~/.codex/skills/maintain-project-memory/scripts/memory_snapshot.py C:\path\to\project
```

Перед записью Checkpoint/Handoff запустите его снова. Если canonical project-memory files или repository HEAD неожиданно изменились, сначала загрузите и reconcile более новое состояние, а не перезаписывайте его из stale session base. Это намеренно простой optimistic revalidation, а не locking system.

## Типовые промпты

### Новый проект с исходными документами

```text
Используй $maintain-project-memory.

Это новый проект. Инициализируй project memory на основе переданных исходных
документов и фактов из репозитория.

Исходные документы / baseline:
<DOCS_PATH_OR_LIST>

Корень проекта определи сам: используй git rev-parse --show-toplevel, если
доступно; иначе используй текущую папку задачи.

Создавай или обновляй только:
- AGENTS.md
- docs/project-memory/PROJECT.md
- docs/project-memory/STATUS.md
- docs/project-memory/DECISIONS.md
- docs/project-memory/SESSION_LOG.md
- docs/project-memory/HANDOFF.md

AGENTS.md используй для рабочих правил и маршрутизации источников, а не как
полную продуктовую спецификацию. Продуктовые факты записывай в PROJECT.md,
существенные решения — в DECISIONS.md.

Если документация лежит вне репозитория, зафиксируй её как внешний
non-portable baseline source.

Политика обновления: notify.
Запусти audit_project_memory.py.
```

### Существующий проект

```text
Используй $maintain-project-memory.

Это существующий проект. Сначала выполни read-only adoption/freshness audit.
Не мигрируй и не перезаписывай существующую project-memory только потому,
что установленный skill новее.

Синхронизируй память с текущим project state только после того, как определены:
- local protocol generation;
- canonical memory root;
- stale/mixed STATUS или HANDOFF;
- unresolved legacy decisions;
- task-relevant repository/runtime evidence.

Разрешённые файлы после review:
- AGENTS.md
- docs/project-memory/*

Сохрани существующую update policy, если пользователь явно её не меняет.
Запусти audit_project_memory.py --adoption до предложения migration diff.
```

### Старт по текущему репозиторию и чату

```text
Используй $maintain-project-memory.

Отдельного пакета исходных документов нет. Инициализируй или обнови project
memory по текущему репозиторию, текущему чату и уже выполненной работе.

Считай текущий чат вспомогательным контекстом, а не автоматическим утверждением.
Неподтверждённые требования записывай как Proposed, Unverified или Assumption.

Используй точечное чтение репозитория вместо чтения всего проекта целиком.
Не меняй код, конфигурацию и продуктовые документы.
Политика обновления: notify.
```

### Checkpoint после смены концепции

```text
Используй $maintain-project-memory.

Концепция проекта изменилась:
<КРАТКОЕ_ОПИСАНИЕ_НОВОГО_НАПРАВЛЕНИЯ>

Запиши это как Approved evolution только если это сообщение является явным
подтверждением или есть другой конкретный источник подтверждения.

Перед записью перечитай canonical project-memory и повторно проверь repository
identity. Если она изменилась с начала сессии, сначала reconcile новое состояние.

Обнови DECISIONS.md, PROJECT.md, STATUS.md и SESSION_LOG.md.
AGENTS.md обновляй только если изменились operating rules, source routing,
memory policy или memory protocol.

Не позволяй старым MVP/baseline-документам переопределять утверждённое новое
направление.
Не меняй код.
Политика обновления: notify.
```

## Модель памяти

| Файл | Назначение |
|---|---|
| `AGENTS.md` | Постоянные operating rules, lifecycle protocol, protocol/schema markers и canonical memory root |
| `PROJECT.md` | Стабильная модель проекта и карта источников/authority |
| `STATUS.md` | Короткий заменяемый снимок текущего состояния |
| `DECISIONS.md` | Proposed, Unverified, Approved, Rejected и Superseded consequential decisions |
| `SESSION_LOG.md` | Append-only журнал factual checkpoints |
| `HANDOFF.md` | Заменяемый контекст только крупной незавершённой работы |

## Политики обновления

- `notify` — автоматически обновлять подтверждённую информацию и сообщать об изменениях;
- `approve-decisions` — автоматически обновлять факты, но согласовывать значимые решения; используется по умолчанию;
- `strict` — показывать предлагаемый diff перед каждым изменением памяти.

Migration protocol не меняет update policy автоматически.

Точные границы описаны в `references/update-policy.md` внутри навыка.

## Аудит

Structural audit:

```powershell
python ~/.codex/skills/maintain-project-memory/scripts/audit_project_memory.py C:\path\to\project
```

Read-only adoption/freshness report:

```powershell
python ~/.codex/skills/maintain-project-memory/scripts/audit_project_memory.py C:\path\to\project --adoption
```

Детерминированный audit не доказывает истинность содержимого. Codex всё равно должен сверить task-relevant memory с актуальными implementation/runtime facts.

## Необязательные возможности

Граф кода позволяет получать архитектуру, связи и небольшие фрагменты без широкого чтения репозитория. Навык использует его, если он уже доступен. Если его нет, работа продолжается через ограниченный поиск по файлам и тексту. Необязательный инструмент не должен становиться точкой отказа.

## Источники вдохновения

Модель памяти создана под влиянием статей Сергея Пименова [«AGENTS.md / SESSION_NOTES — проектная память для coding-агентов»](https://pimenov.ai/knowledge/agents-md-session-notes-proektnaya-pamyat/) и [«Держите памятку для агента свежей»](https://pimenov.ai/blog/derzhite-pamyatku-agenta-svezhey/). Репозиторий является самостоятельной реализацией навыка Codex с оригинальными процессами, шаблонами, правилами валидации и скриптами.

## Лицензия и публикация

Проект распространяется по лицензии MIT. Не включайте в универсальный репозиторий секреты, документы конкретного проекта, сгенерированную project-memory или данные приватных репозиториев.
