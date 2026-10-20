# Automatische Aufgaben

Dieser Ablauf wird vom Agenten ausgeführt. Er setzt eine installierte Skill-Kopie
und die projektbezogene Anweisung voraus, den Skill bei Dateiänderungen zu
verwenden. Er benötigt keinen dauerhaften Hintergrundprozess.

## Einstieg und Arbeitsort

Alle Beispiele beginnen mit `python3 <Skill>/scripts/project.py --project-root
<Projekt> --task <Kennung>`. Die Kennung ist eindeutig und wird nie wiederverwendet.
Verwende `--repo <Checkout>` vor dem Unterbefehl, falls der Ausgangscheckout vom
kanonischen Projektordner abweicht. Lies dessen Anweisungen vor dem Start.

```sh
... start --target main --remote origin --require-push
```

`--remote` nur bei ausgewähltem vorhandenem Projektremote verwenden;
`--require-push` nur, wenn die Veröffentlichung zum Auftrag gehört.
Ohne Remote bleiben Aufgaben lokal. Das Ziel kommt aus den Projektregeln.

Ein freier, sauberer Zielcheckout wird direkt reserviert. Bei vorhandenen
Datei-/Indexänderungen, einem anderen ausgecheckten Branch, einer anderen aktiven
Aufgabe oder einem Checkout-Lock entsteht ein eigener Branch mit Worktree.
Zusätzliche Host-Erkenntnisse über nicht kooperierende Schreiber mit
`--collision-reason <KonkreterBefund>` angeben. Kein anderer Checkout wird
zurückgesetzt oder gestasht. Für bestehende eigene Änderungen ist der bewusste
manuelle Übernahmeweg aus der Abschlussreferenz vorgesehen.

Die JSON-Antwort nennt `working_directory`, `branch`, `mode` und Kollisionsgründe.
Arbeite ab jetzt ausschließlich im zugewiesenen Checkout. Befehle zur
Aufgabenverwaltung finden ihn anschließend selbst, sofern `--repo` weggelassen
wird. Gemeinsame Task-IDs, Ressourcenbesitz und Checkout-Locks bleiben unter
`.local/manage-git-project/`, auch bei abweichender Aufgabenakten-Ablage.

Neue Worktrees liegen unter `.local/worktrees/`. Bei erstmaliger Einrichtung
müssen beide lokalen Verzeichnisse nach Projektkonvention ignoriert werden.
Ist das nicht eingerichtet, verweigert das Skript den Start. Richte die beiden
gezielten Ignore-Regeln als beauftragte Projekteinstellung ein, bevor parallele
Schreibarbeit beginnt; ändere fremde Ignore-Regeln nicht pauschal.

## Geprüft integrieren

Nach fachlicher Prüfung, erforderlichen Freigaben und einem Commit nur der
eigenen Änderungen:

```sh
... complete --wait 30 --idle-evidence <TatsächlicherBefund> --test-command python3 -B -m unittest discover -s tests
```

`--test-command` steht zuletzt und enthält ein Programm mit getrennten Argumenten,
keinen Shellausdruck. Verwende einen im Worker und Integrationscheckout gültigen
Prüfaufruf mit relativen Projektpfaden. Für andere Prüfketten verwende das
vorhandene Prüfskript des Projekts. `--test-timeout` ist standardmäßig 300 Sekunden.

Führe den Abschluss aus einem stabilen Ordner wie dem kanonischen Projekt aus.
Eine Shell mit aktuellem Verzeichnis im Worker kann dessen Entfernung durch die
Prozessprüfung blockieren. Beende eigene Server, Watcher und offene Prozesse im
Worker und prüfe andere aktive Chats unmittelbar vor der Bereinigung.

Im isolierten Modus reserviert `complete` den tatsächlichen Zielcheckout. Bei
Belegung wartet es höchstens `--wait` Sekunden und liefert danach `pending`
mit Exitcode 1. Der Worker bleibt aktiv. Wiederhole den Abschluss mit begrenzter
Wartezeit, solange der andere Chat arbeitet; behaupte vorher keinen Abschluss.
Ein separates Betriebssystem-Lock verhindert zwei gleichzeitige
`complete`-Aufrufe derselben Aufgabe und endet mit dem CLI-Prozess.
Auch kurze Änderungen am gemeinsamen Ressourcenregister verwenden eine
Prozess-Lease. Die zugehörigen Dateien bleiben bestehen; ihre Existenz allein
bedeutet keine aktive Reservierung. Die dauerhafte Checkout-Reservierung einer
Aufgabe bleibt davon getrennt und endet nicht mit einem CLI-Prozess.

