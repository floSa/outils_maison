from pathlib import Path

import streamlit as st

from tools.pdf import deproteger, proteger

st.title("🔒 Protéger / déprotéger un PDF")
st.caption("Ajoute ou retire un mot de passe sur un PDF.")

action = st.radio("Action", ["Protéger", "Déprotéger"], horizontal=True)
chemin = st.text_input("Chemin du PDF", placeholder="C:/Users/.../document.pdf")
mot_de_passe = st.text_input("Mot de passe", type="password")

if not chemin:
    st.stop()

src = Path(chemin)
if not src.is_file():
    st.error(f"PDF introuvable : {src}")
    st.stop()

if st.button(action, type="primary", disabled=not mot_de_passe):
    try:
        if action == "Protéger":
            sortie = proteger(src, mot_de_passe)
        else:
            sortie = deproteger(src, mot_de_passe)
        st.success(f"Créé : `{sortie}`")
    except ValueError as e:
        st.error(str(e))
    except Exception as e:
        st.error(f"Échec : {e}")
