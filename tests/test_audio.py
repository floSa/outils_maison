from tools.audio import nom_depuis_tags


def test_nom_depuis_tags_piste_paddee():
    tags = {"piste": "3", "artiste": "Daft Punk", "titre": "Aerodynamic"}
    assert nom_depuis_tags(tags, "{piste} - {artiste} - {titre}") == "03 - Daft Punk - Aerodynamic"


def test_nom_depuis_tags_champ_manquant():
    tags = {"piste": "", "artiste": "Air", "titre": ""}
    # champs vides tolérés, pas de KeyError
    assert nom_depuis_tags(tags, "{artiste} - {titre}").startswith("Air")


def test_nom_depuis_tags_nettoie_caracteres():
    tags = {"artiste": "AC/DC", "titre": "T.N.T."}
    out = nom_depuis_tags(tags, "{artiste} - {titre}")
    assert "/" not in out  # slash retiré (illégal dans un nom de fichier)
