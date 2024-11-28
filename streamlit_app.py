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

       
        filtered_interferences = {
            key: value for key, value in interferences.items() if value != 0
        }

        # Ajouter uniquement les scores d'interférences non nuls
        user_scores.extend(
            [{"Tâche": key, "Score Enfant": value} for key, value in filtered_interferences.items()]
        )

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
    # Définir les catégories et le mapping des noms abrégés
    categories_mapping = {
        "Langage": [
            "Discrimination Phonologique", "Décision Lexicale Auditive",
            "Mots Outils", "Stock Lexical", "Compréhension Syntaxique", "Mots Outils - BOEHM"
        ],
        "Mémoire de Travail": [
            "Mémoire de travail verbale endroit empan", "Mémoire de travail verbale endroit brut",
            "Mémoire de travail verbale envers empan", "Mémoire de travail verbale envers brut",
            "Mémoire de travail non verbale endroit empan", "Mémoire de travail non verbale endroit brut",
            "Mémoire de travail non verbale envers empan", "Mémoire de travail non verbale envers brut"
        ],
        "Mise à jour": [
            "Mise à jour verbale empan", "Mise à jour verbale score",
            "Mise à jour non verbale empan", "Mise à jour non verbale score"
        ],
        "Inhibition": [
            "Inhibition verbale congruent score", "Inhibition verbale incongruent score",
            "Inhibition verbale congruent temps", "Inhibition verbale incongruent temps",
            "Inhibition verbale interférence score", "Inhibition verbale interférence temps",
            "Inhibition non verbale congruent score", "Inhibition non verbale incongruent score",
            "Inhibition non verbale congruent temps", "Inhibition non verbale incongruent temps",
            "Inhibition non verbale interférence score", "Inhibition non verbale interférence temps"
        ]
    }

    task_name_mapping = {
        "Discrimination Phonologique": "DP",
        "Décision Lexicale Auditive": "DL",
        "Mots Outils": "MO",
        "Stock Lexical": "SL",
        "Compréhension Syntaxique": "CS",
        "Mots Outils - BOEHM": "BOEHM",
        "Mémoire de travail verbale endroit empan": "MDT V\nendroit\nempan",
        "Mémoire de travail verbale endroit brut": "MDT V\nendroit\nbrut",
        "Mémoire de travail verbale envers empan": "MDT V\nenvers\nempan",
        "Mémoire de travail verbale envers brut": "MDT V\nenvers\nbrut",
        "Mémoire de travail non verbale endroit empan": "MDT NV\nendroit\nempan",
        "Mémoire de travail non verbale endroit brut": "MDT NV\nendroit\nbrut",
        "Mémoire de travail non verbale envers empan": "MDT NV\nenvers\nempan",
        "Mémoire de travail non verbale envers brut": "MDT NV\nenvers\nbrut",
        "Mise à jour verbale empan": "MAJ V\nempan",
        "Mise à jour verbale score": "MAJ V\nbrut",
        "Mise à jour non verbale empan": "MAJ NV\nempan",
        "Mise à jour non verbale score": "MAJ NV\nbrut",
        "Inhibition verbale congruent score": "INHIB VC score",
        "Inhibition verbale incongruent score": "INHIB VI score",
        "Inhibition verbale congruent temps": "INHIB VC temps",
        "Inhibition verbale incongruent temps": "INHIB VI temps",
        "Inhibition verbale interférence score": "INHIB V score",
        "Inhibition verbale interférence temps": "INHIB V temps",
        "Inhibition non verbale congruent score": "INHIB NVC score",
        "Inhibition non verbale incongruent score": "INHIB NVI score",
        "Inhibition non verbale congruent temps": "INHIB NVC temps",
        "Inhibition non verbale incongruent temps": "INHIB NVI temps",
        "Inhibition non verbale interférence score": "INHIB NV score",
        "Inhibition non verbale interférence temps": "INHIB NV temps"
    }

    # Ajouter la colonne "Catégorie" pour chaque tâche
    def plot_grouped_scores(data, selected_tasks):
        # Définir les couleurs pour chaque catégorie
        category_colors = {
            "Langage": "#3798da",
            "Mémoire de Travail": "#eca113",
            "Mise à jour": "#4cb254",
            "Inhibition": "#8353da",
            "Autre": "gray"
        }

        # Filtrer les données pour inclure uniquement les tâches sélectionnées
        data = data[data["Tâche"].isin(selected_tasks)]

        # Liste des tâches (abrégées) et leurs Z-scores
        tasks = data["Tâche"].map(task_name_mapping).tolist()
        z_scores = data["Z-Score"].tolist()
        positions = np.arange(len(tasks))
        categories = data["Catégorie"].unique()

        # Créer la figure et l'axe
        fig_width = max(12, len(tasks) * 0.5)
        fig, ax = plt.subplots(figsize=(max(12, len(tasks) * 1.5), 10))

        # Tracer les points uniquement (sans relier les lignes)
        ax.scatter(positions, z_scores, color="black", label="Z-Score", zorder=3)

        # Ajouter une zone grisée pour les scores "acceptables"
        ax.fill_between(positions, -2.5, 2.5, color="lightgray", alpha=0.5, zorder=1)

        # Ligne de référence Z=0
        ax.axhline(0, color="black", linestyle="--", linewidth=0.8, zorder=2)

        # Fixer les limites de l'axe Y
        ax.set_ylim(-10, 10)
        y_max = ax.get_ylim()[1] 

        # Définir la dernière position pour les catégories
        last_pos = 0
        # Parcourir les catégories
        for category in categories:
            # Filtrer les données pour cette catégorie
            category_data = data[data["Catégorie"] == category]
            category_positions = positions[last_pos:last_pos + len(category_data)]
            category_z_scores = category_data["Z-Score"].tolist()

            # Relier les points pour cette catégorie
            ax.plot(
                category_positions, category_z_scores, 
                marker="o", linestyle="-", color="black", label=category
            )

            # Tracer une ligne verticale pour séparer les catégories
            if last_pos != 0:
                ax.axvline(last_pos - 0.5, color="black", linestyle="--", alpha=0.5, zorder=1)

            # Ajouter le titre de la catégorie avec sa couleur
            category_positions = positions[last_pos:last_pos + len(category_data)]  # Positions des tâches de la catégorie
            mid_pos = category_positions.mean()  # Position horizontale exacte basée sur les ticks
            ax.text(
                mid_pos, y_max + 0.5, category,  # Décalage vertical dynamique
                fontsize=18, fontweight="bold", ha="center", color=category_colors[category]
            )
            
            # Colorer les labels des tâches sur l'axe X
            for idx, task_pos in enumerate(range(last_pos, last_pos + len(category_data))):
                if task_pos < len(ax.get_xticklabels()):  # Vérifiez que l'indice existe
                    tick_label = ax.get_xticklabels()[task_pos]
                    tick_label.set_color(category_colors[category])

            last_pos += len(category_data)


        # Configurer les ticks et les labels
        ax.set_xticks(positions)
        ax.set_xticklabels(tasks, fontsize=16, fontweight='bold')
        ax.set_ylabel("Z-Score")
        x_center = positions.mean()
        ax.text(
            x_center, y_max + 2, "Résultats Batterie Comprendre",  
            fontsize=20, fontweight="bold", ha="center"
        )

        # Ajuster la mise en page
        plt.subplots_adjust(top=0.85, bottom=0.25)
        plt.tight_layout()

        # Afficher le graphique
        st.pyplot(fig)


