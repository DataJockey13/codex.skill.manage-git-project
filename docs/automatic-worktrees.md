# Automatische Aufgaben mit parallelen Chats

Geprüft am 20.10.2026 auf macOS 26.6.2/arm64, Python 3.9.6 und
Git 2.50.1. Der [maschinelle Nachweis](verification/2026-10-20-automatic-worktrees.json)
enthält Quellhashes, Commit-IDs, Prüfaufrufe und Bereinigungsergebnisse.

## Umsetzung

`start` reserviert einen freien sauberen Zielcheckout. Bei belegtem Checkout,
bestehenden Änderungen, anderem Ausgangsbranch oder aktiven Peer-Aufgaben legt
es selbst einen Branch `codex/<Task>` und einen projektinternen Worktree an.
Zusätzlich vom Host erkannte fremde Schreiber werden als Kollisionsgrund
übergeben. Die Antwort weist den verbindlichen Arbeitsort aus.

`complete` prüft den committeten Workerstand, reserviert den tatsächlichen
Zielcheckout und prüft einen Merge gegen dessen aktuellen Stand in einer
separaten Arbeitskopie. Erst ein erfolgreicher kombinierter Test erlaubt die
Übernahme ins Ziel. Anschließend erfolgen optional autorisierter normaler Push,
Bestands-/Aktivitätsprüfung, Worktree- und Branchbereinigung und Abschlussprüfung.

Gemeinsame Ressourcenakten verhindern, dass ein Chat die Branches oder Worktrees
eines anderen übernimmt oder als eigene Reste meldet. Abweichende Statuspfade
umgehen die gemeinsame Checkout-Reservierung nicht. Kurze Registeroperationen
und ein einzelner Abschlussaufruf verwenden getrennte OS-Leases; die dauerhafte
Aufgabenreservierung besteht bis zum Abschluss beziehungsweise zur Übergabe.

## Verhaltenstests

**75 Tests bestanden, keine Fehler, keine übersprungenen Tests.** Die Tests laufen
gegen echte lokale Git-Repositories mit lokalen Bare-Remotes. Gegenüber der
bisherigen Suite mit 46 Tests kamen 29 Fälle für die Automatik hinzu.

Geprüft wurden insbesondere parallele Starts, gleiche Task-ID, gleichzeitige
Abschlussaufrufe, unbekannte/fremde Änderungen im Index und in Dateien,
Peer-Besitz, ausgewählte Statusverzeichnisse, andere Zielbranchnamen, fehlende
Zielcheckouts, Worker- und Integrationstestfehler, Konfliktlösung im Worker,
zwischenzeitlich fortgeschriebene Worker, expliziter Push und Wiederaufnahme.

Ignorierte einzigartige Daten verhindern weiterhin die Entfernung. Bereits
entfernte eigene Branches werden anhand der Quittungen erkannt. Für Unterbrechungen
zwischen Git-Löschung und Quittung wird die erwartete Löschabsicht vorher
persistiert. Zwei Tests beenden echte CLI-Kindprozesse mit `os._exit()` direkt
nach erfolgreicher Stage- beziehungsweise Branchlöschung; der nächste Aufruf
gibt anhand des Abgleichs einen erfolgreichen Abschluss aus. Das ist ein
Nachweis für diese konkreten Unterbrechungsstellen.

Die vorhandene Prüfung eines fremden Worktree-Locks bleibt bestehen. Neue
Clients verweigern nun zusätzlich bereits `begin` in einem von einem anderen
Task registrierten Worker oder Integrationscheckout; die ältere Locksituation
wird im Test als vorhandener Lock eines älteren Clients dargestellt.

Der Skill-Validator meldet `Skill is valid!`. Relative Markdown-Verweise,
Freigabegrenzen und die README-Anleitung wurden geprüft.

## Parallele Testchats

Zwei unabhängige Agenten-Chats erhielten normale Entwicklungsaufträge für ein
isoliertes Projekt unter `.local/parallel-chat-automation`. Dessen `AGENTS.md`
verlangte den Skill, Tests, Commit und Push auf ein lokales Bare-Remote.
Die Aufträge enthielten keine vorgegebene Befehlsfolge und keinen ausdrücklichen
Skill-Aufruf. Ein kurzzeitig durch den Testkoordinator reservierter Zielcheckout
erzwang zwei getrennte Worker. Die gleichzeitige Aktivität beider Tasks und
unterschiedliche Arbeitsorte wurden jeweils vor der Freigabe festgehalten.

- Runde 1: Namensnormalisierung und Initialen; anschließend bestanden alle
  **10** gemeinsamen Projekttests.
- Runde 2 mit der abschließenden Implementierung: Wortliste und Wortzählung;
  anschließend bestanden alle **18** gemeinsamen Projekttests.

Alle vier Aufgaben haben erfolgreiche Worker- und Integrationstests sowie
Abschlussbelege. Die Zielbasis des jeweils späteren Merges enthält die zuvor
integrierte Arbeit. Am Ende bestehen genau ein Branch `main` und der ursprüngliche
Checkout. Alle eigenen Worker, Integrationscheckouts und Checkout-Locks sind
entfernt. Das lokale Bare-Remote entspricht dem abschließenden Zielcommit
`f3af4d755767b4609b9c89b5ac94fcf83141cbb5`. Vollständige Quittungen, Testprotokolle
und ein Git-Bundle bleiben im ignorierten lokalen Prüfarchiv; das synthetische
Testprojekt wurde nach dem Abgleich entfernt.

## Belegte Grenzen

Die Chats waren unabhängige Subagent-Kontexte im selben Hostprozessverbund;
separate Fenster der Codex-Desktopoberfläche wurden nicht bedient. Die lokale
AGENTS-Anweisung wurde von beiden Chats befolgt. Daraus folgt weder eine globale
Dateischreibsperre noch eine native Windows-/Linux-Abnahme.

Ein belegter oder schmutziger fremder Zielcheckout, benötigte Freigaben und
unbekannte Daten werden nicht übergangen. Der Zielbranch benötigt einen
verfügbaren projektinternen Checkout. Projekte mit verbindlicher PR-/Squash-
Integration verwenden dafür ihren vorgeschriebenen Ablauf. Die veröffentlichte
Version `v1.0.0` bleibt unverändert; diese Automatik wird über `main` installiert.
