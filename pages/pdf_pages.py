from pathlib import Path

import streamlit as st

from tools.pdf import compter_pages, pivoter_pages, supprimer_pages
from ui import FILETYPES_PDF, champ_fichier

st.title("🔧 Manipuler les pages d'un PDF")
st.caption("Supprime ou pivote des pages d'un PDF.")

pdf = champ_fichier(
    "Chemin du PDF",
    "pdf_pages_pdf",
    filetypes=FILETYPES_PDF,
    placeholder="C:/Users/.../document.pdf",
)

if not pdf:
    st.stop()

src = Path(pdf)
if not src.is_file():
    st.error(f"PDF introuvable : {src}")
    st.stop()

try:
    nb = compter_pages(src)
except Exception as e:
    st.error(f"Lecture impossible : {e}")
    st.stop()

st.info(f"{nb} pages.")


def _parse_pages(txt: str) -> set[int]:
    """Convertit « 1, 3-5, 8 » en {1, 3, 4, 5, 8}."""
    pages: set[int] = set()
    for bloc in txt.replace(" ", "").split(","):
        if not bloc:
            continue
        if "-" in bloc:
            a, b = bloc.split("-")
            pages.update(range(int(a), int(b) + 1))
        else:
            pages.add(int(bloc))
    return pages


action = st.radio("Action", ["Supprimer des pages", "Pivoter des pages"], horizontal=True)
saisie = st.text_input("Pages concernées (ex. 1, 3-5, 8)", value="")

if action == "Pivoter des pages":
    angle = st.selectbox("Rotation", [90, 180, 270], index=0)
    pivoter_tout = st.checkbox("Toutes les pages", value=False)

if st.button("Appliquer", type="primary"):
    try:
        pages = _parse_pages(saisie) if saisie.strip() else set()
        if action == "Supprimer des pages":
            if not pages:
                st.warning("Indique au moins une page.")
                st.stop()
            sortie = supprimer_pages(src, pages, src.with_name(f"{src.stem}_modifie.pdf"))
        else:
            cibles = None if pivoter_tout else pages
            if not pivoter_tout and not pages:
                st.warning("Indique des pages ou coche « Toutes les pages ».")
                st.stop()
            sortie = pivoter_pages(src, angle, src.with_name(f"{src.stem}_modifie.pdf"), cibles)
        st.success(f"Créé : `{sortie}`")
    except ValueError:
        st.error("Saisie de pages invalide.")
    except Exception as e:
        st.error(str(e))
