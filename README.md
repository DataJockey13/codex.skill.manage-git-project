# manage-git-project

Ein Codex-Skill, der Git-Projektarbeit automatisch begleitet: Bei möglichen
Kollisionen arbeitet dein Chat in einem eigenen Branch mit Worktree. Nach
Tests und erforderlichen Freigaben wird die fertige Arbeit in `main` integriert;
erledigte eigene Branches und Arbeitskopien werden geprüft und bereinigt.

Du beschreibst deine Aufgabe wie gewohnt. Codex übernimmt die Git-Schritte im
Hintergrund. Zielbranch, Commit-, Push- und Review-Regeln kommen aus deinem
Projekt; `main` ist das übliche Beispiel, keine feste Vorgabe.

[Skill-Anleitung](manage-git-project/SKILL.md)
· [Automatischer Ablauf](manage-git-project/references/automation.md)
· [Version 1.1 herunterladen](https://github.com/DataJockey13/codex.skill.manage-git-project/releases/tag/v1.1.0)

## Einmal einrichten

### 1. Version 1.1 installieren

Gib Codex diesen Auftrag:

```text
Nutze $skill-installer und installiere manage-git-project aus
https://github.com/DataJockey13/codex.skill.manage-git-project
Unterordner: manage-git-project
Version/Ref: v1.1.0
```

**Version 1.1 enthält die automatische Aufgabenisolation, Integration und
Bereinigung.** Der feste Ref `v1.1.0` installiert genau diesen veröffentlichten
Stand. Wenn du noch `v1.0.0` verwendest, beauftrage Codex mit dem Update auf
`v1.1.0`. Lass dabei die vorhandene Installation und mögliche eigene Anpassungen
prüfen, bevor sie ersetzt wird. Die einmalige Projekteinstellung unten gilt
auch nach dem Update.

Installiert wird der Unterordner mit der `SKILL.md`. Falls der Skill anschließend
nicht angezeigt wird, starte Codex neu.

Für die manuelle Installation lade das
[Skill-ZIP](https://github.com/DataJockey13/codex.skill.manage-git-project/releases/download/v1.1.0/manage-git-project-v1.1.0.zip)
und die zugehörige
[SHA-256-Datei](https://github.com/DataJockey13/codex.skill.manage-git-project/releases/download/v1.1.0/manage-git-project-v1.1.0.zip.sha256).
Prüfe die Prüfsumme, entpacke das ZIP und kopiere den Ordner `manage-git-project` nach
`~/.agents/skills/`. Hinweise zur Skill-Erkennung findest du in der
[OpenAI-Dokumentation](https://learn.chatgpt.com/docs/build-skills).

### 2. Automatische Verwendung festlegen

Ergänze einmal die `AGENTS.md` deines Projekts, damit jeder Chat den Ablauf
verwendet:

```markdown
## Git-Arbeitsablauf

Verwende bei Dateiänderungen und zum Aufgabenabschluss den installierten
Skill manage-git-project selbstständig. Kanonisches Projekt ist dieses
Repository; Integrationsziel ist main. Nutze bei Kollisionen den automatischen
Start mit eigenem Branch und Worktree. Integriere erfolgreich geprüfte und
freigegebene Arbeit und bereinige erledigte eigene Ressourcen. Beachte unsere
Commit-, Push- und Review-Regeln und bewahre fremde Arbeit.
```

Passe den Zielbranch an dein Projekt an. Wenn du den Skill projektübergreifend
verwenden möchtest, kann die entsprechende Anweisung in deiner benutzerweiten
`AGENTS.md` stehen; Projektvorgaben bleiben maßgeblich.

Ergänze außerdem diese lokalen Ablagen in der `.gitignore` deines Projekts,
sofern sie noch nicht durch vorhandene Regeln abgedeckt sind:

```gitignore
/.local/manage-git-project/
/.local/worktrees/
```

## Im Alltag

Ein normaler Auftrag reicht, zum Beispiel:

```text
Ergänze eine Suche nach Kundennamen und prüfe die Änderung.
```

Du musst den Skill nicht bei jeder Aufgabe erwähnen. Codex prüft Projektzustand
und andere Schreiber. Ein freier sauberer Zielcheckout wird direkt verwendet.
Bei einer Kollision entsteht ein eigener Branch `codex/<Aufgabe>` mit Worktree
unter `.local/worktrees/`. Parallele Chats bearbeiten so getrennte Dateien und
teilen sich nicht denselben schreibenden Checkout.

Nach dem Commit der eigenen Änderungen prüft Codex den Aufgabenstand sowie den
Merge mit dem aktuellen Zielstand. Die Integration in `main` erfolgt nacheinander.
Danach werden der eigene Worktree und Branch nach Bestands-, Aktivitäts- und
Integrationsprüfung entfernt. Ein nach Projektregeln autorisierter Push kann
zum Abschluss gehören.

Testfehler, Mergekonflikte, ausstehende Freigaben oder einzigartige lokale Daten
verhindern einen erfolgreichen Abschluss. Codex behebt die Ursache im Rahmen
deines Auftrags und prüft erneut. Belegte offene Arbeit bleibt mit einem
konkreten Grund erhalten. Ein fremder belegter Zielcheckout wird nicht übernommen.

## Voraussetzungen und Grenzen

Du brauchst Codex mit Skill-Unterstützung, Python **ab 3.9** und Git mit
Unterstützung für `git worktree list --porcelain -z`. Python-Zusatzpakete werden
nicht benötigt. Ist `lsof` vorhanden, wird es vor Worktree-Entfernungen zusätzlich
zur Prozessprüfung verwendet.

Die Automatik wird von Codex beim Bearbeiten deiner Aufgabe ausgeführt; sie ist
kein dauerhaft laufender Dienst. Die einmalige `AGENTS.md`-Regel macht ihre
Verwendung zur Projektanweisung. Kooperative Locks koordinieren beteiligte
Chats. Andere aktive Prozesse und Schreiber müssen zusätzlich geprüft werden;
es gibt keine globale Dateischreibsperre.

Der Zielbranch benötigt einen verfügbaren Checkout innerhalb des kanonischen
Projekts. Nicht kooperierende Schreiber, unbekannte externe Dateien und
projektbezogene Freigaben werden nicht durch einen Lock ersetzt. Es gibt keinen
Force-Push und keine automatische Löschung veröffentlichter Aufgabenbranches.
Projekte mit verbindlichem PR-/Squash-Verfahren verwenden für die Integration
ihren vorgeschriebenen Ablauf.

## Prüfungen

Die Verhaltenstests verwenden echte lokale Git-Repositories und Bare-Remotes.
Alle **75 Verhaltenstests** bestehen auf macOS/arm64. Die aktuelle Automatik
wurde zusätzlich mit zwei parallelen Agenten-Chats in zwei aufeinanderfolgenden
Runden in einem isolierten Testprojekt geprüft. Details und Ergebnisse stehen im
[Automatik-Prüfnachweis](docs/automatic-worktrees.md).
Das veröffentlichte Paket von Version 1.1 wird zusätzlich in einer isolierten
Python-Umgebung einschließlich automatischem Aufgabenabschluss geprüft;
Details stehen im [Release-Prüfnachweis](docs/release-v1.1.0.md).

Die frühere öffentliche Installation von `v1.0.0` wurde separat auf macOS/arm64
geprüft; die damaligen 46 Tests und der vollständige Installationsablauf sind im
[Versionsnachweis](docs/public-install-v1.0.0.md) dokumentiert. Daraus folgt keine
native Abnahme für Windows oder Linux.

Zum eigenen Testen:

```sh
git clone https://github.com/DataJockey13/codex.skill.manage-git-project.git
cd codex.skill.manage-git-project
python3 -B manage-git-project/tests/test_project.py \
  --scratch-root .local/test-repositories \
  --report .local/verification/tests.json
```

Die Tests schreiben nicht auf GitHub. Verbleibende Test-Repositories werden im
JSON-Bericht aufgeführt und sollten vor einer Bereinigung geprüft werden.

## Weiterführende Dokumentation

- [Skript](manage-git-project/scripts/project.py) und [Automationsmodul](manage-git-project/scripts/automation.py)
- [Verhaltenstests](manage-git-project/tests/test_project.py)
- [Manuelle Integration und Übergaben](manage-git-project/references/closure.md)
- [Öffentlicher Installationscheck für v1.0.0](docs/verification/verify_public_install.py)
- [Herkunft und Übertragungsnachweis](docs/migration.json)