# Ajouter la colonne "Catégorie" pour chaque tâche
def assign_category(task):
    for category, tasks in categories_mapping.items():
        if task in tasks:
            print(f"Task '{task}' assigned to category '{category}'")  # Débogage
            return category
    return "Autre"


# Étape 3 : Résultats
if st.session_state["scores_entered"]:
    st.header("Étape 3 : Résultats")

    # Récupérer les données mises à jour
    age_data = st.session_state["age_data"]
    missing_norms = st.session_state["missing_norms"]

    # Ajouter la colonne "Catégorie" si elle n'existe pas
    if "Catégorie" not in age_data.columns:
        categories_mapping = {
            "Langage": [
                "Discrimination Phonologique", "Décision Lexicale Auditive",
                "Mots Outils", "Stock Lexical", "Compréhension Syntaxique", "Mots Outils - BOEHM"
            ],
            "Mémoire de Travail": [
                "Mémoire de travail verbale endroit empan", "Mémoire de travail verbale endroit brut",
                "Mémoire de travail verbale envers empan", "Mémoire de travail verbale envers brut",
                "Mémoire de travail non verbale endroit empan", "Mémoire de travail non verbale endroit brut",
                "Mémoire de travail non verbale envers empan", "Mémoire de travail non verbale envers brut"
            ],
            "Mise à jour": [
                "Mise à jour verbale empan", "Mise à jour verbale score",
                "Mise à jour non verbale empan", "Mise à jour non verbale score"
            ],
            "Inhibition": [
                "Inhibition verbale congruent score", "Inhibition verbale incongruent score",
                "Inhibition verbale congruent temps", "Inhibition verbale incongruent temps",
                "Inhibition verbale interférence score", "Inhibition verbale interférence temps",
                "Inhibition non verbale congruent score", "Inhibition non verbale incongruent score",
                "Inhibition non verbale congruent temps", "Inhibition non verbale incongruent temps",
                "Inhibition non verbale interférence score", "Inhibition non verbale interférence temps"
            ]
        }
        age_data["Catégorie"] = age_data["Tâche"].apply(assign_category)

    # Afficher le tableau des résultats
    st.write("")
    st.dataframe(age_data.reset_index(drop=True))

    # Afficher les tâches sans normes
    if missing_norms:
        st.warning(f"Les normes suivantes ne sont pas disponibles : {', '.join(missing_norms)}")

    # Sélection des tâches calculées
    st.subheader("Sélectionnez les tâches à afficher dans le graphique")
    calculated_tasks = age_data[~age_data["Z-Score"].isna()]["Tâche"].tolist()
    selected_tasks = st.multiselect(
        "Tâches calculées disponibles :", 
        options=calculated_tasks, 
        default=calculated_tasks
    )

    # Vérifiez que des tâches sont sélectionnées
    if selected_tasks:
        # Appeler la fonction pour tracer le graphique
        plot_grouped_scores(age_data, selected_tasks)
    else:
        st.warning("Veuillez sélectionner au moins une tâche à afficher.")

