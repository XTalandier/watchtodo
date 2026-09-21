# watchtodo

**Une TUI pour suivre un `TODO.md` sans jamais quitter le terminal.**
Navigation clavier et souris, dépliage des descriptions, rechargement à chaud.
Zéro dépendance.

L'idée : garder un panneau ouvert en permanence à côté de son éditeur, avec l'état
réel du chantier. Le fichier reste un markdown parfaitement lisible — sur GitHub,
dans un éditeur, ou à l'œil nu.

```
Kidyscope — TODO · 3/31 (10%)  28 ouverts
─────────────────────────────────────────────────────────────────────────────
🔴 Sécurité (2/9)
 ▸ ✔ SEC-1 IDOR capsules : scope enfant sur findAll/findOne + create @api
 ▸ ○ SEC-2 IDOR milestones : findOne et verifyChildAccess !haute @api
 ▸ ✔ SEC-3 Commentaires au niveau tribu : assumé, décision produit @api
 ▸ ○ SEC-4 Factoriser les deux verifyAccess identiques !basse @api
 ▸ ◐ SEC-6 Test API du scope enfant !haute @test

🔴 Produit (0/4)
 ▸ ○ PROD-1 Sceller les capsules côté serveur !haute @api
 ▸ ○ PROD-2 Worker de déverrouillage !haute @api
   ○ PROD-3 Écran de révélation à l'ouverture !moyenne @mobile

🟠 Dette (0/10)
 ▸ ○ DET-1 media-proxy sans backpressure !moyenne @api
 ▾ ○ DET-2 fanOutToFamily séquentiel !basse @api
     `notifications.service.ts:84` — await dans une boucle.

↑↓ naviguer · ⏎/clic déplier · e tout · a masquer faits · q quitter
```

> La commande s'appelle `watchdodo`, le dépôt `watchtodo`. C'est volontaire :
> le nom du binaire est resté celui du prototype.

---

## Installation

Node ≥ 18, rien d'autre. Pas de `npm install`, pas de `node_modules`.

```bash
git clone git@github.com:XTalandier/watchtodo.git ~/projects/watchtodo
ln -s ~/projects/watchtodo/bin/watchdodo ~/.local/bin/watchdodo
```

Remplacez `~/.local/bin` par n'importe quel répertoire de votre `PATH`.

---

## Utilisation

```bash
watchdodo                 # le TODO.md de la racine git courante
watchdodo fichier.md      # un fichier précis
watchdodo -o              # n'affiche que les items ouverts
watchdodo --once          # sortie texte, sans TUI — pipeable
watchdodo --init          # crée un TODO.md d'exemple
```

### Raccourcis

| Touche | Action |
|---|---|
| `↑` `↓` · `j` `k` | naviguer d'un item à l'autre |
| `⏎` · clic | déplier / replier la description |
| `→` `←` | déplier / replier |
| molette | défiler |
| `Tab` | section suivante |
| `e` / `c` | tout déplier / tout replier |
| `a` | masquer / réafficher les items faits |
| `g` / `G` | premier / dernier item |
| `q` | quitter |

`watchtodo` est en **lecture seule**. Il n'écrit jamais dans votre fichier : vous
cochez dans votre éditeur, l'affichage se met à jour tout seul. Aucun risque de
conflit d'écriture si un autre outil modifie le fichier en même temps.

---

## Format

````markdown
# Titre du projet

## 🔴 Catégorie

- [ ] **SEC-1** Libellé court sur une seule ligne `@api` `!haute`
  Une ligne de description. Deux au grand maximum.

- [~] **SEC-2** Un item en cours `@api` `!moyenne`

- [x] **SEC-3** Un item terminé `@api`
````

| Élément | Règle |
|---|---|
| `#` | titre du fichier, affiché en en-tête |
| `##` | catégorie — emoji libre |
| `[ ]` `[~]` `[x]` | à faire · en cours · fait |
| `**ID**` | juste après la case. Court et stable : `SEC-1`, `DET-3` |
| `` `@tag` `` | zone concernée — libre |
| `` `!priorité` `` | `!haute` `!moyenne` `!basse` |
| description | lignes indentées de 2 espaces, sous l'item |

**Les métadonnées sont obligatoirement entre backticks.** Sans cette contrainte,
un libellé contenant `@nestjs/throttler` ou `!important` serait avalé comme une
métadonnée. Les backticks lèvent l'ambiguïté et rendent les tags visibles comme
des puces sur GitHub.

L'`ID` est facultatif mais recommandé : c'est ce qui permet de désigner un item
sans ambiguïté — à l'oral, dans un ticket, ou dans un prompt.

Tout le reste du markdown — prose, tableaux, listes — est **ignoré par l'outil
mais conservé dans le fichier**. Votre `TODO.md` reste un document, pas un format
de données déguisé.

---

## Avec un agent IA

Le format a été pensé pour être écrit par un agent et lu par un humain.

Déposez ceci dans `~/.claude/CLAUDE.md` (chargé dans toutes vos sessions Claude
Code, quel que soit le répertoire) :

```markdown
Quand je demande une todo ou un plan de travail persistant, écris-le dans
`TODO.md` à la racine du repo, au format watchtodo :

- `#` titre, `##` catégorie
- `- [ ] **ID-1** Libellé `@zone` `!haute``
- description : lignes indentées de 2 espaces, 1 ligne, 2 maximum
- métadonnées toujours entre backticks
```

L'agent lit l'état courant avec `watchdodo --once`, qui produit une sortie texte
compacte sans séquences d'échappement.

---

## Notes d'implémentation

**Pourquoi pas `curses`.** La première version visait Python, dont le module
`curses` est dans la bibliothèque standard. Mesure faite sur macOS :

```
ncurses version           : 6.0.20150808
libncurses.5.4.dylib      ← la lib système, figée en 2015
BUTTON5_PRESSED (molette) : False
```

Pas de molette, et pas de protocole SGR 1006 — donc des clics faux au-delà de
223 colonnes. En Node il n'y a rien entre le programme et le terminal : on émet
`\x1b[?1000;1006h` et on parse les événements soi-même. Clic, molette, largeur
arbitraire, et aucune dépendance système.

Le démarrage de Node est deux fois plus lent que celui de Python (28 ms contre
14 ms sur la machine de test). Sans importance pour un processus qui tourne en
continu — ce chiffre n'a pas pesé dans le choix.

**Rechargement.** Le fichier est surveillé par `fs.watchFile` (polling 200 ms)
plutôt que par `fs.watch`. Beaucoup d'éditeurs enregistrent par
`rename`-remplacement atomique, ce qui fait perdre la cible à `fs.watch` mais
laisse `watchFile` parfaitement opérationnel.

**État conservé.** Les items dépliés sont mémorisés par `ID`, pas par position.
Un rechargement qui réordonne, ajoute ou supprime des items préserve ce qui était
ouvert, et la sélection reste sur le même item.

**Largeur des colonnes.** Les emojis comptent pour deux colonnes. Sans cela, les
troncatures et le remplissage de la ligne sélectionnée seraient décalés dès qu'un
titre de catégorie contient un emoji.

---

## Licence

MIT — voir [LICENSE](LICENSE).
