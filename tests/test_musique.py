from pathlib import Path

from tools import musique


def _f(chemin: Path, contenu: str = "x"):
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(contenu, encoding="utf-8")


def _biblio(racine: Path):
    # ArtisteA
    _f(racine / "ArtisteA" / "Album1" / "track.flac")
    _f(racine / "ArtisteA" / "Album1" / "cover.jpg")            # single + cover
    _f(racine / "ArtisteA" / "Album2" / "song.mp3")             # single sans cover
    _f(racine / "ArtisteA" / "AlbumComplet" / "01.flac")        # vrai album → ignoré
    _f(racine / "ArtisteA" / "AlbumComplet" / "02.flac")
    _f(racine / "ArtisteA" / "AlbumExtra" / "hit.flac")         # single + .nfo → à vérifier
    _f(racine / "ArtisteA" / "AlbumExtra" / "notes.nfo")
    _f(racine / "ArtisteA" / "AlbumJunk" / "tune.flac")         # single + junk → traité
    _f(racine / "ArtisteA" / "AlbumJunk" / "Thumbs.db")
    # ArtisteB
    _f(racine / "ArtisteB" / "AlbumX" / "track.flac")           # même nom, autre artiste
    _f(racine / "ArtisteB" / "AlbumX" / "front.png")


def test_analyser_classement(tmp_path):
    _biblio(tmp_path)
    plan = musique.analyser(tmp_path)

    traites = {sa.album.name for sa in plan.a_traiter}
    verifier = {sa.album.name for sa in plan.a_verifier}
    assert traites == {"Album1", "Album2", "AlbumJunk", "AlbumX"}
    assert verifier == {"AlbumExtra"}
    # AlbumComplet (2 titres) n'apparaît nulle part
    assert "AlbumComplet" not in traites | verifier


def test_previsualiser_collision_meme_artiste(tmp_path):
    _f(tmp_path / "Art" / "A" / "same.flac")
    _f(tmp_path / "Art" / "B" / "same.flac")
    plan = musique.analyser(tmp_path)
    noms = sorted(mv.audio_dst.name for mv in musique.previsualiser(plan))
    assert noms == ["same (2).flac", "same.flac"]


def test_appliquer_et_structure(tmp_path):
    _biblio(tmp_path)
    plan = musique.analyser(tmp_path)
    musique.appliquer(plan, tmp_path)

    singA = tmp_path / "ArtisteA" / "Singles"
    assert (singA / "track.flac").is_file()
    assert (singA / "cover_track.jpg").is_file()       # cover renommée
    assert (singA / "song.mp3").is_file()
    assert (singA / "tune.flac").is_file()
    assert (tmp_path / "ArtisteB" / "Singles" / "cover_track.png").is_file()

    # dossiers single supprimés, le reste conservé
    assert not (tmp_path / "ArtisteA" / "Album1").exists()
    assert not (tmp_path / "ArtisteA" / "AlbumJunk").exists()
    assert (tmp_path / "ArtisteA" / "AlbumComplet").is_dir()
    assert (tmp_path / "ArtisteA" / "AlbumExtra").is_dir()   # à vérifier → laissé


def test_annuler_restaure(tmp_path):
    _biblio(tmp_path)
    plan = musique.analyser(tmp_path)
    musique.appliquer(plan, tmp_path)
    musique.annuler(tmp_path)

    assert (tmp_path / "ArtisteA" / "Album1" / "track.flac").is_file()
    assert (tmp_path / "ArtisteA" / "Album1" / "cover.jpg").is_file()
    assert (tmp_path / "ArtisteB" / "AlbumX" / "front.png").is_file()
