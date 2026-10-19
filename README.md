# codex.skill.manage-git-project

Eigenständiges Entwicklungsprojekt für den Codex-Skill
[`manage-git-project`](manage-git-project/SKILL.md).
Der Skill unterstützt kanonische Projektablage, aufgabenbezogene Git-Inventare,
Integration, geschützte Bereinigung und überprüften Aufgabenabschluss.

## Einstieg

- [Startprompt für einen neuen Projektchat](PROMPT.md)
- [Projektanweisungen](AGENTS.md)
- [Skill-Anleitung](manage-git-project/SKILL.md)
- [Integration und Abschluss](manage-git-project/references/closure.md)
- [Prüfskript](manage-git-project/scripts/project.py) und
  [Verhaltenstests](manage-git-project/tests/test_project.py)
- [Übertragungsnachweis](docs/migration.json) mit ursprünglichem Commit und
  SHA-256 aller übertragenen Dateien

Die benutzerweite Installation
`/Users/dj/.agents/skills/manage-git-project` verweist auf den Unterordner
`manage-git-project/` dieses Repositories. Die benutzerweite Pflicht zur Nutzung
in `/Users/dj/.codex/AGENTS.md` bleibt erhalten. Der frühere Quellbestand unter
`server.hostinger/implementation/agent-skills/` entfällt nach geprüftem Umzug.
Das Repository wird zunächst lokal auf `main` geführt; es gibt kein Remote.

## Prüfen

Aus diesem Projektverzeichnis mit Python ab 3.9 und installiertem Git:

```sh
mkdir -p .local/verification
python3 manage-git-project/tests/test_project.py --scratch-root .local/test-repositories --report .local/verification/tests.json > .local/verification/tests.log 2>&1
python3 manage-git-project/scripts/project.py --project-root "$PWD" inspect --target main
```

Die Tests nutzen echte lokale Repositories und Bare-Remotes. Sie führen keine
GitHub-Schreibzugriffe aus. Verbleibende Testverzeichnisse vor einer Bereinigung
prüfen. Die Strukturprüfung des installierten `skill-creator` ist zusätzlich
mit einem Python-Interpreter möglich, in dem PyYAML verfügbar ist:

```sh
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py manage-git-project
```

Der aktuelle datierte [Prüfnachweis](docs/verification/2026-10-19.json) bindet
die ausgeführten Tests an die Quellhashes. Die Installation eines zusätzlichen
Pakets ist für Skill-Skript und Verhaltenstests nicht erforderlich.

## Herkunft

Der unverändert übernommene Skill stammt aus Commit
`d8c92618c409f4bbb924539f4fde6f44bfccde3a` des früheren Projekts
`/Users/dj/Documents/server.hostinger`.
Unter `docs/origin/2026-10-19/` liegen die unverändert kopierten
Einführungsberichte, damaligen Testlogs und der historische Projektprüfbericht.
Ihre Pfade, Links und Statusangaben beschreiben den damaligen Projektkontext;
sie sind keine aktuelle Ablageanweisung. Die maßgeblichen aktuellen Pfade und
Prüfbefehle stehen hier und in `AGENTS.md`. Allgemeine Serverquellen,
Produktivdaten und Gesprächsabzüge gehören nicht zu diesem Projekt.
