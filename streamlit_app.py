import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import zipfile
import io
import openpyxl
from pandas import ExcelWriter
from streamlit_sortables import sort_items
#pmm
# Charger le fichier Excel
file_path = 'NORMES_NOV_24.xlsx'
excel_data = pd.ExcelFile(file_path)

# Liste des groupes d'âge (onglets du fichier)
age_groups = excel_data.sheet_names

# Initialisation des clés de session
if "age_selected" not in st.session_state:
    st.session_state["age_selected"] = False
if "scores_entered" not in st.session_state:
    st.session_state["scores_entered"] = False

# Titre de l'application
st.title("Batterie COMPRENDRE")

# Étape 1 : Sélection de l'âge
st.header("Étape 1 : Sélectionnez le groupe d'âge")
selected_age_group = st.selectbox("Sélectionnez le groupe d'âge de l'enfant :", age_groups)
child_id = st.text_input("Saisissez l'ID de l'enfant :", value="", placeholder="ID de l'enfant")

# Confirmation de l'ID et de l'âge
if st.button("Passer à l'étape suivante"):
    if not child_id.strip():  # Vérifiez si l'ID est vide
        st.error("Veuillez saisir un ID valide avant de continuer.")
    else:
        st.session_state["age_selected"] = True
        st.session_state["child_id"] = child_id  # Enregistrez l'ID dans la session
        st.success(f"ID {child_id} et âge {selected_age_group} confirmés.")
        
# Fonction pour charger les données d'un onglet
def load_age_data(sheet_name, excel_file):
    try:
        return pd.read_excel(excel_file, sheet_name=sheet_name, engine="openpyxl")
    except Exception as e:
        st.error(f"Erreur lors du chargement des données : {e}")
        return pd.DataFrame()

