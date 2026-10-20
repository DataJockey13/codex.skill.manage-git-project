# Öffentliche Installation und vollständiger Aufgabenablauf von Version 1.0

Am 20. Oktober 2026 wurde der veröffentlichte Tag `v1.0.0` aus
[`DataJockey13/codex.skill.manage-git-project`](https://github.com/DataJockey13/codex.skill.manage-git-project)
unabhängig vom Entwicklungscheckout geprüft. Installation und Aufgabenablauf
funktionieren; eine Änderung am veröffentlichten Skill war nicht erforderlich.
Der Tag zeigt auf `5cbf355f2a22255825299b81b5299332df01a454`.

## Installation und Isolation

Der vorhandene `skill-installer` installiert den Skill-Unterordner vom festen
Tag zunächst mit `--method download`, danach in ein zweites leeres Ziel mit
`--method git`. Beide Wege verwenden anonymen öffentlichen GitHub-Zugriff.
GitHub-Tokens, SSH-Agent, Benutzer- und System-Gitkonfiguration werden nicht
übernommen. `HOME`, `CODEX_HOME`, temporäre Verzeichnisse und Cache sind für die
Prüfung getrennt unter `.local/` angelegt.

Die verwendete Python-3.9.6-Umgebung enthält weder pip noch Zusatzpakete und
übernimmt keine Benutzerpakete. Die installierten Skripte laufen als eigene
Prozesse mit `-I` und `-B`. Beide Installationen enthalten genau die vier
veröffentlichten Skill-Dateien mit passenden SHA-256-Werten. Auch das separat
anonym heruntergeladene Release-ZIP und seine Prüfsumme stimmen damit überein.
Der Installer hinterlässt keine temporären Downloads oder Git-Checkouts.

## Vollständiger Ablauf

Das Szenario verwendet ein neues Projekt mit Leerzeichen im Pfad, Zielbranch
`develop` und einem lokalen Bare-Remote als `origin`. Sämtliche Skill-Aufrufe
stammen aus der frisch installierten Kopie:

1. Ausgangslage erfassen und Aufgabe mit `--require-push` beginnen; ein zweiter
   Aufgabenbeginn im selben Checkout wird abgewiesen.
2. Eigenen Branch und projektinternen Worktree anlegen, zuordnen, eine kleine
   ausführbare Änderung prüfen und ausschließlich diese committen.
3. Verfrühten Abschluss und Entfernung ohne Integration abweisen; anschließend
   die geprüfte Änderung integrieren und das lokale Remote veröffentlichen.
4. Eine ignorierte einzigartige Datei vor der Entfernung erkennen und mit
   Inhaltsbeleg ins kanonische Projekt migrieren.
5. Worktree entfernen; den lokalen Aufgabenbranch erst nach dem Entfernen
   seines Gegenstücks im lokalen Bare-Remote bereinigen.
6. Eine deklarierte temporäre Datei beseitigen, `check` und `finish` erfolgreich
   ausführen und den freigegebenen Lock nachweisen.

Ein vor Aufgabenbeginn angelegter simulierter fremder Entwurf bleibt bytegleich
erhalten. Die integrierte Änderung liefert weiterhin das erwartete Ergebnis;
die ignorierte Datei bleibt mit identischem Inhalt im Projekt. Es verbleiben
kein eigener Aufgabenbranch, kein zusätzlicher Worktree und kein Aufgabenlock.
Alle **46 Verhaltenstests der installierten Kopie** bestehen ebenfalls ohne
Fehler oder übersprungene Fälle. Die Test-Remotes sind ausschließlich lokal;
der synthetische Ablauf schreibt nicht auf GitHub.

## Nachweis und Wiederholung

Der [Maschinenbeleg](verification/2026-10-20-public-install-v1.0.0.json) enthält
Quellhashes, Tag-Commit, Laufzeit, Ergebnisse und Hashes der lokalen Protokolle.
Die vorhandene benutzerweite Installation und die benutzerweite `AGENTS.md`
bleiben unverändert. Die isolierten Installationen und Test-Repositories werden
nach erfolgreicher Prüfung entfernt; relevante Protokolle bleiben unter
`.local/verification/public-install-v1-2026-10-20/`.

Der [Prüflauf](verification/verify_public_install.py) lässt sich mit einem
installierten `skill-installer`, Python ab 3.9 und Git wiederholen. Das
Arbeitsverzeichnis muss neu sein; sämtliche Pfade liegen im kanonischen Projekt:

```sh
python3 -B -u docs/verification/verify_public_install.py \
  --work-root .local/public-install-repeat \
  --evidence-root .local/verification/public-install-repeat
```

## Belegte Reichweite

Ausgeführt wurde auf macOS/arm64 mit Python 3.9.6 und Apple Git 2.50.1.
Die Isolation betrifft Umgebung, Konfiguration und Testverzeichnisse; es handelt
sich um keine Betriebssystem-Sandbox, keinen Container und keine VM. Eine neue
Codex-Sitzung mit automatischer Skill-Auswahl wurde nicht getestet. Native
Windows- oder Linux-Ausführung wird daraus nicht abgeleitet.
