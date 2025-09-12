"""
But du test
-----------
Vérifier que `add_features` lève une erreur explicite (ValueError)
lorsque des colonnes indispensables sont absentes du DataFrame d'entrée.

Contexte
--------
`add_features` attend au minimum ces colonnes :
- "revenu_mensuel"
- "poste"
- "augementation_salaire_precedente"
- "annees_depuis_la_derniere_promotion"

Si l’une manque, la fonction doit échouer rapidement et clairement
(plutôt que de produire des NaN ou des erreurs plus loin dans le pipeline).
"""

import pandas as pd
import pytest
from futurisys_churn_api.api.preprocessing import add_features

def test_add_features_missing_columns_raises():
    # On fournit volontairement un DF incomplet : seulement 2 colonnes sur 4
    df = pd.DataFrame({
        "revenu_mensuel": [1000],
        "poste": ["Manager"],
    })

    # Attendu : ValueError, car il manque
    # "augementation_salaire_precedente" et
    # "annees_depuis_la_derniere_promotion"
    with pytest.raises(ValueError):
        add_features(df)