# Étape 2 : Saisie des scores
if st.session_state["age_selected"]:
    st.header("Étape 2 : Entrez les scores")

    # Charger les données pour le groupe d'âge sélectionné
    age_data = load_age_data(selected_age_group, excel_data)

    if age_data.empty:
        st.error("Impossible de charger les données pour le groupe d'âge sélectionné.")
    else:
        # Filtrer les colonnes pertinentes
        age_data = age_data[["Tâche", "Moyenne", "Ecart-type", "Minimum", 
                             "5e percentile", "10e percentile", "Q1", 
                             "Q2 - mediane", "Q3", "90e percentile", "Maximum"]].dropna()

        # Liste des catégories avec les tâches regroupées par paires
        categories = {
            "Langage": [
                ("Discrimination Phonologique", "Décision Lexicale Auditive"),
                ("Mots Outils", "Stock Lexical"),
                ("Compréhension Syntaxique", "Mots Outils - BOEHM")
            ],
            "Mémoire de Travail Verbale": [
                ("Mémoire de travail verbale endroit empan", "Mémoire de travail verbale endroit brut"),
                ("Mémoire de travail verbale envers empan", "Mémoire de travail verbale envers brut")
            ],
            "Mémoire de Travail Non Verbale": [
                ("Mémoire de travail non verbale endroit empan", "Mémoire de travail non verbale endroit brut"),
                ("Mémoire de travail non verbale envers empan", "Mémoire de travail non verbale envers brut")  
            ],   
            "Mise à jour Verbale": [
                ("Mise à jour verbale empan", "Mise à jour verbale score"),
            ],
            "Mise à jour Non Verbale": [
                ("Mise à jour non verbale empan", "Mise à jour non verbale score"),
            ],
            "INHIB verbale": [
                ("Inhibition verbale congruent score", "Inhibition verbale incongruent score"),
                ("Inhibition verbale congruent temps", "Inhibition verbale incongruent temps")
            ],
            "INHIB non verbale": [
                ("Inhibition non verbale congruent score", "Inhibition non verbale incongruent score"),
                ("Inhibition non verbale congruent temps", "Inhibition non verbale incongruent temps")
            ]
        }

        # Collecte des scores utilisateur et calculs d'interférences
        user_scores = []
        inhibition_scores = {}
        missing_norms = []

        for category, task_pairs in categories.items():
            st.subheader(category)
            for task1, task2 in task_pairs:
                col1, col2 = st.columns(2)

                # Colonne 1 : Saisie pour task1
                with col1:
                    if task1 in age_data["Tâche"].values:
                        score1 = st.text_input(f"{task1} :", value="")
                        if score1.strip():  # Si l'utilisateur a saisi une valeur
                            try:
                                score1 = float(score1)
                                user_scores.append({"Tâche": task1, "Score Enfant": score1})
                                inhibition_scores[task1] = score1
                            except ValueError:
                                st.error(f"Valeur non valide pour {task1}. Veuillez entrer un nombre.")
                                inhibition_scores[task1] = score1
                    else:
                        st.warning(f"Pas de normes disponibles pour {task1}")
                        missing_norms.append(task1)

                # Colonne 2 : Saisie pour task2
                with col2:
                    if task2 in age_data["Tâche"].values:
                        score2 = st.text_input(f"{task2} :", value="")
                        if score2.strip():  # Si l'utilisateur a saisi une valeur
                            try:
                                score2 = float(score2)
                                user_scores.append({"Tâche": task2, "Score Enfant": score2})
                                inhibition_scores[task2] = score2
                            except ValueError:
                                st.error(f"Valeur non valide pour {task2}. Veuillez entrer un nombre.")
                                inhibition_scores[task2] = score2
                    else:
                        st.warning(f"Pas de normes disponibles pour {task2}")
                        missing_norms.append(task2)

        # Calculs des interférences
                # Calculs des interférences
        interferences = {
            "Inhibition verbale interférence score": (
                inhibition_scores.get("Inhibition verbale incongruent score", 0) 
                - inhibition_scores.get("Inhibition verbale congruent score", 0)
            ),
            "Inhibition non verbale interférence score": (
                inhibition_scores.get("Inhibition non verbale incongruent score", 0) 
                - inhibition_scores.get("Inhibition non verbale congruent score", 0)
            ),
            "Inhibition verbale interférence temps": (
                inhibition_scores.get("Inhibition verbale incongruent temps", 0) 
                - inhibition_scores.get("Inhibition verbale congruent temps", 0)
            ),
            "Inhibition non verbale interférence temps": (
                inhibition_scores.get("Inhibition non verbale incongruent temps", 0) 
                - inhibition_scores.get("Inhibition non verbale congruent temps", 0)
            )
        }

        # Afficher les résultats des interférences au fur et à mesure
        st.subheader("Scores d'interférence calculés")
        for key, value in interferences.items():
            st.write(f"**{key}** : {value:.2f}")

        # Ajouter les scores d'interférence
        for key, value in interferences.items():
            user_scores.append({"Tâche": key, "Score Enfant": value})

        # Convertir les scores saisis en DataFrame
        scores_df = pd.DataFrame(user_scores, columns=["Tâche", "Score Enfant"])

        # Fusionner avec les données originales pour les calculs
        merged_data = pd.merge(age_data, scores_df, on="Tâche", how="left")
        merged_data["Z-Score"] = (merged_data["Score Enfant"] - merged_data["Moyenne"]) / merged_data["Ecart-type"]

        # Filtrer les tâches avec des scores saisis
        filled_data = merged_data[~merged_data["Score Enfant"].isna()]

        # Supprimer les doublons
        filled_data = filled_data.drop_duplicates(subset="Tâche")

        # Bouton pour confirmer les scores
        if st.button("Confirmer les scores et afficher les résultats"):
            st.session_state["scores_entered"] = True
            st.session_state["age_data"] = filled_data
            st.session_state["missing_norms"] = missing_norms


