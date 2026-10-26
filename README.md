# Console OpsReady — application d'entraînement AUM-Biosync

Application interne d'exercice, calquée sur le métier d'[AUM-Biosync](https://www.aumbiosync.com/) :
deeptech française experte en **chronobiologie**, qui gère le risque fatigue des équipes à
horaires atypiques (pompiers, soignants, industrie 3x8) via ses produits **OPTeam**
(planification), **OpsReady** (préparation opérationnelle) et **Orbe** (capteur biométrique).

La Console OpsReady est le back-office qui orchestre tout cela. **Elle démarre
volontairement petite** : une console lecture seule (agents, shifts, alertes, sites)
avec authentification JWT. Les 12 tickets de [TICKETS.md](TICKETS.md) la font
évoluer pas à pas vers un vrai outil (planification, dashboard, télémétrie,
acquittement) — chacun avec sa Definition of Done, et le suivi de l'avancement se
coche dans ce README (section [Suivi des tâches](#suivi-des-tâches)).

📖 **Guide visuel des tickets** : [docs/guide-tickets.html](docs/guide-tickets.html)
illustre chaque ticket avec son cas d'usage (qui s'en sert et pourquoi) et une
maquette du rendu attendu. Un seul fichier autonome, à ouvrir dans un navigateur.

## Stack

| Couche | Techno |
|---|---|
| Back-end | Python 3.11, [Quart](https://quart.palletsprojects.com/) (async), [SQLAlchemy 2.0](https://docs.sqlalchemy.org/) async (ORM), SQLite via aiosqlite, PyJWT, pydantic, hypercorn |
| Base de données | SQLite (`backend/aumbiosync.db`), peuplée par un script de seed réaliste |
| Front-end | Angular 21 (standalone, signals), Angular Material 21 (thème M3) |
| Tests | pytest + pytest-asyncio (client de test Quart) |

```
AumBiosyncTraining/
├── backend/                  # API Quart
│   ├── app/
│   │   ├── __init__.py       # fabrique create_app()
│   │   ├── config.py         # config env (AUM_SECRET_KEY, AUM_DATABASE)
│   │   ├── db.py             # moteur SQLAlchemy async, session par requête
│   │   ├── models.py         # modèles ORM (source de vérité du schéma SQLite)
│   │   ├── errors.py         # ApiError + format d'erreur JSON stable
│   │   ├── security.py       # hash mots de passe, JWT, décorateur require_auth()
│   │   ├── validation.py     # lecture du corps JSON
│   │   ├── blueprints/       # contrôleurs HTTP : auth, sites, agents, shifts, alerts
│   │   ├── services/         # logique métier : classes *_service (une par domaine)
│   │   └── repositories/     # accès aux données : classes *_repository, requêtes ORM
│   ├── scripts/seed.py       # peuplement via les modèles ORM (dates relatives à maintenant)
│   ├── tests/                # 19 tests pytest
│   └── run.py                # python run.py (dev) / hypercorn (prod)
├── frontend/                 # Angular 21
│   └── src/app/
│       ├── core/             # modèles, AuthService (signaux), interceptors
│       ├── services/         # Agents, Shifts, Alerts, Sites
│       ├── shared/           # empty-state, helpers fatigue
│       ├── layout/shell.*    # coquille : sidenav + barre + profil
│       └── features/         # login, agents (liste), alerts
└── TICKETS.md                # 12 tickets d'évolution, chacun avec sa Definition of Done
```

### Architecture du back-end : trois étages

Le back-end suit la séparation contrôleur / service / repository, comme dans une
vraie application :

- **Les blueprints sont des contrôleurs HTTP** (`app/blueprints/`) : ils lisent la
  requête (`request.args`, corps JSON), valident avec pydantic, appellent un service
  et renvoient la réponse. Ils n'écrivent **jamais** de SQL ni de règle métier.
- **Les services portent la logique métier et l'orchestration** (`app/services/`) :
  une classe par domaine, exposée en instance unique (`agent_service.py`,
  `shift_service.py`, `alert_service.py`, `site_service.py`, `auth_service.py`,
  `user_service.py`). Bornes de pagination, règles de transition d'état, calculs :
  ils ne touchent **jamais** à `request` ni à la réponse HTTP.
- **Les repositories possèdent l'accès aux données** (`app/repositories/`) : le seul
  étage qui parle à la base, via l'ORM SQLAlchemy (`select`, `session`). Même
  convention de nommage (`agent_repository.py`, `shift_repository.py`…). Pas de
  règle métier dedans, juste des requêtes et du mapping vers des dictionnaires.

Chaque service et repository est une **classe** exposée comme instance unique en bas
du fichier (ex. `shift_service = ShiftService()`) : simple à importer, simple à
remplacer par un mock dans les tests. Les blueprints, eux, restent en fonctions de
route : c'est la convention canonique Flask/Quart.

Règle à respecter dans tous les tickets : une nouvelle route = un contrôleur mince
**+** une fonction de service **+** une fonction de repository ; une règle métier
(anti-chevauchement, acquittement…) va dans le service, où elle est testable sans HTTP.

Convention de langue : **le code est en anglais** (identifiants, tables, champs JSON,
routes, commentaires), les **libellés affichés** dans la console et les **messages
d'erreur** utilisateur restent en français (produit interne français), tout comme
cette documentation.

## Démarrage

### 1. Back-end (port 5000)

```bash
cd backend
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt      # Windows
.venv/Scripts/python -m scripts.seed --reset       # crée + peuple la base
.venv/Scripts/python run.py
```

Linux/macOS : remplacer `.venv/Scripts/` par `.venv/bin/`.

Pour un mode « production like » : `hypercorn --bind 0.0.0.0:5000 "app:create_app()"`.

### 2. Front-end (port 4200)

```bash
cd frontend
npm install
npm start            # ng serve, proxy /api -> http://127.0.0.1:5000
```

Ouvrir [http://localhost:4200](http://localhost:4200). En développement, les appels
`/api` passent par le proxy du dev-server (`proxy.conf.json`) ; le CORS du back-end
n'est utile que pour d'autres origines.

### Comptes de démonstration (mot de passe : `OpsReady2026!`)

| Email | Rôle | Droits |
|---|---|---|
| `sofia.lambert@aum-bio.fr` | SUPERVISOR | consultation |
| `nadia.fournier@aum-bio.fr` | PLANNER | consultation |
| `admin@aum-bio.fr` | ADMIN | consultation (les écritures arrivent avec les tickets) |

## Routine de travail sur un ticket

Le réflexe à installer, dans cet ordre :

1. **Lire le ticket** dans [TICKETS.md](TICKETS.md) : comportement attendu, règles
   métier, et sa **Definition of Done** — la liste de cases qui dit exactement quand
   le ticket est terminé. Elle s'ajoute à la DoD commune (tests verts, front
   compilé, fonctionnalité vue fonctionner) définie en tête du fichier.
2. **Explorer la base** : chaque ticket a un patron existant à imiter. Côté back-end,
   un contrôleur (`app/blueprints/agents.py`), **son service** (`app/services/agent_service.py`)
   et **son repository** (`app/repositories/agent_repository.py`), le décorateur de rôle
   (`security.py`, fonction `require_auth`), les erreurs métier (`errors.py`) et les
   helpers de test (`tests/conftest.py` : `token()`, `auth_headers()`). Côté front, un
   service (`frontend/src/app/services/`), une page (`frontend/src/app/features/`) et
   les helpers (`frontend/src/app/shared/fatigue.ts`).
3. **Back-end d'abord**, front ensuite. Entre les deux, tester la route à la main :

   ```bash
   curl -s -X POST http://127.0.0.1:5000/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"admin@aum-bio.fr","password":"OpsReady2026!"}'
   ```

4. **Vérifier avant de passer à la suite** — les tests existants doivent rester verts
   et la compilation front doit passer :

   ```bash
   cd backend && .venv/Scripts/python -m pytest -v
   cd ../frontend && npx ng build
   ```

5. **Regarder au navigateur** ([localhost:4200](http://localhost:4200)) : avec
   `python run.py` + `npm start` lancés, le front se recharge tout seul à chaque
   sauvegarde. Cochez ensuite la tâche dans le suivi ci-dessous.

## Suivi des tâches

Douze tickets font évoluer la console, du plus simple au plus costaud : chacun
ajoute une fonctionnalité et a sa Definition of Done dans [TICKETS.md](TICKETS.md).
Pour marquer une tâche comme faite, remplacez `[ ]` par `[x]` ici même (et, si vous
voulez, ajoutez la date ou une note entre parenthèses). Ordre suggéré, du plus simple au plus costaud.

### Niveau découverte

- [ ] **T01 — Planning hebdomadaire** (front, ★★☆) : page `/planning`, grille agents x 7 jours par site, navigation de semaines, pastilles colorées par type de garde.
- [ ] **T02 — Planification d'une garde** (back, ★★☆) : `POST /api/shifts` avec anti-chevauchement (409), fin > début (422), score de fatigue et statut automatiques.
- [ ] **T03 — Dialog de planification** (front, ★★☆) : formulaire site puis agent, nuit passant au lendemain, erreurs de l'API affichées en ligne.

### Niveau intermédiaire

- [ ] **T04 — Vue d'ensemble** (back + front, ★★★) : `GET /api/metriques/vue-ensemble` (KPIs, répartition, tendance 7 jours, couverture) + page dashboard avec stat-cards, donut et courbe.
- [ ] **T05 — Fiche agent + télémétrie** (back + front, ★★★) : `GET /api/agents/{id}`, série de relevés Orbe, page `/agents/:id` avec graphique double axe FC/HRV.
- [ ] **T06 — Ingestion Orbe** (back, ★★★) : `POST /api/telemetry/releves`, recalcul de l'indice de fatigue (formule dans le ticket), alerte critique automatique >= 85.

### Niveau confirmation

- [ ] **T07 — Création d'agent** (back + front, ★☆☆) : `POST /api/agents` (email unique, site inconnu) + formulaire de création.
- [ ] **T08 — Modification d'agent** (back + front, ★☆☆) : `PATCH /api/agents/{id}` réservé ADMIN, modification partielle (statut, grade).
- [ ] **T09 — Modification de garde** (back + front, ★☆☆) : `PATCH /api/shifts/{id}`, statut et commentaire seulement, rôles Planner/Admin.
- [ ] **T10 — Suppression de garde** (back, ★☆☆) : `DELETE /api/shifts/{id}` réservé ADMIN, interdite sur une garde en cours (409).
- [ ] **T11 — Acquittement des alertes** (back + front, ★★☆) : `PATCH /api/alerts/{id}/acknowledge` (409 si déjà traitée) + bouton conditionné au rôle superviseur.
- [ ] **T12 — Compteur d'alertes** (front, ★☆☆) : pastille rouge dans le menu latéral, rechargée à chaque navigation et toutes les 30 s.

## API (version minimale, lecture seule)

Toutes les routes (sauf `/api/health` et `/api/auth/login`) exigent
`Authorization: Bearer <jeton>`. Erreurs au format :
`{"error": {"code", "message", "details"}}` (codes anglais, messages français).

| Méthode | Route | Description |
|---|---|---|
| POST | `/api/auth/login` | jeton JWT (8 h) |
| GET | `/api/auth/me` | profil courant |
| GET | `/api/health` | sonde de vivacité |
| GET | `/api/sites` | sites + effectifs |
| GET | `/api/agents` | liste filtrable (`q`, `site_id`, `statut`) |
| GET | `/api/shifts` | planning paginé (`from`, `to`, `site_id`, `agent_id`, `status`, `page`, `page_size`) |
| GET | `/api/alerts` | filtres `status`, `severity`, `agent_id`, `limit` |

Les écritures (planification, acquittement, CRUD agents), la télémétrie Orbe et les
métriques **ne sont pas encore implémentées** : ce sont les tickets
[TICKETS.md](TICKETS.md).

## Tests

```bash
cd backend
.venv/Scripts/python -m pytest -v
```

19 tests couvrent l'authentification (jeton, expiration implicite, erreurs) et la
consultation filtrée des quatre ressources, avec contrôle systématique du 401.

## Données de démonstration

Le seed (`python -m scripts.seed --reset`) génère **dates relatives à maintenant** :
3 sites (SDIS 21 Dijon, CHU Dijon, Plastival Mâcon), 24 agents nommés, 85 shifts de la
semaine courante (postes 24/48, 2-3-2, 3x8, astreinte week-end), 14 alertes et 1 152
relevés Orbe avec profils circadiens (utiles dès le ticket T05/T06). Trois agents sont
toujours « en nuit » pour que les listes soient vivantes à toute heure. Les horaires
sont stockés en ISO local sans fuseau (choix documenté, simplificateur pour la démo).
Les contenus métier (noms, professions, messages d'alerte) restent français : ce sont
des données produit réalistes.

## Au-delà des tickets

Quelques idées pour plus tard, une fois les 12 tickets de [TICKETS.md](TICKETS.md) bouclés :

- **Refresh token** : `POST /api/auth/refresh` + interceptor qui renouvelle le jeton sans déconnecter.
- **PostgreSQL** : remplacer SQLite (`asyncpg` / `SQLAlchemy 2.0 async`) sans casser les tests.
- **Simulateur Orbe** : script qui pousse des relevés toutes les minutes (ticket T06 requis)
  avec dérive de fatigue, et observer les alertes se créer.
- **Export CSV** du planning de la semaine (`GET /api/shifts/export.csv`).
- **Docker** : Dockerfile back + front (nginx), `docker compose up`.

## Notes

- Les données sont synthétiques ; n'y voyez rien d'exact sur l'entreprise réelle.
- `AUM_SECRET_KEY` doit être définie hors développement (JWT HS256).
- Le front suppose que l'API est servie sur la même origine en production (sinon
  ajuster `CORS_ORIGINES` et l'URL de l'API).
