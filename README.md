# codex.skill.manage-git-project

Eigenständiges Entwicklungsprojekt für den Codex-Skill
[`manage-git-project`](manage-git-project/SKILL.md).
Der Skill unterstützt kanonische Projektablage, aufgabenbezogene Git-Inventare,
Integration, geschützte Bereinigung und überprüften Aufgabenabschluss.

Version 1.0 ist als [Release v1.0.0](https://github.com/DataJockey13/codex.skill.manage-git-project/releases/tag/v1.0.0)
mit einem ZIP des Skill-Ordners und SHA-256-Prüfsumme verfügbar.

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
Das Repository wird auf `main` geführt. Das öffentliche Remote `origin` ist
[`DataJockey13/codex.skill.manage-git-project`](https://github.com/DataJockey13/codex.skill.manage-git-project).

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

Der aktuelle [Prüfnachweis für v1.0.0](docs/verification/2026-10-19-v1.0.0.json)
bindet die ausgeführten Tests an die Quellhashes. Der
[Abschlussaudit](docs/closure-audit-v1.0.0.md) beschreibt die belegten Fehler und
Korrekturen. Die Installation eines zusätzlichen
Pakets ist für Skill-Skript und Verhaltenstests nicht erforderlich.

Die [öffentliche Installationsprüfung](docs/public-install-v1.0.0.md) belegt
anonyme Installation vom Tag `v1.0.0`, einen vollständigen Aufgabenablauf und die
46 Verhaltenstests aus der isoliert installierten Kopie.

## Herkunft

Der ursprünglich unverändert übernommene Skill stammt aus Commit
`d8c92618c409f4bbb924539f4fde6f44bfccde3a` des früheren Projekts
`/Users/dj/Documents/server.hostinger`.
Der [Importprüfnachweis](docs/verification/2026-10-19.json) dokumentiert den
damaligen Stand vor der Weiterentwicklung in diesem Repository.
Unter `docs/origin/2026-10-19/` liegen die unverändert kopierten
Einführungsberichte, damaligen Testlogs und der historische Projektprüfbericht.
Ihre Pfade, Links und Statusangaben beschreiben den damaligen Projektkontext;
sie sind keine aktuelle Ablageanweisung. Die maßgeblichen aktuellen Pfade und
Prüfbefehle stehen hier und in `AGENTS.md`. Allgemeine Serverquellen,
Produktivdaten und Gesprächsabzüge gehören nicht zu diesem Projekt.
