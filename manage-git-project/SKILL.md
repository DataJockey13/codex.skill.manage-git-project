---
name: manage-git-project
description: >-
  Organisiere Dateiänderungen in Git-Projekten vom Arbeitsbeginn bis zum geprüften
  Abschluss mit kanonischer Ablage, aufgabenbezogenen Arbeitskopien, Integration
  und Bereinigung. Verwende den Skill auch bei beauftragter Zusammenführung
  verstreuter Projektdateien oder erledigter Branches; reine Lesefragen erzeugen
  keinen Aufgabenstatus.
---

# Git-Projektarbeit verwalten

Arbeite innerhalb des beauftragten Projekts und seiner geltenden Anweisungen.
Bestimme den kanonischen Projektordner und den Integrationsbranch aus dem
Auftrag und den Projektregeln. Setze nicht pauschal `main` voraus. Ein neuer
Chat benötigt keinen neuen Branch. Dieser Skill erweitert keine Freigaben für
Reviews, Remote-Änderungen, Deployments oder fremde Arbeit.

## Vor dem Schreiben

1. Lies die geltenden `AGENTS.md` einschließlich projektbezogener Overrides.
   Prüfe über die verfügbaren Host-Werkzeuge, ob andere Agenten denselben
   Checkout verändern. Vorhandene Arbeit bewahren; nicht automatisch staschen,
   zurücksetzen oder zusammen mit eigenen Änderungen committen.
2. Verwende `scripts/project.py inspect` für Branch, Upstream, Status und
   registrierte Worktrees. Prüfe bei alten Arbeitskopien auch deren tatsächlichen
   Dateibestand; eine Git-Registrierung ist kein vollständiges Dateiinventar.
3. Lege Ausgaben, temporäre Projektarbeit und notwendige zusätzliche Worktrees
   von Anfang an innerhalb des kanonischen Projekts an. Verwende vorhandene
   Struktur und ignorierte lokale Bereiche. Installierte Werkzeuge und ihre
   allgemeinen Programmdaten sind davon getrennt; Projektlieferdateien dürfen
   nicht als Programmdaten ausgelagert werden.
4. Starte für Dateiänderungen einen Aufgabenstatus mit `begin`. Wähle eine
   eindeutige Aufgabenkennung. Der kooperative Checkout-Lock bleibt bis `finish`
   bestehen und wird nicht wegen eines beendeten CLI-Prozesses gestohlen.
   Eine reine Untersuchung benötigt weder Lock noch neue Dateien.

```sh
python3 <Skill>/scripts/project.py --project-root <Projekt> inspect --target <Zielbranch>
python3 <Skill>/scripts/project.py --project-root <Projekt> --task <Kennung> begin --target <Zielbranch> --remote <Remote>
```

Lasse `--remote` nur bei rein lokaler Arbeit ohne zu prüfendes Remote weg.
`--require-push` verlangt am Ende die Veröffentlichung des Zielstands.
Der Standardstatus liegt unter `.local/manage-git-project/`; dieser Bereich
muss ignoriert sein. Passe die Ablage mit `--state-dir` an Projektkonventionen
an. Das Werkzeug ändert `.gitignore` nicht selbst. `--repo` wählt bei Bedarf
einen anderen Checkout innerhalb des kanonischen Projektordners.

## Während der Arbeit

- Erfasse eigene Aufgabenbranches unmittelbar nach dem Anlegen mit
  `track-branch --branch <Name>`. Bereits vorhandene Zweige nur bei tatsächlicher
  Aufgabenverantwortung und mit `--reason` übernehmen. Der Integrationsbranch
  darf nicht als löschbarer Aufgabenbranch geführt werden.
- Erfasse relevante Ergebnisse und temporäre Ausgaben mit
  `artifact --path <Pfad> --disposition retain|temporary`. Erhalte relevante
  bearbeitbare Quellen und Ergebnisse; archiviere nicht wahllos Toolcaches oder
  vollständige Gespräche. Geheimnisse und lokale Laufzeitdaten gehören in
  geeignete ignorierte Projektbereiche, nicht in Git.
- Für vorhandene externe Dateien nutze `artifact --disposition migrate
  --path <Quelle> --destination <Projektziel>` vor der Übertragung. Prüfe und
  übernimm den vollständigen relevanten Inhalt, bevor die Quelle entfernt wird.
  Die Abschlussprüfung verlangt identische Inhalte und eine entfernte Quelle.
- `external-control` ist ausschließlich für ausdrücklich beauftragte allgemeine
  Benutzerkonfiguration mit benanntem Pfad und konkreter `--reason` vorgesehen,
  etwa die benutzerweite `AGENTS.md`; es ist keine Ausnahme für Projektausgaben.
- Lies [Integration und Abschluss](references/closure.md), sobald Branches,
  zusätzliche Worktrees, Remote-Bereinigung oder eine offene Übergabe betroffen
  sind. Ein vollständig beauftragter Ablauf wird ohne zusätzliche pauschale
  Bestätigung ausgeführt; fehlende echte Freigaben bleiben gültige Grenzen.

## Abschluss

Prüfe die fachliche Arbeit angemessen und befolge die geltenden Commit-/Push-
Regeln. Integriere fertige, freigegebene Änderungen in den vorgesehenen Zielstand.
Verworfene Versuche nicht automatisch mergen. Bereinige ausschließlich erledigte
eigene Zweige und redundante Arbeitskopien nach erneutem Abgleich. Offene Arbeit
bleibt mit konkretem Zweck erhalten; sie gilt als dokumentierte Übergabe.

```sh
python3 <Skill>/scripts/project.py --project-root <Projekt> --task <Kennung> check
python3 <Skill>/scripts/project.py --project-root <Projekt> --task <Kennung> finish
```

`check` liefert bei offenen Befunden Exitcode 1, eine verweigerte Operation
Exitcode 2. `finish` schließt nur nach erfolgreicher Prüfung und gibt dann den
Lock frei. Für eine tatsächlich offene Übergabe sind `retain` und
`finish --outcome handoff --reason <Grund>` vorgesehen. Berichte Ergebnisorte,
Prüfungen, Git-Stand, nicht veröffentlichte Commits und begründet offene Ressourcen.

Die Prüfung umfasst den erfassten Checkout, seine registrierten Worktrees und
die deklarierten Artefakte. Sie überwacht keine beliebigen Schreibvorgänge des
Betriebssystems und findet nicht automatisch jede unbekannte externe Datei.
Der Lock koordiniert Agenten, die diesen Ablauf verwenden; aktive fremde
Prozesse und nicht kooperierende Schreiber müssen zusätzlich geprüft werden.

## Selbsttest

```sh
python3 <Skill>/tests/test_project.py --scratch-root <Projekt>/.local/manage-git-project-tests --report <Projekt>/.local/manage-git-project-tests.json
```

Der Test verwendet echte synthetische Git-Repositories und lokale Bare-Remotes,
keine GitHub-Schreibzugriffe. Native Plattformprüfungen nur für das tatsächlich
ausgeführte Betriebssystem behaupten.
