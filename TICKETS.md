# Tickets — faites évoluer la console OpsReady

La console OpsReady démarre volontairement petite : une console **lecture seule**
(agents, shifts, alerts, sites) avec authentification JWT. Les 12 tickets ci-dessous
la font évoluer, un pas à la fois, vers un vrai outil de gestion du risque fatigue :
planification, tableau de bord, télémétrie Orbe, acquittement des alertes...

Suivez l'ordre suggéré : chaque ticket s'appuie sur les précédents. Les descriptions
donnent le **comportement attendu**, pas le code — la conception vous appartient.
Chaque ticket se termine par sa **Definition of Done** : la liste de cases qui dit
exactement quand il est terminé.

> 📖 **Guide visuel** : le cas d'usage de chaque ticket (qui s'en sert, pourquoi) et
> une maquette du rendu attendu sont dans
> [docs/guide-tickets.html](docs/guide-tickets.html) — un seul fichier autonome,
> à ouvrir dans un navigateur.

**Convention de langue** : le code s'écrit en anglais (identifiants, routes, champs
JSON, commentaires) ; les libellés affichés et les messages d'erreur utilisateur
restent en français. Cette doc garde les descriptions en français et les références
de code en anglais.

**Convention d'architecture à respecter dans tous les tickets** (voir README,
section « Architecture du back-end : trois étages ») : le blueprint est un contrôleur
mince (lire la requête, valider, appeler un service, répondre) ; la logique métier va
dans `app/services/` ; l'accès aux données (requêtes ORM SQLAlchemy) va dans
`app/repositories/`, les modèles étant définis dans `app/models.py`. Exemples
concrets : T02 ajoutera la règle anti-chevauchement dans `shift_service.py` et la
création (`session.add(Shift(...))`) dans `shift_repository.py`, T06 la formule de
fatigue dans un service dédié, T11 la transition d'état d'acquittement dans
`alert_service.py`.

## Definition of Done commune à tous les tickets

Un ticket est **terminé** quand toutes ces cases sont cochées, en plus de la
Definition of Done spécifique du ticket :

- [ ] Le comportement décrit est implémenté **au bon endroit** : contrôleur mince,
      règles métier en service, accès données en repository.
