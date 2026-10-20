---
name: manage-git-project
description: >-
  Begleite Dateiänderungen in Git-Projekten automatisch von der Bestandsprüfung
  bis zu Tests, Integration und Bereinigung. Isoliere kollidierende Aufgaben in
  eigenen Branches und projektinternen Worktrees. Verwende den Skill auch für
  beauftragte Zusammenführung; reine Lesefragen erzeugen keinen Aufgabenstatus.
---

# Git-Projektarbeit verwalten

Verwende diesen Ablauf bei Dateiänderungen selbstständig im Hintergrund.
Bestimme kanonisches Projekt und Integrationsziel aus Auftrag und `AGENTS.md`;
das Ziel kann etwa `main` heißen. Der Benutzer muss weder den Skill nennen noch
Git-Befehle vorgeben. Projektregeln für Commit, Push, Review und Freigabe gelten
weiterhin. Eine Arbeitsanweisung erteilt keine zusätzlichen Veröffentlichungsrechte.

## Vor dem Schreiben

1. Lies die geltenden Projektanweisungen. Prüfe mit den verfügbaren
   Host-Werkzeugen andere aktive Agenten und Prozesse im betroffenen Checkout.
   Bewahre fremde Änderungen und einzigartige Daten.
2. Prüfe mit `inspect` Git-Zustand und Arbeitskopien. Verwende für Änderungen
   den automatischen Ablauf aus [Automatische Aufgaben](references/automation.md).
   `start` verwendet den freien sauberen Zielcheckout oder erstellt bei Kollision
   selbstständig `codex/<Kennung>` mit einem Worktree unter `.local/worktrees/`.
   Melde zusätzlich erkannte fremde Schreiber über `--collision-reason`.
3. Verwende danach für **alle** Dateiänderungen, Tests, Commits und projektbezogenen
   Ausgaben das zurückgegebene `working_directory`. Auch temporäre Arbeit und
   weitere Worktrees gehören in das kanonische Projekt. Allgemeine installierte
   Werkzeuge bleiben an ihren Betriebsorten.

```sh
python3 <Skill>/scripts/project.py --project-root <Projekt> inspect --target <Ziel>
python3 <Skill>/scripts/project.py --project-root <Projekt> --task <EindeutigeKennung> start --target <Ziel>
```

Eine reine Lesefrage benötigt keinen Aufgabenstatus. Status und gemeinsame
Koordination liegen unter `.local/manage-git-project/`; dieser Bereich und neue
Worktrees müssen ignoriert sein. `--state-dir` verlegt die Aufgabenakten, nicht
die gemeinsamen Locks. Das Werkzeug ändert `.gitignore` nicht selbst.

## Arbeit und Abschluss

Erfasse relevante Ergebnisse und temporäre Bestände mit `artifact --path <Pfad>
--disposition retain|temporary`. Committe nur eigene Änderungen nach den
Projektregeln. Führe erforderliche Tests und Reviews aus. Starte anschließend
`complete` vom kanonischen Projekt aus mit dem tatsächlichen Prüfkommando:

```sh
python3 <Skill>/scripts/project.py --project-root <Projekt> --task <Kennung> complete --idle-evidence <AgentenUndProzessprüfung> --test-command <Programm> <Argumente>
```

`complete` prüft den Aufgabenstand und den kombinierten Integrationsstand,
reserviert den Zielcheckout für die Integration, übernimmt den geprüften Merge
und entfernt erledigte eigene Branches und Worktrees nach erneutem Abgleich.
Ein belegter Konflikt wird im eigenen Worker gelöst und erneut geprüft.
Bei belegtem parallelem Zielbesitz mit `--wait 30` erneut versuchen, solange der
andere Chat Fortschritte macht. Stehle keine Locks. Details zu Wiederaufnahme,
Remote-Veröffentlichung und Datenbeständen stehen in der Automationsreferenz.

Für übernommene Altbestände, manuelle Integrationsstrategien, externe Artefakte
und offene Übergaben lies [Integration und Abschluss](references/closure.md).
Die bisherigen Befehle `begin`, `track-branch`, `check` und `finish` bleiben
für diese Fälle verfügbar. Verworfene Versuche nur nach klarer Entscheidung
entfernen. Unfertige oder noch nicht freigegebene Arbeit bleibt mit konkretem
Zweck als Übergabe erhalten.

Berichte Ergebnisorte, Prüfungen, Integration, Veröffentlichung und begründet
offene Ressourcen. Nach abgeschlossenem Status keine weitere Arbeit anhängen.
Der kooperative Lock ersetzt keine Prüfung fremder Schreiber und ist keine
Betriebssystem-Schreibsperre. Unbekannte externe Dateien werden nicht vollständig
inventarisiert; deklarierte Artefakte und tatsächliche Dateibestände abgleichen.

## Selbsttest

```sh
python3 <Skill>/tests/test_project.py --scratch-root <Projekt>/.local/manage-git-project-tests --report <Projekt>/.local/manage-git-project-tests.json
```

Die Tests verwenden echte lokale Git-Repositories und Bare-Remotes. Behaupte
native Plattformprüfungen nur für tatsächlich ausgeführte Betriebssysteme.
