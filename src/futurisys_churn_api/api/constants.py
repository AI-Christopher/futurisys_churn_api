"""
Constantes et mappings utilisés par le préprocessing de l'API Futurisys Churn.

Contenu :
- MOYENNES_POSTE : salaire moyen (mensuel) par intitulé de poste — sert à calculer
  la feature dérivée `ratio_revenu_poste = revenu_mensuel / (moyenne_poste + 1)`.
- MAPPING_POSTE : encodage ordinal des intitulés de poste (entiers).
- MAPPING_FREQ : encodage ordinal de la fréquence de déplacement (entiers).

Notes importantes
-----------------
1) Les clés doivent correspondre EXACTEMENT aux valeurs reçues en entrée API
   (après normalisation éventuelle), sinon `map()` produira des NaN.
   C’est OK si vous réalignez ensuite les colonnes avec `reindex(..., fill_value=0)`.

2) Pour la fréquence, on accepte à la fois "Fréquent" (avec accent) et "Frequent"
   (sans accent) et on les mappe vers la même valeur.

3) En cas d’ajout de nouveaux postes ou nouvelles valeurs, pensez à :
   - mettre à jour ces mappings,
   - re-générer/valider `models/input_features.json` si cela impacte l’encodage,
   - re-tester le pipeline (pytest).
"""

# Salaire moyen mensuel par poste (utilisé pour ratio_revenu_poste)
MOYENNES_POSTE = {
    "Représentant Commercial": 2626.0,
    "Consultant": 3237.17,
    "Assistant de Direction": 3239.97,
    "Ressources Humaines": 4235.75,
    "Cadre Commercial": 6924.28,
    "Tech Lead": 7295.14,
    "Manager": 7528.76,
    "Directeur Technique": 16033.55,
    "Senior Manager": 17181.67,
}

# Encodage ordinal des postes (entiers croissants arbitraires mais stables)
MAPPING_POSTE = {
    'Représentant Commercial': 0, 
    'Consultant': 1, 
    'Assistant de Direction': 2, 
    'Ressources Humaines': 3, 
    'Cadre Commercial': 4, 
    'Tech Lead': 5, 
    'Manager': 6, 
    'Directeur Technique': 7, 
    'Senior Manager': 8
}

# Encodage ordinal de la fréquence de déplacement
# (on gère les deux variantes "Fréquent"/"Frequent")
MAPPING_FREQ = {
    'Aucun': 0, 
    'Occasionnel': 1, 
    "Fréquent": 2,
    "Frequent": 2,
}