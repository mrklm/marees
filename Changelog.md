# Changelog

Toutes les évolutions notables du projet sont documentées dans ce fichier.

Ce projet suit le principe du Semantic Versioning (SemVer) :
MAJEUR.MINEUR.CORRECTIF

---

## [0.1.1] - 2026-02-26

### Modifié

 - La localité n'est plus Cancale par defaut, il faut remplir le champ

---

## [0.1.0] - 2026-02-26

### Ajouté

- Création de l'application **TideBuilder**
  - Générateur de fichiers annuels de marées pour HorlogeLune
- Interface graphique Tkinter comprenant :
  - Champ **Localité**
  - Champ **Année**
  - Zone de collage des données brutes
  - Aperçu dynamique du fichier `.txt`
  - Boutons : **Importer**, **Vérifier**, **Enregistrer**
  - Boutons rapides : **Coller**, **Tout effacer**

---

### Parsing texte brut

- Détection automatique :
  - Mois (français, avec ou sans accents)
  - Jour
  - Marée haute / basse
- Extraction des heures et hauteurs
- Extraction des coefficients
- Gestion des lignes parasites (lune, saint, lever/coucher, etc.)
- Déduplication automatique
- Tri chronologique garanti

---

### Parsing HTML (code source page marées)

- Détection automatique du format HTML
- Détection du mois via ancre `id="jj-mm"`
- Extraction :
  - Marées hautes / basses
  - Heures
  - Hauteurs
  - Coefficients
- Association correcte du coefficient à la marée haute correspondante
- Commit sécurisé des blocs `tide-line`

---

### Génération du fichier de sortie

Format strict :


YYYY-MM-DD;HH:MM;H|L;hauteur_m;coef


- Ajout automatique des entêtes :
Marees <localité> <année> (extrait: ...)
Format: YYYY-MM-DD;HH:MM;H|L;hauteur_m;coef
- Indication des mois manquants :
[MANQUANT] Mois: janvier
- Indication des jours manquants :
[MANQUANT] Jour: 2026-03-14
- Nom d'export automatique :

MAREE<YY>_<localite>.txt


---

### Vérification avancée

- Détection des mois manquants
- Détection des jours manquants
- Détection des marées hautes sans coefficient
- Détection des doublons
- Détection d’ordre chronologique invalide
- Détection de trous temporels suspects (> 9h30)
- Détection de trous majeurs (> 18h)

---

### Thèmes

- Bibliothèque interne de thèmes :
- Sombres
- Clairs
- Pouêt-Pouêt
- Thème aléatoire au démarrage
- Sélecteur de thème via Combobox
- Application dynamique sur :
- ttk widgets
- Text widgets

---

### Technique

- Architecture modulaire
- Parser HTML basé sur `HTMLParser`
- Gestion des erreurs non bloquantes
- Déduplication robuste
- Version interne via `__VERSION__`
- Dépôt Git initialisé
- Tag Git `v0.1.0`
- Publication sur GitHub

---

Version initiale stable.