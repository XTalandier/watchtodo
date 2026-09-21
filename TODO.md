# watchtodo — TODO

Cases : `[ ]` à faire · `[~]` en cours · `[x]` fait
Méta : `@zone` et `!haute` / `!moyenne` / `!basse`
Affichage : `watchdodo`

## 🎯 Fonctionnalités

- [ ] **UI-1** Filtrer par tag ou par priorité `@tui` `!moyenne`
  Une touche pour ne garder que `!haute`, ou qu'un `@tag` donné.

- [ ] **UI-2** Recherche incrémentale avec `/` `@tui` `!basse`

- [ ] **UI-3** Mode écriture optionnel pour cocher depuis la TUI `@tui` `!basse`
  Volontairement absent en v1 : évite tout conflit avec un agent qui édite le fichier.

- [ ] **UI-4** Repli des catégories entières `@tui` `!basse`

## 🤖 claudeagent

- [x] **AG-1** TUI de suivi des agents Claude Code `@tui`
  Liste live, navigation clavier et souris, détail de l'activité.

- [ ] **AG-2** Distinguer « terminé » de « bloqué » `@tui` `!moyenne`
  Aujourd'hui c'est la fraîcheur du fichier qui décide — un agent lent paraît fini.

- [ ] **AG-3** Ouvrir le transcript complet depuis la TUI `@tui` `!basse`
  Une touche pour envoyer le JSONL dans le pager.

## 🔌 Compatibilité

- [ ] **CMP-1** Valider le rendu hors tmux `@compat` `!moyenne`
  iTerm2, Terminal.app, Ghostty, Alacritty — surtout le support SGR 1006.

- [ ] **CMP-2** Vérifier sous Linux `@compat` `!moyenne`

- [x] **CMP-3** Souris SGR validée sous tmux 3.7 / tmux-256color `@compat`

- [x] **CMP-4** Largeur des emojis prise en compte dans les troncatures `@compat`

## 📦 Distribution

- [ ] **PKG-1** Publier sur npm `@packaging` `!basse`
  Vérifier d'abord que le nom `watchtodo` est libre.

- [ ] **PKG-2** Formule Homebrew `@packaging` `!basse`

- [ ] **DOC-1** Traduire le README en anglais `@doc` `!basse`

- [ ] **DOC-2** Enregistrer un GIF de démonstration pour le README `@doc` `!moyenne`

## 🧪 Qualité

- [ ] **TST-1** Tests du parseur sur des markdown tordus `@test` `!moyenne`
  Items sans ID, méta en double, indentation irrégulière, fichier vide.

- [ ] **TST-2** Test de la machine à états d'entrée `@test` `!basse`
  Séquences d'échappement coupées entre deux lectures du stdin.
