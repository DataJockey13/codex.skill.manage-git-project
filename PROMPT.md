# Startprompt für das neue Projekt

```text
Du arbeitest im Projekt /Users/dj/Source/codex.skill.manage-git-project.
Hier entwickeln wir den Codex-Skill manage-git-project weiter.

Lies zuerst die benutzerweite und die lokale AGENTS.md, README.md,
manage-git-project/SKILL.md und bei Bedarf references/closure.md im Skill.
Prüfe Git-Status, Branch, Arbeitskopien und andere aktive Schreiber.
Nutze den Skill selbst vor Dateiänderungen und für den Aufgabenabschluss.

Der Skill mit scripts/project.py und tests/test_project.py wurde ursprünglich
unverändert aus dem Projekt server.hostinger übernommen und wird hier
weiterentwickelt. Herkunft, Hashes und Prüfergebnisse stehen unter docs/.
Historische Berichte unter docs/origin/
enthalten die damals geltenden Pfade; sie sind keine aktuelle Konfiguration.
Die benutzerweite Installation ~/.agents/skills/manage-git-project zeigt auf
den Unterordner manage-git-project dieses neuen Projekts.

Ziel ist ein zuverlässiger, allgemein einsetzbarer Ablauf für gitbasierte
Projektarbeit: relevante Dateien im jeweiligen kanonischen Projekt halten,
fremde Änderungen und einzigartige Daten bewahren, fertige freigegebene Arbeit
integrieren und erledigte eigene Branches und Worktrees nach belegtem Abgleich
bereinigen. Verworfene Versuche nur bei klarer Verwerfungsentscheidung entfernen.
Offene Arbeit mit konkretem Zweck übergeben. Projektbezogene Commit-, Push-,
Review- und Freigaberegeln bleiben maßgeblich.

Entwickle ausschließlich in diesem Projekt. Lege temporäre Daten und
Test-Repositories unter .local/ ab. Übernimm keine pauschalen Regeln aus
server.hostinger und ändere dort keine Dateien. Der Skill-Lock koordiniert
kooperierende Agenten und ersetzt keine Prüfung aktiver fremder Schreiber.
Behaupte keine globale Dateischreibsperre oder ungetestete Plattformabnahme.

Arbeite anhand konkreter Anforderungen oder nachgewiesener Fehler. Halte
SKILL.md knapp, verlagere bedingte Details in references/ und prüfe Änderungen
an den Skripten mit beobachtbaren Verhaltenstests an echten lokalen Git-Repos.
Committe geprüfte Änderungen auf main beziehungsweise integriere fertige eigene
Aufgabenbranches und bereinige sie. Das öffentliche Remote origin ist
https://github.com/DataJockey13/codex.skill.manage-git-project.
Pushe geprüfte abgeschlossene Änderungen auf origin/main.

Beginne mit einer lesenden Bestandsaufnahme: Erkläre kurz den aktuellen Aufbau,
die vorhandenen Prüfungen und belegte Grenzen. Erfinde keinen nächsten
Entwicklungsauftrag und ändere bei dieser ersten Orientierung keine Dateien.
```
