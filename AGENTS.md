# Anweisungen für die Skill-Entwicklung

- Sprich den Benutzer immer mit du an.
- Kanonisches Projektverzeichnis ist
  `/Users/dj/Source/codex.skill.manage-git-project`.
  Hier wird ausschließlich der Skill `manage-git-project` weiterentwickelt.
- Verwende `$manage-git-project` vor Dateiänderungen und zum Aufgabenabschluss.
  Lies die aktuelle Skill-Fassung unter `manage-git-project/SKILL.md`.
  Integrationsziel ist `main`. Kleine aufeinanderfolgende Aufgaben verwenden
  den bestehenden Checkout; zusätzliche Branches nur bei konkretem Bedarf mit
  Präfix `codex/`, zusätzliche Worktrees ausschließlich unter `.local/worktrees/`.
- Der installierte Verweis `~/.agents/skills/manage-git-project` zeigt auf
  `manage-git-project/` in diesem Repository. Änderungen dort wirken unmittelbar
  auf die benutzerweite Installation; berücksichtige das bei Selbständerungen.
  Benutzerweite AGENTS-Regeln nicht ohne ausdrücklichen Auftrag ändern.
- Skill-Inhalt gehört unter `manage-git-project/`, Entwicklungs- und
  Prüfnachweise unter `docs/`. Temporäre Dateien, Test-Repositories und
  Aufgabenstatus gehören in ignorierte Unterverzeichnisse von `.local/`.
  Keine Entwicklungsdateien in `server.hostinger` oder anderen Projekten ablegen.
- Prüfe vor Schreibarbeit andere aktive Agenten und Prozesse. Der kooperative
  Skill-Lock ersetzt diese Prüfung nicht. Fremde Änderungen und einzigartige
  Daten erhalten; denselben Checkout nicht gleichzeitig verändern.
- Bei Änderungen an Prüflogik die Verhaltenstests mit echten lokalen
  Git-Repositories ausführen. Änderungen an der Anleitung auf gültige
  Verweise, klare Freigabegrenzen und ihre Auswirkungen auf den Ablauf prüfen.
  Keine neue Plattformabnahme aus vorhandenen Tests ableiten.
- Dokumentiere relevante Entscheidungen und Prüfungen knapp im Projekt.
  Die importierten Nachweise unter `docs/origin/` sind datierte historische
  Belege und werden nicht nachträglich an neue Pfade oder Ergebnisse angepasst.
- Committe nach erfolgreicher Prüfung nur aufgabenbezogene Änderungen und
  integriere abgeschlossene eigene Zweige in `main`. Bereinige erledigte eigene
  Zweige und Arbeitskopien gemäß Skill. Das öffentliche Remote `origin` ist
  `https://github.com/DataJockey13/codex.skill.manage-git-project`.
  Pushe geprüfte abgeschlossene Änderungen auf `origin/main`. Tags und Releases
  werden bei entsprechendem Auftrag veröffentlicht.
