# Integration und Abschluss

Alle Aufrufe verwenden `python3 <Skill>/scripts/project.py --project-root
<Projekt> --task <Kennung>` als gemeinsamen Anfang. Parameter vor dem Unterbefehl
stehen vor `begin`, `check` usw. Die Beispiele sind Argumentvorlagen; Dateinamen
und Werte als echte getrennte Argumente übergeben, nicht als ungeprüften Shelltext.

## Erforderlicher Bestand

`begin` hält vorhandene Änderungen und Branches fest. Nicht zur Aufgabe
gehörende Änderungen müssen unverändert erhalten bleiben. Eigene bereits
begonnene Arbeit darf nur mit genauer Zuordnung über `--adopt-path <Pfad>` und
`--adopt-reason <Beleg>` übernommen werden, etwa beim Bootstrap des Checkers.
Eine Übernahme ist keine Erlaubnis, fremde Änderungen einzuschließen.

Für zusätzliche Worktrees die Integration vom Hauptcheckout aus verwalten,
den neuen Pfad im Projekt anlegen und anschließend `track-branch` ausführen.
Ein außerhalb liegender bereits vorhandener Worktree verlangt Zusammenführung
oder eine begründete Klassifizierung mit `retain --path <Pfad> --reason <Grund>`.
Das ist insbesondere für laufende fremde Arbeit gedacht und rechtfertigt keine
neuen externen Projektarbeitskopien. Nicht registrierte Altbestände erfordern
eine gesonderte, ausdrücklich beauftragte Bestandsprüfung.

## Prüfen und integrieren

Tests und erforderliche Reviews erfolgen vor der Integration. Committe nur
die eigenen Änderungen. Merge beziehungsweise Squash folgt der Projektstrategie;
der Skill führt selbst keine Merges aus. Konflikte nicht durch Verwerfen fremder
Änderungen lösen. Nicht freigegebene, unfertige oder verworfene Experimente
werden nicht automatisch integriert.

Vor dem Entfernen veröffentlichter Zweige muss der enthaltene Stand auch auf
dem tatsächlichen Remote-Ziel vorhanden sein. Tracking-Refs allein reichen
nicht; `ls-remote` prüft den Live-Stand. Bei unbekannten Objekten den bekannten
Projekt-Remote gezielt fetchen und erneut prüfen, keine Integration erraten.
Eine Remote-Löschung ist ein eigener beauftragter Git-Schritt; die Skripte
schreiben niemals auf Remotes. Bei verändertem Remote-Stand erneut abgleichen.
Keine History-Umschreibung, kein Force-Push, kein pauschales Löschen nach Präfix.

## Eigene Arbeitskopie entfernen

```sh
... remove-worktree --path <ProjektinternerPfad> --idle-evidence <TatsächlichePrüfung>
```

Das Werkzeug verlangt Aufgabenverantwortung, nachgewiesene Integration,
einen registrierten ungesperrten Worktree ohne geänderte, unversionierte oder
ignorierte Dateien und eine konkrete Prüfung aktiver Prozesse/Agenten.
Wenn verfügbar, wird `lsof` zusätzlich verwendet; ein Fehler oder Zeitlimit
führt zum Erhalt des Worktrees. Ohne `lsof` muss die Aktivitätsprüfung über
geeignete Host-Werkzeuge erfolgen. Ein bloß erfundener Leerlaufbeleg genügt nicht.

Auch ein sauberer Git-Status erlaubt keine Entfernung ignorierter Daten.
Einzigartige Dateien zuerst vollständig ins Projekt überführen; bekannte
reproduzierbare, entbehrliche Caches ausdrücklich und gezielt entfernen.
Keine automatische Ausnahmeliste für `.env`, Datenbanken oder Buildverzeichnisse.
Initialisierte Submodule und weitere Git-Sperren werden nicht erzwungen entfernt.

## Eigenen lokalen Branch entfernen

```sh
... remove-branch --branch <Aufgabenbranch>
```

Der Checkout muss auf dem Integrationsbranch stehen. Der zu entfernende Zweig
darf nirgends mehr ausgecheckt sein. Sein aktueller Tip wird erneut gegen den
Zielbranch geprüft und mit einer `update-ref --stdin`-Transaktion entfernt;
diese prüft atomar sowohl den erwarteten Zielstand als auch die Branchspitze.
Bei zwischenzeitlicher Änderung bleibt der Branch erhalten. Branch-Konfiguration und
ein Lösch-/Integrationsnachweis werden ebenfalls verwaltet. Ein noch vorhandener
Remote-Zweig oder ein nicht nachweislich veröffentlichter Integrationsstand
blockiert bei ausgewähltem Remote die lokale Bereinigung.

Bei Squash oder einem einzelnen Cherry-pick kann
`--integration-commit <TatsächlicherCommit>` angegeben werden, auch beim
Entfernen des Worktrees. Der Integrationscommit muss im Ziel liegen und genau
denselben vollständigen binären Patch einschließlich Modi und Blob-IDs enthalten.
Leere, gemischte, mehrdeutige oder veränderte Patches werden nicht automatisch
als gleichwertig anerkannt. Bei komplexeren Integrationen die Änderungen konkret
prüfen und den Zweig bis zum belastbaren Nachweis begründet erhalten.

Nur bei einer klaren Benutzerentscheidung, den konkreten Versuch zu verwerfen,
darf `--discard-reason <EntscheidungUndBeleg>` die Integration ersetzen.
Diese Option ist keine selbst erteilte Freigabe. Sie protokolliert das bewusste
Verwerfen; sie umgeht weder Aufgabenverantwortung noch den Schutz unversionierter
oder ignorierter Dateien, aktiver Prozesse und noch vorhandener Remote-Zweige.

## Übergabe und Protokoll

`check` verlangt eigene neue Änderungen committed, unveränderte fremde
Ausgangsänderungen, erledigte deklarierte Artefakte und Löschbelege für eigene
Zweige. Unregistrierte neue Branches/Worktrees und wieder angelegte Remote-Zweige
werden sichtbar. Mit `--require-push` beim Start wird auch die Veröffentlichung
des aktuellen Integrationsstands verlangt.

Für tatsächlich offene Arbeit `retain --branch <Name> --reason <KonkreterGrund>`
und anschließend `finish --outcome handoff --reason <Übergabegrund>` verwenden.
Das Ergebnis heißt ausdrücklich Übergabe, nicht vollständiger Abschluss.
Stashes, interne Agenten-Refs, andere Repositories und fremde offene Arbeit
werden weder automatisch übernommen noch entfernt.

Der JSON-Aufgabenstatus unter dem ignorierten Statusverzeichnis enthält
Ausgangslage, Artefakte und Bereinigungsbelege ohne Rohinhalte. Relevante
Ergebnisse dauerhaft nach Projektkonvention protokollieren. Statusdateien sind
keine unveränderbaren Sicherheitsatteste; sie setzen wahrheitsgemäße
Aufgabenverantwortung voraus. Nach `finish` keine unprotokollierte Restarbeit
anhängen; bei neuen Änderungen eine neue Aufgabe beginnen.