- [ ] La suite de tests back passe : `cd backend && .venv/Scripts/python -m pytest` —
      les 19 tests existants restent verts et le nouveau comportement est couvert
      par au moins un test (statuts de succès et d'erreur).
- [ ] Le front compile : `cd frontend && npx ng build` (sauf ticket back pur).
- [ ] La fonctionnalité a été **vue fonctionner** : navigateur pour ce qui touche à
      l'UI, curl (ou client HTTP) pour un endpoint back pur.
- [ ] Le code suit la convention de langue : identifiants anglais, messages
      utilisateur français, pas de règle métier dans un contrôleur.
- [ ] La case du ticket est cochée dans le README (section « Suivi des tâches »).

| # | Ticket | Difficulté | Couche |
|---|---|---|---|
| T01 | Planning hebdomadaire (grille) | ★★☆ | Front |
| T02 | Planification d'un shift (POST + règles métier) | ★★☆ | Back |
| T03 | Dialog de planification | ★★☆ | Front |
| T04 | Vue d'ensemble (métriques + dashboard) | ★★★ | Back + Front |
| T05 | Fiche agent + consultation télémétrie | ★★★ | Back + Front |
| T06 | Ingestion Orbe + modèle de fatigue | ★★★ | Back |
| T07 | Création d'agent | ★☆☆ | Back + Front |
| T08 | Modification d'agent | ★☆☆ | Back + Front |
| T09 | Modification de shift | ★☆☆ | Back + Front |
| T10 | Suppression de shift | ★☆☆ | Back |
| T11 | Acquittement des alertes | ★★☆ | Back + Front |
| T12 | Compteur d'alertes dans la navigation | ★☆☆ | Front |

---

## T01 — Planning hebdomadaire (grille) `★★☆` Front

**Quoi.** Nouvelle page `/planning` : grille hebdomadaire agents x 7 jours pour un
site choisi. C'est la pièce maîtresse de la console : prenez le temps de la soigner.

**Spécification.**
- Sélecteur de site (défault : premier site) + navigation semaine (précédente /
  « Cette semaine » / suivante).
- Une ligne par agent (hors `SUSPENDED`), une colonne par jour du lundi au dimanche,
  en-tête avec le jour courant marqué.
- Chaque cellule affiche les shifts du jour sous forme de pastilles colorées par type
  (`DAY` clair, `NIGHT` sombre, `ON_CALL` pointillée) avec les horaires `07h-19h` ;
  pastille à **contour ambré** quand `predicted_fatigue_score >= 65`, infobulle avec
  type, score et commentaire. Légende sous la grille.
- Données : `GET /api/shifts?site_id=...&from=...&to=...&page_size=500` (l'endpoint
  existe déjà), agents via `GET /api/agents?site_id=...`.
- Débordement horizontal contrôlé (grille `min-width` + scroll dans la carte).

**But pédagogique.** Signals `computed` (jours de la semaine, index agent+date →
shifts), `DatePipe`, CSS Grid, scroll horizontal, `forkJoin` pour charger agents +
shifts.

### Definition of Done

- [ ] La route `/planning` apparaît dans le menu latéral et est protégée par
      l'authentification (redirection vers `/login` sinon).
- [ ] À l'ouverture : semaine courante (lundi → dimanche) du premier site, avec les
      shifts correctement placés sur les bons jours, y compris un shift qui
      chevauche minuit (ex. NIGHT 19h → 7h le lendemain).
- [ ] Navigation ‹ / › change de semaine et recharge les données ; « Cette semaine »
      revient à la semaine courante ; le jour courant est marqué dans l'en-tête.
- [ ] Chaque pastille est colorée par type, affiche les horaires, et porte un
      contour ambré quand `predicted_fatigue_score >= 65` ; l'infobulle montre type,
      score et commentaire.
- [ ] Les agents `SUSPENDED` n'apparaissent pas ; un agent sans shift sur le site
      n'apparaît pas non plus.
- [ ] La grille défile dans sa carte (aucun scroll horizontal de la page entière).
- [ ] Les états chargement (voile ou skeleton), erreur (message + réessayer) et vide
      (message) sont gérés.

---

## T02 — Planification d'un shift (POST) `★★☆` Back

**Quoi.** `POST /api/shifts` (rôles `PLANNER`, `ADMIN`) : la première écriture de
l'application, qui transforme la console en vrai outil de planification.

**Spécification.**
- Contrôleur : corps validé par pydantic (`extra="forbid"`) : `agent_id`, `type` ∈
  {DAY, NIGHT, ON_CALL}, `starts_at`, `ends_at` (datetime naive local, fuseau ignoré),
  `comment` optionnel.
- Service : erreurs `422 BUSINESS_RULE` si `ends_at <= starts_at` ; `404
  AGENT_NOT_FOUND` ; `409 SHIFT_OVERLAP` (details contenant le shift existant) si
  l'agent a déjà un shift non annulé qui chevauche : `starts_at < existant.ends_at AND
  ends_at > existant.starts_at` ; `site_id` déduit du site de l'agent ; `status`
  calculé selon maintenant (`SCHEDULED` / `IN_PROGRESS` / `COMPLETED`) ;
  `predicted_fatigue_score` estimé, par exemple base selon type (DAY 45, NIGHT 68,
  ON_CALL 30) pondérée par le `fatigue_index` actuel de l'agent, bornée 0..100.
- Repository : création (`session.add`) + lecture enrichie (agent + site).
- Réponse 201 avec le shift enrichi.

**But pédagogique.** Validation pydantic, règle métier async en service, écriture en
repository, codes d'erreur métier.

### Definition of Done

- [ ] `POST /api/shifts` sans jeton → 401 ; avec un jeton `SUPERVISOR` → 403
      `FORBIDDEN` (details avec `required_roles`) ; avec `PLANNER` ou `ADMIN` → 201.
- [ ] Création valide → 201, corps enrichi (`agent_last_name`, `site_name`),
      `predicted_fatigue_score` entre 0 et 100, `status` cohérent avec les dates
      envoyées (tester un shift passé, un en cours, un futur).
- [ ] `ends_at <= starts_at` → 422 `BUSINESS_RULE`, message en français.
- [ ] `agent_id` inexistant → 404 `AGENT_NOT_FOUND`.
- [ ] Chevauchement → 409 `SHIFT_OVERLAP` avec `details` contenant le shift existant
      (au moins son `id` et son `type`) ; un shift `CANCELLED` ne bloque pas.
- [ ] `type` hors énumération ou champ inconnu → 422 `VALIDATION`.
- [ ] La règle anti-chevauchement est dans `shift_service.py`, la création dans
      `shift_repository.py` : le contrôleur ne contient ni l'une ni l'autre.
- [ ] Tests : création valide (3 cas de statut) + les 4 erreurs + 403.

---

## T03 — Dialog de planification `★★☆` Front

**Quoi.** Boîte de dialogue « Planifier une garde » ouverte depuis le planning (T01),
visible seulement si l'utilisateur peut planifier (rôle `PLANNER`/`ADMIN` — la
propriété `canPlanify` est à créer dans `AuthService`).

**Spécification.** Formulaire réactif : site (charge les agents du site), agent,
type, date native, heure de début/fin (menus 0..23), commentaire. Une fin antérieure
au début bascule automatiquement au lendemain (nuit 22h → 6h). Erreurs de l'API
affichées en ligne dans le dialog (409 chevauchement typiquement), snackbar +
rafraîchissement de la grille à la fermeture avec succès.

**But pédagogique.** Reactive forms, `MatDialog` et `MAT_DIALOG_DATA`, cascade de
listes, traduction des erreurs API en messages utilisateur.

### Definition of Done

- [ ] `canPlanify` (ADMIN ou PLANNER) est créée dans `AuthService` ; le bouton
      « Planifier une garde » n'apparaît que pour ces rôles (vérifié en se
      connectant avec `sofia.lambert` puis `nadia.fournier`).
- [ ] Le select Agent se rempli depuis le site choisi ; changer de site recharge la
      liste et réinitialise l'agent.
- [ ] Formulaire réactif : les champs requis bloquent la soumission avec un message
      sous le champ ; le bouton est désactivé pendant l'envoi.
- [ ] Une fin antérieure au début bascule automatiquement au lendemain (nuit
      22h → 6h testée à la main).
- [ ] Une erreur de l'API (409 chevauchement typiquement) s'affiche en ligne dans le
      dialog, en français, et laisse l'utilisateur corriger.
- [ ] Succès → dialog fermé, snackbar de confirmation, grille rafraîchie avec la
      nouvelle pastille au bon endroit.
- [ ] « Annuler » ferme le dialog sans appel réseau.

---

## T04 — Vue d'ensemble (métriques + dashboard) `★★★` Back + Front

**Quoi.** Le tableau de bord de la console : un endpoint de métriques côté back, une
page d'accueil côté front.

**Back — `GET /api/metrics/overview`** (connecté) :
- `kpis` : score moyen de fatigue, agents ok/warning/critical (tranches fatigue_index
  < 40, 40-74, >= 75), alertes ouvertes, shifts de nuit de la semaine, taux de
  couverture (part des créneaux jour et nuit pourvus sur la semaine, tous sites).
- `repartition` (3 tranches), `tendance` (moyenne de `predicted_fatigue_score` des
  shifts par jour, lundi → dimanche, `null` si pas de shift), `site_loads` (effectif,
  score moyen, critiques par site), `recent_alerts` (5), `upcoming_heavy_shifts`
  (6 prochains shifts à venir avec score >= 65).

**Front — page `/overview`** : 4 cartes KPI (composant `StatCard` à créer), anneau
de répartition et courbe de tendance (composants chart.js à créer : `DonutChart`
avec total au centre et légende intégrée, `LineChart` avec séries, remplissage doux,
`spanGaps`), listes « alertes récentes » et « shifts à surveiller », table « charge
par site », skeletons de chargement. Route par défaut de l'application.

**But pédagogique.** Agrégations ORM (`func.count`, `func.avg`, `GROUP BY`),
calculs de couverture en Python, chart.js dans Angular, conception de composants
d'affichage réutilisables.

### Definition of Done

- [ ] `GET /api/metrics/overview` sans jeton → 401 ; avec jeton → 200.
- [ ] La réponse contient `kpis`, `repartition`, `tendance`, `site_loads`,
      `recent_alerts`, `upcoming_heavy_shifts` ; sur le jeu de test, la somme des
      `repartition[].nb` égale le nombre total d'agents et `tendance` compte
      exactement 7 jours (lundi → dimanche).
- [ ] Les tranches de fatigue sont respectées : un agent à `fatigue_index` 80 compte
      dans `critical`, un à 50 dans `warning`, un à 10 dans `ok` (test dédié).
- [ ] `tendance` met `score_moyen` à `null` les jours sans shift au lieu d'inventer
      une valeur.
- [ ] La route `/overview` est la route par défaut (`/` redirige vers elle) et
      l'entrée du menu a une icône.
- [ ] La page affiche les 4 cartes KPI, l'anneau avec le total au centre, la courbe
      avec les 7 jours, les deux listes et la table par site, sans erreur console.
- [ ] Les états chargement (skeletons), erreur (réessayer) et vide (aucune alerte
      ouverte) sont gérés.
- [ ] Tests back : structure de la réponse + cohérence des KPI sur le jeu de test
      (3 agents, 1 critique, 1 warning).

---

## T05 — Fiche agent + consultation télémétrie `★★★` Back + Front

**Quoi.** La fiche détaillée d'un agent et la lecture des relevés du capteur Orbe.

**Back.**
- `GET /api/agents/{id}` : fiche + 5 derniers shifts + alertes non résolues +
  dernier relevé ; `404 AGENT_NOT_FOUND` sinon.
- `GET /api/telemetry/agents/{id}/readings?hours=48` : série horaire ascendante,
  bornée 1..336 h (la table `readings` est déjà remplie par le seed).

**Front — page `/agents/:id`** : en-tête (initiales, grade, site, statut), cartes
mesures (indice coloré par tranche, dernier sommeil, dernier relevé), graphique
télémétrie **double axe** (fréquence cardiaque à gauche en bpm, HRV à droite en ms)
avec sélecteur de plage 24 h / 48 h / 7 j, tables derniers shifts et alertes ouvertes.
Navigation depuis la ligne du registre des agents (colonne chevron ou clic de ligne,
à vous de choisir).

**But pédagogique.** Route paramétrée (`withComponentInputBinding` ou
`ActivatedRoute`), chart.js multi-axes, jointures de lecture enrichies en ORM.

### Definition of Done

- [ ] `GET /api/agents/999` → 404 `AGENT_NOT_FOUND` ; `GET /api/agents/1` → 200 avec
      la fiche + `recent_shifts` (5 max, triés du plus récent) + `open_alerts` +
      `latest_reading`.
- [ ] `GET /api/telemetry/agents/1/readings?hours=48` → 200, série ascendante ;
      `hours` est borné (0 ou 1000 → respectivement 1 et 336) ; agent inconnu → 404.
- [ ] Depuis le registre, cliquer un agent ouvre `/agents/:id` ; l'URL directe
      fonctionne aussi (rechargement de page compris).
- [ ] La fiche affiche : avatar initiales, grade/profession/site, badge de statut,
      indice coloré par tranche, dernier sommeil, dernier relevé (FC, HRV,
      température, date).
- [ ] Le graphique télémétrie trace deux courbes sur deux axes (bpm à gauche, ms à
      droite) ; le sélecteur 24 h / 48 h / 7 j recharge la série.
- [ ] Un agent sans alerte ouverte ni shift affiche des états vides composés, pas
      des sections vides.
- [ ] Un id inexistant dans l'URL → état « agent introuvable » avec retour au
      registre.
- [ ] Tests back : 200 enrichi, 404, bornes du paramètre `hours`.

---

## T06 — Ingestion Orbe + modèle de fatigue `★★★` Back

**Quoi.** `POST /api/telemetry/readings` (connecté), la passerelle du capteur : c'est
par là que la console devient vivante, les relevés entrants recalculant l'état des
agents.

**Spécification.**
- Corps : `agent_id`, `heart_rate` (30-220), `hrv` (5-200), `temperature` (33-42),
  `recorded_at` optionnel (défaut : maintenant, normalisé naive local).
- Insertion du reading, puis recalcul du `fatigue_index` de l'agent :
  `index = 40 + (45 - hrv) * 1.2 + (heart_rate - 70) * 0.6 + (7 - sleep) * 7`, borné
  0..100, arrondi à 0,1 ; `sleep` = `last_sleep_hours` de l'agent (7 par défaut).
- Si `index >= 85` : création automatique d'une alerte `FATIGUE_CRITICAL`
  (`CRITICAL`) nommant l'agent.
- Réponse `202` : `{reading, fatigue_index, alert_created}`.

**But pédagogique.** Logique métier avec effets de bord (deux écritures + une
alerte) répartie entre service et repository, tests de la formule aux bornes,
cohérence entre tables.

### Definition of Done

- [ ] Sans jeton → 401 ; corps hors plages (`heart_rate` 300, `hrv` 0,
      `temperature` 50) → 422 `VALIDATION` avec le champ fautif dans `details` ;
      agent inconnu → 404.
- [ ] Ingestion valide → 202 avec `reading` (dont `recorded_at` normalisé sans
      microsecondes), `fatigue_index` recalculé et `alert_created`.
- [ ] La formule est implémentée **dans un service** et exacte : pour un agent avec
      `last_sleep_hours` = 8, un relevé FC 60 / HRV 60 donne 9.0 ; FC 95 / HRV 18
      avec 6.5 h de sommeil donne 90.9 (tests avec ces chiffres).
- [ ] L'indice borné : un relevé très favorable ne descend pas sous 0, un très
      mauvais ne dépasse pas 100.
- [ ] `agent.fatigue_index` est mis à jour en base (vérifié par un `GET
      /api/agents/{id}` après ingestion).
- [ ] Un indice >= 85 crée une alerte `FATIGUE_CRITICAL` de sévérité `CRITICAL`,
      visible via `GET /api/alerts?agent_id=...` ; `alert_created` vaut `true` dans
      la réponse.
- [ ] Tests : formule (2 jeux chiffrés), bornes, 422, 404, alerte automatique.

---

## T07 — Création d'agent `★☆☆` Back + Front

**Quoi.** `POST /api/agents` (rôles `PLANNER`, `ADMIN`) + le formulaire de création
côté front, à concevoir.

**Back.** Validation pydantic (`site_id`, `last_name`, `first_name`, `email` normalisé
en minuscules, `profession`, `grade`, `hired_on`, `status` par défaut `ACTIVE`) ;
`404 SITE_NOT_FOUND`, `409 EMAIL_ALREADY_USED` ; indice initial 20, sommeil 7 ;
réponse 201.

**Front.** Bouton + dialog ou panneau dans le registre des agents, champs avec
validation, affichage des erreurs API (409 en ligne sous le champ email).

**But pédagogique.** POST complet de bout en bout, unicité, retour d'erreur champ
par champ.

### Definition of Done

- [ ] `POST /api/agents` sans jeton → 401 ; `SUPERVISOR` → 403 ; `PLANNER`/`ADMIN`
      → 201.
- [ ] Création valide → 201 : `status` vaut `ACTIVE`, `fatigue_index` vaut 20,
      `last_sleep_hours` vaut 7 ; l'email fourni en majuscules est stocké en
      minuscules ; l'agent apparaît dans `GET /api/agents`.
- [ ] `site_id` inexistant → 404 `SITE_NOT_FOUND` ; email déjà pris → 409
      `EMAIL_ALREADY_USED` ; champ inconnu ou email vide → 422.
- [ ] Le formulaire (dialog ou panneau) valide les champs requis côté front, et une
      erreur 409 s'affiche en français sous le champ email.
- [ ] Après création réussie, la liste des agents est rafraîchie et le nouvel agent
      est visible (recherche par son nom).
- [ ] Tests back : 201 (+ valeurs par défaut), 404, 409, 403, normalisation email.

---

## T08 — Modification d'agent `★☆☆` Back + Front

**Quoi.** `PATCH /api/agents/{id}` (rôle `ADMIN` uniquement) : modification partielle
de `status`, `grade`, `profession` (les champs `None` sont ignorés). Front : menu de
changement de statut sur la liste ou la future fiche, réservé aux admins.

**But pédagogique.** PATCH partiel, contrôle de rôle strict (403 `FORBIDDEN` avec
details `required_roles`), UI conditionnée au rôle.

### Definition of Done

- [ ] `PATCH /api/agents/1` sans jeton → 401 ; `PLANNER` ou `SUPERVISOR` → 403
      `FORBIDDEN` ; `ADMIN` → 200.
- [ ] Modification partielle : `{"status": "LEAVE"}` ne touche qu'au statut (grade
      et profession inchangés dans la réponse) ; un statut hors énumération → 422.
- [ ] Agent inexistant → 404 `AGENT_NOT_FOUND` ; champ inconnu (`extra="forbid"`)
      → 422.
- [ ] La modification est persistante : un `GET /api/agents` après le PATCH montre
      le nouveau statut.
- [ ] Front : le changement de statut est actionnable depuis l'UI, visible seulement
      pour ADMIN, et la ligne du registre reflète le nouveau statut sans
      rechargement manuel.
- [ ] Tests back : PATCH partiel, 403 (deux rôles), 404, 422.

---

## T09 — Modification de shift `★☆☆` Back + Front

**Quoi.** `PATCH /api/shifts/{id}` (rôles `PLANNER`, `ADMIN`) : changement de `status`
(SCHEDULED / IN_PROGRESS / COMPLETED / CANCELLED) et de `comment` uniquement ; `404
SHIFT_NOT_FOUND`. Front : menu d'action sur un shift (fiche agent, planning).

**But pédagogique.** Cycle de vie d'une ressource, contrainte de champs modifiables,
permissions combinées.

### Definition of Done

- [ ] `PATCH /api/shifts/1` sans jeton → 401 ; `SUPERVISOR` → 403 ; `PLANNER` ou
      `ADMIN` → 200.
- [ ] Seuls `status` et `comment` sont modifiables : une tentative de changer
      `starts_at` ou `agent_id` → 422 (champs interdits), pas une mise à jour
      silencieuse.
- [ ] Un `status` hors énumération → 422 `VALIDATION` ; shift inexistant → 404
      `SHIFT_NOT_FOUND`.
- [ ] La modification est persistante et visible dans `GET /api/shifts`.
- [ ] Front : le changement de statut d'un shift est actionnable dans l'UI (planning
      ou fiche agent) et la pastille/ligne reflète le nouveau statut.
- [ ] Tests back : changement de statut, changement de commentaire, 403, 404, 422
      (champ interdit et statut invalide).

---

## T10 — Suppression de shift `★☆☆` Back

**Quoi.** `DELETE /api/shifts/{id}` (rôle `ADMIN`) : suppression réelle, `409
SHIFT_IN_PROGRESS` si le shift est en cours, `204` sinon. Front (optionnel) : bouton
poubelle dans le planning ou la fiche, avec confirmation.

**But pédagogique.** DELETE + code 204, règle d'irréversibilité, test du 403 planner.

### Definition of Done

- [ ] `DELETE /api/shifts/1` sans jeton → 401 ; `PLANNER` → 403 ; `ADMIN` → 204.
- [ ] Un shift `IN_PROGRESS` → 409 `SHIFT_IN_PROGRESS` et il existe toujours après
      la tentative.
- [ ] Après un 204, le shift n'apparaît plus dans `GET /api/shifts` ni via
      `GET /api/shifts/{id}` (404) — ce GET individuel fait partie du ticket s'il
      n'existe pas encore.
- [ ] Shift inexistant → 404 `SHIFT_NOT_FOUND`.
- [ ] (Si front) la suppression passe par une confirmation ; annuler ne supprime
      rien.
- [ ] Tests back : 204, 409 en cours, 403, 404.

---

## T11 — Acquittement des alertes `★★☆` Back + Front

**Quoi.** Le cycle de traitement des alertes : la fin du flux lecture seule. Un
superviseur prend connaissance d'une alerte et la marque comme traitée.

**Back.** `PATCH /api/alerts/{id}/acknowledge` (rôles `SUPERVISOR`, `ADMIN`, corps
vide) : refuse `404 ALERT_NOT_FOUND` (inconnue) et `409 ALERT_ALREADY_HANDLED` si le
statut n'est plus `NEW` ; pose `status = ACKNOWLEDGED`, `acknowledged_by` (utilisateur
courant, disponible via `g.user`) et `acknowledged_at` ; renvoie l'alerte enrichie du
nom d'acqureur.

**Front.** Colonne d'actions dans la liste des alertes : bouton « Acquitter » sur les
alertes `NEW`, visible seulement si `canAcknowledge` (à créer dans `AuthService`),
snackbar de confirmation, rafraîchissement de la liste, note de rôle pour les
planners.

**But pédagogique.** Transition d'état refusée une fois consommée (409), identité du
token (`g.user`), permissions croisées supervisor/planner.

### Definition of Done

- [ ] `PATCH /api/alerts/999/acknowledge` → 404 `ALERT_NOT_FOUND` ; sans jeton →
      401 ; `PLANNER` → 403 ; `SUPERVISOR`/`ADMIN` → 200.
- [ ] Acquittement réussi → 200 : `status` vaut `ACKNOWLEDGED`, `acknowledged_at`
      est rempli, `acknowledged_by_name` porte le **nom de l'utilisateur connecté**
      (vérifié avec deux comptes différents).
- [ ] Deuxième acquittement sur la même alerte → 409 `ALERT_ALREADY_HANDLED`, en
      français.
- [ ] Une alerte déjà `RESOLVED` ne peut pas être acquittée (même 409).
- [ ] Front : le bouton « Acquitter » n'apparaît que sur les alertes `NEW` et que
      pour SUPERVISOR/ADMIN ; après clic, snackbar + la liste reflète le nouveau
      statut ; les autres rôles voient une note de rôle.
- [ ] Le compteur du filtre « Nouvelles » descend après acquittement.
- [ ] Tests back : 200 (avec nom d'acqureur), 409 (deux fois), 403, 404.

---

## T12 — Compteur d'alertes dans la navigation `★☆☆` Front

**Quoi.** Pastille rouge dans le menu latéral sur l'entrée « Alertes », montrant le
nombre d'alertes `NEW`, rechargée à chaque navigation et toutes les 30 s.

**Piste.** Dans le `Shell` : `AlertsService.list({status: 'NEW', limit: 200})` →
signal, rechargement sur `NavigationEnd` + `interval` RxJS proprement désabonné.

**But pédagogique.** État partagé au niveau du layout, polling RxJS avec
désabonnement, rafraîchissement sur navigation.

### Definition of Done

- [ ] L'entrée « Alertes » du menu affiche une pastille avec le nombre d'alertes
      `NEW` (valeur cohérente avec la page Alertes filtre « Nouvelles »).
- [ ] La pastille disparaît quand le compte est zéro (pas de « 0 » affiché).
- [ ] Après un acquittement (T11) ou toute navigation, le compteur se met à jour
      sans rechargement manuel de la page.
- [ ] Le polling toutes les 30 s fonctionne et est **proprement désabonné** : pas de
      requêtes résiduelles après destruction du composant (vérifié dans l'onglet
      Réseau des devtools en naviguant puis en changeant de page).
- [ ] Une erreur réseau ne casse pas l'application : le compteur retombe à 0 ou
      reste, sans message bloquant.
