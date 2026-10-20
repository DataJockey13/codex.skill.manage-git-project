# Version 1.1: automatische Git-Aufgaben

Version `v1.1.0` veröffentlicht die Automatik aus Commit
`e607960e2ad27bca8ef69089c56c82a0fe115e2a`. Der Skill-Inhalt bleibt gegenüber
diesem geprüften Stand unverändert. Die Release-Vorbereitung ergänzt die feste
Installationsversion, Downloadlinks und diesen Nachweis.

## Enthaltene Änderungen gegenüber Version 1.0

- Automatischer Start mit eigenem Branch und projektinternem Worktree bei Kollisionen.
- Geprüfte Integration gegen den aktuellen Zielstand und anschließende Bereinigung.
- Getrennte Arbeitsorte für parallele Aufgaben und koordinierte Integration.
- Wiederaufnahme nach blockierter Bereinigung sowie belegten Unterbrechungsfällen.
- Einmalige `AGENTS.md`-Einrichtung statt ausdrücklichem Skill-Aufruf bei jeder Aufgabe.

Die [README](../README.md) beschreibt Installation und Update auf `v1.1.0`.
Das [Release](https://github.com/DataJockey13/codex.skill.manage-git-project/releases/tag/v1.1.0)
enthält `manage-git-project-v1.1.0.zip` und die zugehörige `.sha256`-Datei.
Das ZIP enthält ausschließlich die sechs Dateien des installierbaren Skill-Ordners,
einschließlich des neuen Moduls `scripts/automation.py`.

## Prüfung des Release-Pakets

Geprüft am 20.10.2026 auf macOS/arm64 mit Python 3.9.6 und Git 2.50.1.
Der [Maschinenbeleg](verification/2026-10-20-v1.1.0.json) enthält die SHA-256-Werte
aller Skill-Dateien und des ZIPs sowie die Ergebnisse.

Das Paket wurde vor der Veröffentlichung entpackt und gegen die Quelldateien
abgeglichen. Alle Prüfungen liefen aus dieser installierten Kopie in einer
frischen Python-Umgebung ohne Zusatzpakete, mit eigenem HOME, TMPDIR und ohne
benutzerweite Git-Konfiguration.

- Alle **75 Verhaltenstests** bestanden, keine Fehler und keine übersprungenen Tests.
- Ein vollständiger automatischer Aufgabenablauf erzeugte zwei isolierte Worker,
  während der Zielcheckout noch reserviert war.
- Die Integration wartete bei belegtem Ziel. Nach dessen Freigabe wurden beide
  Aufgaben mit Worker- und Kombinationstests integriert und auf ein lokales
  Bare-Remote gepusht.
- Registrierte Ergebnisse wurden auf identische kanonische Dateien umgeordnet.
- Am Ende bestanden die drei gemeinsamen Projekttests. Es blieben nur `main`
  und der ursprüngliche Checkout, ohne Aufgabenworktrees oder Checkout-Locks.
- Die synthetische Umgebung wurde nach belegtem Abgleich entfernt;
  Protokolle und ein Git-Bundle bleiben im lokalen ignorierten Prüfarchiv.

Der frühere [Parallelitätsnachweis](automatic-worktrees.md) mit zwei unabhängigen
Agenten-Chats in zwei Runden gilt für dieselben unveränderten Skill-Dateien.

## Öffentliche Installation nach Veröffentlichung

Nach Veröffentlichung wurde das feste Tag `v1.1.0` anonym über HTTPS abgefragt.
Der offizielle Skill Installer konnte den Skill sowohl per Download als auch
per Git in neue isolierte Zielordner installieren. Alle sechs installierten
Dateien stimmen bytegenau mit dem vollständig geprüften Paket überein; beide
installierten CLIs starten erfolgreich.

Die öffentlich heruntergeladenen Release-Dateien stimmen mit den zuvor geprüften
Dateien, den SHA-256-Angaben der GitHub-Assets und der beigefügten Prüfsumme
überein. GitHub weist `v1.1.0` als neuestes stabiles Release aus. Die README im Tag
verwendet den festen Ref `v1.1.0`. Die Testumgebung wurde anschließend entfernt.
Der [öffentliche Installationsbeleg](verification/2026-10-20-public-install-v1.1.0.json)
enthält Tagcommit, Downloadlinks, Hashes und geprüfte Installationsmethoden.

## Grenzen

Die Umgebung war durch Verzeichnisse, Umgebungsvariablen und Python-venv isoliert;
es wurde kein Container und keine Betriebssystem-Sandbox verwendet. Native
Windows-/Linux-Prüfungen wurden nicht ausgeführt. Projektbezogene Freigaben,
PR-/Squash-Strategien und die zusätzliche Prüfung fremder Schreiber bleiben
maßgeblich. Die kooperativen Locks sind keine globale Dateischreibsperre.
Die historische Version `v1.0.0` und ihre Release-Dateien bleiben unverändert.