# Étape 3 : Résultats
# Fonction pour générer un graphique radar
if st.session_state["scores_entered"]:
    st.header("Étape 3 : Résultats")

    # Récupérer les données mises à jour
    age_data = st.session_state["age_data"]
    missing_norms = st.session_state["missing_norms"]

    # Afficher le tableau des résultats
    st.write("")
    st.dataframe(age_data.reset_index(drop=True))

    # Afficher les tâches sans normes
    if missing_norms:
        st.warning(f"Les normes suivantes ne sont pas disponibles : {', '.join(missing_norms)}")

    # Ajout d'une colonne pour indiquer la catégorie "Langage"
        categories_mapping = {
            "Langage": [
                "Discrimination Phonologique",
                "Décision Lexicale Auditive",
                "Mots Outils",
                "Stock Lexical",
                "Compréhension Syntaxique",
                "Mots Outils - BOEHM",
            ],
            "FE V": [
                "Mémoire de travail verbale endroit empan",
                "Mémoire de travail verbale endroit brut", 
                "Mémoire de travail verbale envers empan",
                "Mémoire de travail verbale envers brut", 
                "Mise à jour verbale empan", 
                "Mise à jour verbale score", 
                "Inhibition verbale congruent score",
                "Inhibition verbale incongruent score",
                "Inhibition verbale congruent temps",
                "Inhibition verbale incongruent temps",
                "Inhibition verbale interférence score", 
                "Inhibition verbale interférence temps",
            ],
            
            "FE NV": [
                "Mémoire de travail non verbale endroit empan",
                "Mémoire de travail non verbale endroit brut", 
                "Mémoire de travail non verbale envers empan",
                "Mémoire de travail non verbale envers brut", 
                "Mise à jour non verbale empan", 
                "Mise à jour non verbale score", 
                "Inhibition non verbale congruent score",
                "Inhibition non verbale incongruent score",
                "Inhibition non verbale congruent temps",
                "Inhibition non verbale incongruent temps",
                "Inhibition non verbale interférence score", 
                "Inhibition non verbale interférence temps",
            ]
        }
        # Ajouter la colonne "Catégorie" pour chaque tâche
        def assign_category(task):
            for category, tasks in categories_mapping.items():
                if task in tasks:
                    return category
            return "Autre"

        age_data["Catégorie"] = age_data["Tâche"].apply(assign_category)


        # Permettre à l'utilisateur de choisir l'ordre des tâches
        st.subheader("Réorganisez l'ordre des tâches")
        available_tasks = age_data["Tâche"].tolist()
        ordered_tasks = st.multiselect(
            "Sélectionez les tâches selon l'ordre souhaité :", 
            options=available_tasks, 
            default=[]
        )

        # Vérifiez si l'utilisateur a sélectionné toutes les tâches
        if len(ordered_tasks) != len(available_tasks):
            st.warning("Vous n'avez pas sélectionné toutes les tâches. Les tâches non sélectionnées seront exclues.")

        # Réorganiser les données en fonction de l'ordre choisi par l'utilisateur
        filtered_data = age_data[age_data["Tâche"].isin(ordered_tasks)]
        filtered_data = filtered_data.set_index("Tâche").loc[ordered_tasks].reset_index()

        # Générer le graphique uniquement si des tâches sont sélectionnées
        if not filtered_data.empty:
            st.write("")

            # Générer le graphique
            fig, ax = plt.subplots(figsize=(8, max(4, len(filtered_data) * 0.5)))  # Taille dynamique

            # Recalculer les positions Y avec un facteur d'espacement
            spacing_factor = 1.5
            y_pos = np.arange(len(filtered_data))[::-1] * spacing_factor  # Inversion de l'ordre

            # Zone acceptable en Z-score
            ax.fill_betweenx(
                y_pos,
                -2.5,
                2.5,
                color="#d0f0c0",
                alpha=0.5,
                label=""
            )

            # Ligne de référence pour Z=0
            ax.axvline(0, color="black", linestyle="--")

            # Tracer les Z-scores
            ax.plot(
                filtered_data["Z-Score"],
                y_pos,
                marker="o",
                linestyle="-",
                color="black",
                label=""
            )

            # Configurer les étiquettes des tâches
            ax.set_yticks(y_pos)
            ax.set_yticklabels(filtered_data["Tâche"], fontsize=10, ha='right', va='center')

            # Ajouter les Z-scores obtenus par l'enfant à droite avec un encadré
            for i, z_score in enumerate(filtered_data["Z-Score"]):
                # Déterminer la couleur de la boîte et du texte
                if -2.5 <= z_score <= 2.5:
                    color = "green"
                    box_color = "#d8f5d3"
                else:
                    color = "gray"
                    box_color = "#e0e0e0"

                # Ajouter le texte avec décalage et encadré
                ax.text(
                    11,  # Décaler vers la droite pour éloigner du graphique
                    y_pos[i],  # Position alignée verticalement avec les tâches
                    f"{z_score:.2f}",
                    color=color,
                    fontsize=10,
                    ha="left",
                    va="center",
                    bbox=dict(
                        facecolor="white",  # Fond blanc
                        edgecolor=color,  # Bordure colorée
                        boxstyle="round,pad=0.5",  # Encadré arrondi avec padding
                        linewidth=1,
                    )
                )

            # Ajouter la coloration des étiquettes des tâches en fonction de leur catégorie
            for tick, (task, category) in zip(ax.get_yticklabels(), zip(filtered_data["Tâche"], filtered_data["Catégorie"])):
                if category == "Langage":
                    tick.set_bbox(dict(
                        facecolor="#fff9f0",  # Couleur de fond pour Langage
                        edgecolor="#fdb848",  # Bordure orange
                        boxstyle="round,pad=0.5"
                    ))
                elif category == "FE V":
                    tick.set_bbox(dict(
                        facecolor="#ebf7ff",  # Couleur de fond pour FE V
                        edgecolor="#5cace1",  # Bordure bleue
                        boxstyle="round,pad=0.5"
                    ))
                elif category == "FE NV":
                    tick.set_bbox(dict(
                        facecolor="#faefff",  # Couleur de fond pour FE NV
                        edgecolor="#af7ac5",  # Bordure violette
                        boxstyle="round,pad=0.5"
                    ))
                else:
                    tick.set_bbox(dict(
                        facecolor="white",  # Couleur de fond pour "Autre"
                        edgecolor="gray",  # Bordure grise
                        boxstyle="round,pad=0.5"
                    ))

                # Ajuster l'apparence du texte
                tick.set_x(-0.05)  # Légère marge
                tick.set_fontweight("bold")  # Texte en gras
                tick.set_fontsize(12)        # Taille de la police
                tick.set_color("black")      # Couleur du texte

            # Ajuster les limites de l'axe Y
            ax.set_ylim(-0.5, max(y_pos) + 0.5)

            # Configurer le graphique
            ax.set_xlabel("Z-Scores")
            ax.set_xlim(-10, 10)  # Ajuster pour inclure les Z-scores
            ax.set_title(
            "Résultats obtenus à la batterie Comprendre",
            fontdict={'fontsize': 14, 'fontweight': 'bold'}
            )
            
            ax.grid(
                color='lightgray',  # Couleur des lignes du grillage
                linestyle='--',     # Style de ligne en pointillés
                linewidth=0.5,      # Épaisseur des lignes
                alpha=0.7           # Transparence du grillage
            )

            # Afficher le graphique
            st.pyplot(fig)
        else: 
            st.error("Aucune tâche sélectionnée pour le graphique.")

        # Bouton pour enregistrer les résultats
        if st.button("Enregistrer les résultats dans un fichier ZIP"):

            # 1. Créer un fichier en mémoire pour le graphique PNG
            graph_buffer = io.BytesIO()
            fig.savefig(graph_buffer, format='png', bbox_inches="tight", dpi = 300)
            graph_buffer.seek(0)  # Revenir au début du fichier en mémoire

            # 2. Créer un fichier en mémoire pour le tableau Excel
            excel_buffer = io.BytesIO()
            with ExcelWriter(excel_buffer, engine="openpyxl") as writer:
                # Sauvegarder les résultats dans une feuille Excel avec un nom personnalisé
                age_data.to_excel(writer, index=False, sheet_name=f"Résultats_{child_id}")
            excel_buffer.seek(0) # Revenir au début du fichier en mémoire # Revenir au début du fichier en mémoire

            # 3. Créer un fichier ZIP en mémoire
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zf:
                # Ajouter le graphique au fichier ZIP
                zf.writestr(f"graphique_{child_id}.png", graph_buffer.getvalue())
                # Ajouter le tableau des résultats au fichier ZIP
                zf.writestr(f"tableau_{child_id}.xlsx", excel_buffer.getvalue())

            zip_buffer.seek(0)  # Revenir au début du fichier ZIP en mémoire

            # 4. Proposer le téléchargement du fichier ZIP
            st.download_button(
                label="Télécharger le fichier ZIP",
                data=zip_buffer,
                file_name=f"resultats_comprendre_{child_id}.zip",
                mime="application/zip"
            )