Das Werkzeug prüft den Workercommit und erstellt einen separaten temporären
Integrationscheckout. Es führt einen Merge mit `--no-ff` aus und prüft den
kombinierten Stand erneut. Erst danach wird der saubere Zielcheckout auf den
geprüften Commit vorgezogen. Die Belege enthalten Prüfkommando, Commit-IDs,
Exitcodes und Ausgabehashes. Ein inzwischen geänderter Worker oder Zielstand
verlangt erneute Prüfung. Die Branchspitzen werden vor Bereinigung erneut geprüft.

Für die Integration muss genau ein Checkout des Zielbranches innerhalb des
kanonischen Projekts verfügbar sein. Falls er fehlt, bereite nach Aktivitäts-
und Bestandsprüfung einen geeigneten Zielcheckout vor; wechsle keinen fremden
belegten Checkout um. Ein schmutziger oder fremd belegter Zielcheckout bleibt
erhalten. Erforderliche Reviews beziehungsweise eine vom Projekt verlangte
Squash-/PR-Strategie werden vor der Integration erfüllt; bei abweichender
Merge-Strategie den manuellen Abschlussweg verwenden.

## Veröffentlichung und Bereinigung

`complete --push ... --test-command ...` veröffentlicht den Zielbranch auf dem
beim Start ausgewählten Remote mit normalem Push. Verwende es selbstständig,
wenn der Auftrag oder die Projektregeln Push bereits autorisieren. Ohne diese
Option gibt es keinen Remote-Schreibzugriff. Kein Force-Push und keine
automatische Remote-Branch-Löschung. Automatische Aufgabenbranches bleiben lokal.

Nach Integration werden nur eigene Arbeitskopien ohne Änderungen, unversionierte
oder ignorierte Dateien und ohne aktive Prozesse/Locks entfernt. Registrierte
`retain`-Artefakte im Worker müssen am gleichen relativen Ort identisch im
Zielcheckout vorliegen; ihre Pfade werden nachvollziehbar umgeordnet. Einzigartige
Daten vorher kanonisch sichern. Bekannte entbehrliche Testcaches gezielt entfernen.
Eigene Branches werden erst nach Integrations- und gegebenenfalls Live-Remote-
Nachweis gelöscht. Peer-Aufgaben sind registrierter fremder Besitz und werden
weder übernommen noch bereinigt. `finish` prüft zuletzt Artefakte und Löschbelege.

## Fehler und Wiederaufnahme

Bei Testfehlern bleibt das Ziel unverändert. Ein Konflikt bleibt im generierten
Integrationscheckout sichtbar. Brich dort nur den eigenen generierten Merge mit
`git merge --abort` ab. Merge den aktuellen Zielbranch im **Worker**, löse den
Konflikt unter Erhalt beider Arbeiten, committe und wiederhole `complete`.
Unprotokollierte Commits im Integrationscheckout werden nicht gelöscht.

Bei Fehlern vor Veröffentlichung kann nach Korrektur mit einem passenden
Prüfkommando erneut geprüft werden. Nach Beginn der Veröffentlichung verlangt
die Wiederaufnahme dasselbe gespeicherte Kommando. Fehlgeschlagener Push,
blockierende Dateien oder noch vorhandene temporäre Artefakte verhindern den
Abschluss; beseitige nur die belegte Ursache und wiederhole `complete`.
Bereits protokollierte Löschungen werden erkannt. Zielreservierungen werden
bei behandelbaren Fehlern freigegeben; ein noch vorhandener Worker bleibt
reserviert. Neue Workercommits nach einer blockierten Bereinigung werden erneut
geprüft und integriert. Vor Stage-/Branchlöschung gespeicherte Löschabsichten
erlauben nach Prozessabbruch einen Abgleich bereits verschwundener Ressourcen.
Ein fehlender Bestand ohne solchen Nachweis bleibt ein Fehler.
Nach hartem Prozessabbruch vorhandene kooperative Checkout-Locks anhand
Taskbesitz und tatsächlicher Aktivität prüfen, nie wegen einer alten PID stehlen.

Exitcode 0 bedeutet geprüften Abschluss, 1 eine offene Prüfung beziehungsweise
wartende Integration, 2 eine verweigerte Operation. Noch ausstehende Freigaben
oder tatsächlich offene Arbeit mit `retain` und begründetem
`finish --outcome handoff` übergeben. Eine Übergabe ist kein erfolgreicher Abschluss.
