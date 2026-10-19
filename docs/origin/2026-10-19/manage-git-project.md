# Git-Projektarbeit verbindlich abschließen

Am 19. Oktober 2026 beauftragt der Benutzer ausdrücklich die Erstellung und
Erprobung von `manage-git-project`, seine verbindliche Nutzung über die
benutzerweite `AGENTS.md` und die entsprechende Anpassung der Projektanweisungen.
Der [Maschinenbeleg](manage-git-project.json) enthält die Anweisungshashes vor
und nach der Änderung, den eingesetzten globalen Regelblock, Quellhashes und
die Ergebnisse der Verhaltenstests.

## Installation und Zuständigkeiten

Der einzige gepflegte Skill-Bestand liegt unter
[`implementation/agent-skills/manage-git-project/`](../../../implementation/agent-skills/manage-git-project/SKILL.md).
Die benutzerweite Installation unter
`/Users/dj/.agents/skills/manage-git-project` ist ein geprüfter Symlink auf diesen
Bestand. Die allgemeine Konfiguration und dieser Installationsverweis sind
ausdrücklich beauftragte Benutzerkonfiguration, keine ausgelagerten
Projektlieferdateien. Ein Verschieben des Projekts erfordert eine Aktualisierung
des Installationsverweises.

Die benutzerweite Datei `/Users/dj/.codex/AGENTS.md` verlangt die Skill-Nutzung
vor Dateiänderungen und beim Abschluss von Git-Aufgaben. Die vorherige
Du-Anweisung bleibt erhalten. [Projekt-AGENTS.md](../../../AGENTS.md) bindet
Projektpfade, `main`, `origin`, Commit-/Push-Regeln, Wiki-Verweise und die
bestehende Parallelitätssperre. Die allgemeine Ablaufbeschreibung steht im
Skill; `wiki.md` bleibt unverändert. Die vorhandenen beiden benötigten
Hermes-Themenworktrees und die installierte Anwendung werden erhalten.

## Ablauf und Prüfungen

[`scripts/project.py`](../../../implementation/agent-skills/manage-git-project/scripts/project.py)
stellt einen lesenden Inventarlauf, Aufgabenbeginn mit kooperativem
Checkout-Lock, Artefakt- und Branchzuordnung, geschützte lokale Bereinigung
sowie Abschlussprüfung und Lock-Freigabe bereit. Vorherige fremde Änderungen
werden mit Inhaltsfingerprints erfasst und müssen erhalten bleiben. Ein
sauberer Git-Status reicht zur Worktree-Entfernung nicht: unversionierte und
ignorierte Dateien, Git-Sperren und aktive Prozesse werden zusätzlich geprüft.

Branchlöschungen verlangen Aufgabenverantwortung und Integrationsnachweis.
Eine atomare Ref-Transaktion schützt vor zwischenzeitlichen Änderungen an
Branchspitze und Integrationsziel. Squash/Cherry-pick benötigt einen exakt
gleichen vollständigen Patch; das ausdrücklich beschlossene Verwerfen eines
Versuchs wird gesondert protokolliert. Offene Arbeit wird als Übergabe erhalten.
Live-Remote-Prüfungen erkennen unveröffentlichte Zielstände und verbliebene
oder neu angelegte Aufgabenbranches. Das Skript führt weder Merges noch
Remote-Schreibzugriffe aus; diese erledigt der Agent im beauftragten Ablauf.

Der echte Auftrag verwendet denselben Skill mit der Kennung
`manage-git-project-2026-10-19`, Ziel `main` und `--require-push`.
Sein lokaler Aufgabenstatus einschließlich Abschlussprüfung liegt unter
`.local/manage-git-project/tasks/manage-git-project-2026-10-19.json`.
Der Abschlusslauf folgt auf Commit und normalen Push. Zu Beginn war der
Checkout sauber und enthielt bereits einen noch nicht gepushten fremden
Commit; dieser wird unverändert erhalten. Für diese Aufgabe wird kein
zusätzlicher Branch oder Worktree angelegt.
Die Prüfung vor dem Commit verweigerte den Abschluss erwartungsgemäß wegen
uncommitteter Aufgabenänderungen und des noch nicht veröffentlichten Zielstands;
der lokale Beleg ist im Maschinenbericht benannt.

## Testergebnis

37 Verhaltenstests bestehen auf macOS mit echten synthetischen Git-Repositories
und lokalen Bare-Remotes. Getestet sind unter anderem:

- vollständige Merge- und Squash-Abläufe einschließlich Branch-/Worktree-Abbau;
- Schutz fremder Änderungen, ignorierter Geheimnisdateien, offener Arbeit und
  einzigartiger noch nicht integrierter Commits;
- ein tatsächlich laufender Prozess im Worktree und konkurrierende Ref-Änderungen;
- ausstehende Pushes, Remote-Ausfall, entfernte und wieder angelegte Remote-Zweige;
- Migration mit Inhaltsvergleich, externe Symlinkziele und fehlende Ergebnisse;
- ausdrücklich beschlossene Verwerfung ohne Merge und ohne Löschung ignorierter Daten.

Keine Fehler, Auslassungen oder verbleibenden Test-Repositories. Alle Fixtures
entstanden unter `.local/manage-git-project-tests/` im Projekt. Die Testlogs
und der Strukturprüflauf bleiben als lokale Belege unter `.local/`; ihre
Hashes und die getesteten Skill-Quellhashes stehen im Maschinenbeleg.
Die Skill-Strukturprüfung meldet `Skill is valid!`. Der zusätzliche
[Projekt-/Wiki-Prüflauf](validation.json) prüft Verweise, Provenienz, Manifest,
erhaltene historische Belege und die aktuelle autorisierte Regeländerung.

## Reichweite

Der Skill ist eine verbindliche Arbeitsanweisung mit überprüfbaren Schritten,
keine Betriebssystemsperre gegen jede externe Dateiablage. Das Skript prüft den
erfassten Checkout, registrierte Worktrees und deklarierte Artefakte; unbekannte
externe Altbestände erfordern eine beauftragte Bestandsprüfung. Der Lock wirkt
zwischen kooperierenden Agenten. Die Einbindung von Hermes/n8n in diesen Lock
ist damit nicht bestätigt; ihre bestehende Sperre gleichzeitiger Schreibarbeit
bleibt gültig. Native Windows-Tests wurden nicht ausgeführt. Die automatisierten
Tests schreiben nicht auf GitHub und ersetzen keine neue Produktivabnahme.

## Erneut gefundene Vergleichsdateien

Der Bestandsprüflauf hat zwei bekannte temporäre Before-/After-Dateien des
Hermes-Tests `create-agent-lazy-profile.test` außerhalb des Projekts erneut
gefunden. Beide stimmen byteweise und per SHA-256 mit ihren schon unter
`.local/recovered/2026-10-18/external-final/macos-temp/` gesicherten Kopien
überein. `lsof` meldete keine offenen Dateien; die beiden externen Dubletten
wurden nach Registrierung als Migration im neuen Aufgabenstatus entfernt.
Pfade, Größen, Hashes und Abgleich stehen im Maschinenbeleg. Die Ursache der
erneuten Erzeugung ist nicht belegt; eine globale Schreibüberwachung wird
daraus nicht abgeleitet. Die erste Bestandsprüfung meldete außerdem den noch
nicht erzeugten eigenen Ergebnisverweis `validation.json`; dieser wird durch
den Prüflauf angelegt und anschließend erneut geprüft.
