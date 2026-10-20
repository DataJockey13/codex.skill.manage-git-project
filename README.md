# manage-git-project

Ein Codex-Skill für Git-Aufgaben vom Arbeitsbeginn bis zum geprüften Abschluss.
Er hilft dir, Ergebnisse im richtigen Projekt abzulegen, vorhandene Arbeit zu
bewahren und erledigte Branches und Worktrees nach belegter Integration zu
bereinigen.

Der Skill kombiniert eine Arbeitsanleitung für Codex mit einem Python-Werkzeug
für Aufgabeninventar, Artefaktnachweise und Abschlussprüfungen.

[Version 1.0 herunterladen](https://github.com/DataJockey13/codex.skill.manage-git-project/releases/tag/v1.0.0)
· [Skill-Anleitung](manage-git-project/SKILL.md)
· [Installationsprüfung](docs/public-install-v1.0.0.md)

## Wann hilft dir der Skill?

- Du möchtest eine Änderung einschließlich Tests, Commit, Integration und
  Bereinigung abschließen.
- Im Projekt liegen bereits fremde Änderungen, die erhalten bleiben müssen.
- Du arbeitest mit mehreren Branches oder Worktrees und möchtest vor dem
  Entfernen Integration, Dateibestand und Aktivität prüfen.
- Ergebnisse oder temporäre Dateien sollen nachvollziehbar im Projekt bleiben
  beziehungsweise nach geprüftem Abgleich entfernt werden.
- Offene Arbeit soll mit einem konkreten Grund als Übergabe erhalten bleiben.

Der Zielbranch und die Commit-, Push- und Review-Regeln kommen aus deinem
Projekt. Der Skill setzt keinen bestimmten Branch oder Hostinganbieter voraus.

## Voraussetzungen

- Codex mit Skill-Unterstützung und Zugriff auf dein lokales Git-Projekt.
- Python **ab 3.9**; für das Werkzeug und seine Verhaltenstests brauchst du keine
  zusätzlichen Python-Pakete.
- Git mit Unterstützung für `git worktree list --porcelain -z`.

Wenn `lsof` verfügbar ist, verwendet das Werkzeug es zusätzlich zur Prüfung
aktiver Prozesse vor einer Worktree-Entfernung.

## Installation

### Mit dem Codex Skill Installer

Gib Codex diesen Auftrag:

```text
Nutze $skill-installer und installiere manage-git-project aus
https://github.com/DataJockey13/codex.skill.manage-git-project
Unterordner: manage-git-project
Version/Ref: v1.0.0
```

Installiert wird der Unterordner `manage-git-project`, der die `SKILL.md`
enthält. Die feste Versionsangabe hält die Installation auf dem veröffentlichten
Stand. Falls der Skill anschließend nicht angezeigt wird, starte Codex neu.
Hinweise zur Erkennung und Verwendung von Skills findest du in der
[offiziellen OpenAI-Dokumentation](https://learn.chatgpt.com/docs/build-skills).

### Manuell aus dem Release

Lade aus dem [Release v1.0.0](https://github.com/DataJockey13/codex.skill.manage-git-project/releases/tag/v1.0.0)
die Datei `manage-git-project-v1.0.0.zip` und die zugehörige `.sha256`-Datei.
Prüfe die SHA-256-Summe und entpacke das ZIP. Kopiere den enthaltenen Ordner
`manage-git-project` in deinen persönlichen Skill-Ordner `~/.agents/skills/`.
Die Anleitung liegt danach unter
`~/.agents/skills/manage-git-project/SKILL.md`.
Prüfe eine vorhandene Installation, bevor du sie ersetzt.

## Nutzung

Öffne dein Git-Projekt in Codex und nenne den Skill zusammen mit deiner Aufgabe:

```text
Nutze $manage-git-project für diese Aufgabe: [beschreibe deine Änderung].
Beachte die AGENTS.md und die Commit-, Push- und Review-Regeln dieses Projekts.
Erhalte vorhandene fremde Arbeit und führe die Aufgabe bis zum geprüften
Abschluss einschließlich Integration und Bereinigung aus.
```

Codex prüft zunächst den Projektzustand und andere aktive Schreiber. Für
Dateiänderungen beginnt es einen Aufgabenstatus mit kooperativem Checkout-Lock.
Während der Arbeit werden eigene Branches und relevante Artefakte zugeordnet.
Nach Prüfung und Integration kontrolliert das Werkzeug den Abschluss und gibt
den Lock erst bei erfolgreichem `finish` frei. Tatsächlich offene Arbeit wird
als begründete Übergabe ausgewiesen.

Der Aufgabenstatus liegt standardmäßig unter `.local/manage-git-project/` im
jeweiligen Projekt. Dieser Bereich muss in Git ignoriert sein. Die vollständigen
Befehle und Optionen stehen in der [Skill-Anleitung](manage-git-project/SKILL.md)
und unter [Integration und Abschluss](manage-git-project/references/closure.md).

## Prüfungen und Grenzen

Version 1.0 wurde auf **macOS/arm64 mit Python 3.9.6 und Git 2.50.1** geprüft:
Alle **46 Verhaltenstests** bestehen. Zusätzlich wurden anonyme Installation
aus GitHub per Download und Git sowie ein vollständiger Aufgabenablauf aus der
isoliert installierten Kopie geprüft. Die Tests verwenden echte lokale
Git-Repositories und Bare-Remotes.

Der Lock koordiniert Nutzer dieses Ablaufs. Er ist keine globale Schreibsperre;
andere aktive Schreiber müssen zusätzlich geprüft werden. Unbekannte externe
Dateien werden nicht automatisch vollständig erfasst. Das Werkzeug führt keine
Merges oder Remote-Schreibzugriffe aus; Codex erledigt diese im Rahmen deines
Auftrags und der Projektregeln.

Eine native Windows- oder Linux-Prüfung sowie die automatische Skill-Auswahl in
einer neuen Codex-Sitzung sind nicht belegt. Details findest du im
[Abschlussaudit](docs/closure-audit-v1.0.0.md) und in der
[öffentlichen Installationsprüfung](docs/public-install-v1.0.0.md).

## Tests selbst ausführen

Klone dieses Repository und führe die Verhaltenstests aus dessen Hauptordner aus:

```sh
git clone https://github.com/DataJockey13/codex.skill.manage-git-project.git
cd codex.skill.manage-git-project
python3 manage-git-project/tests/test_project.py \
  --scratch-root .local/test-repositories \
  --report .local/verification/tests.json
```

Die Tests schreiben nicht auf GitHub. Verbleibende Test-Repositories sind im
JSON-Bericht aufgeführt und sollten vor einer Bereinigung geprüft werden.

## Weiterführende Dokumentation

- [Prüfskript](manage-git-project/scripts/project.py) und
  [Verhaltenstests](manage-git-project/tests/test_project.py)
- [Prüfnachweis zu Version 1.0](docs/verification/2026-10-19-v1.0.0.json)
- [Reproduzierbarer öffentlicher Installationscheck](docs/verification/verify_public_install.py)
- [Herkunft und Übertragungsnachweis](docs/migration.json)
