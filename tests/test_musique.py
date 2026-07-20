from pathlib import Path

from tools import musique


def _f(chemin: Path, contenu: str = "x"):
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(contenu, encoding="utf-8")


def _biblio(racine: Path):
    # single + 1 pochette (sans numéro)
    _f(racine / "ArtisteA" / "Album1" / "track.flac")
    _f(racine / "ArtisteA" / "Album1" / "cover.jpg")
    # single AVEC numéro de piste → retiré
    _f(racine / "ArtisteA" / "Album2" / "01 - Ring Ring.mp3")
    # single + 3 pochettes (cas des 661) → traité, toutes déplacées
    _f(racine / "ArtisteA" / "Triple" / "hit.flac")
    _f(racine / "ArtisteA" / "Triple" / "AlbumArtSmall.jpg")
    _f(racine / "ArtisteA" / "Triple" / "Cover.jpg")
    _f(racine / "ArtisteA" / "Triple" / "Folder.jpg")
    # single + junk → traité, junk part en corbeille avec le dossier
    _f(racine / "ArtisteA" / "AlbumJunk" / "tune.flac")
    _f(racine / "ArtisteA" / "AlbumJunk" / "Thumbs.db")
    # vrai album (2 titres) → ignoré
    _f(racine / "ArtisteA" / "AlbumComplet" / "01.flac")
    _f(racine / "ArtisteA" / "AlbumComplet" / "02.flac")
    # single + sous-dossier → à vérifier (non traité)
    _f(racine / "ArtisteA" / "AvecDossier" / "hit.flac")
    _f(racine / "ArtisteA" / "AvecDossier" / "bonus" / "x.flac")
    # autre artiste, même contexte
    _f(racine / "ArtisteB" / "AlbumX" / "song.flac")
    _f(racine / "ArtisteB" / "AlbumX" / "front.png")


def test_titre_sans_numero():
    assert musique._titre_sans_numero("01 - Ring Ring") == "Ring Ring"
    assert musique._titre_sans_numero("07. Titre") == "Titre"
    assert musique._titre_sans_numero("Sans numero") == "Sans numero"
    # pas de séparateur → on ne touche pas (protège « 99 Luftballons »)
    assert musique._titre_sans_numero("99 Luftballons") == "99 Luftballons"


def test_analyser_classement(tmp_path):
    _biblio(tmp_path)
    plan = musique.analyser(tmp_path)
    traites = {sa.album.name for sa in plan.a_traiter}
    verifier = {sa.album.name for sa in plan.a_verifier}
    assert traites == {"Album1", "Album2", "Triple", "AlbumJunk", "AlbumX"}
    assert verifier == {"AvecDossier"}
    assert "AlbumComplet" not in traites | verifier


def test_previsualiser_numero_et_pochettes(tmp_path):
    _biblio(tmp_path)
    plan = musique.analyser(tmp_path)
    par_dst = {mv.audio_dst.name: mv for mv in musique.previsualiser(plan)}
    # numéro retiré
    assert "Ring Ring.mp3" in par_dst
    # 3 pochettes déplacées, renommées au titre (avec suffixes anti-collision)
    triple = par_dst["hit.flac"]
    covers = sorted(dst.name for _, dst in triple.sidecars)
    assert covers == ["hit (2).jpg", "hit (3).jpg", "hit.jpg"]


def test_previsualiser_collision_meme_artiste(tmp_path):
    _f(tmp_path / "Art" / "A" / "same.flac")
    _f(tmp_path / "Art" / "B" / "same.flac")
    plan = musique.analyser(tmp_path)
    noms = sorted(mv.audio_dst.name for mv in musique.previsualiser(plan))
    assert noms == ["same (2).flac", "same.flac"]


def test_appliquer_structure_et_corbeille(tmp_path):
    _biblio(tmp_path)
    avant = sum(1 for p in tmp_path.rglob("*") if p.is_file())

    plan = musique.analyser(tmp_path)
    res = musique.appliquer(plan, tmp_path)
    assert res.erreurs == []

    singA = tmp_path / "ArtisteA" / "Singles"
    assert (singA / "track.flac").is_file() and (singA / "track.jpg").is_file()
    assert (singA / "Ring Ring.mp3").is_file()          # numéro retiré
    assert (singA / "hit.flac").is_file()
    assert {p.name for p in singA.glob("hit*.jpg")} == {"hit.jpg", "hit (2).jpg", "hit (3).jpg"}
    assert (singA / "tune.flac").is_file()
    assert (tmp_path / "ArtisteB" / "Singles" / "song.png").is_file()

    # dossiers vidés déplacés en corbeille (PAS supprimés), junk préservé dedans
    corb = tmp_path / musique.NOM_CORBEILLE
    assert (corb / "ArtisteA" / "Album1").is_dir()
    assert (corb / "ArtisteA" / "AlbumJunk" / "Thumbs.db").is_file()   # junk pas perdu
    assert not (tmp_path / "ArtisteA" / "Album1").exists()

    # à vérifier / vrai album laissés en place
    assert (tmp_path / "ArtisteA" / "AlbumComplet").is_dir()
    assert (tmp_path / "ArtisteA" / "AvecDossier").is_dir()

    # aucune perte de fichier (rien supprimé, tout déplacé)
    apres = sum(1 for p in tmp_path.rglob("*") if p.is_file())
    assert apres == avant + 1  # +1 = le journal .singles_undo.json


def test_annuler_restaure(tmp_path):
    _biblio(tmp_path)
    plan = musique.analyser(tmp_path)
    musique.appliquer(plan, tmp_path)
    musique.annuler(tmp_path)

    assert (tmp_path / "ArtisteA" / "Album1" / "track.flac").is_file()
    assert (tmp_path / "ArtisteA" / "Album1" / "cover.jpg").is_file()
    assert (tmp_path / "ArtisteA" / "Album2" / "01 - Ring Ring.mp3").is_file()
    assert (tmp_path / "ArtisteA" / "Triple" / "Cover.jpg").is_file()
    assert (tmp_path / "ArtisteA" / "AlbumJunk" / "Thumbs.db").is_file()
    assert (tmp_path / "ArtisteB" / "AlbumX" / "front.png").is_file()
