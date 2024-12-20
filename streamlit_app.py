import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import zipfile
import io
import openpyxl
from pandas import ExcelWriter
from streamlit_sortables import sort_items
from scipy.stats import norm
#pmm
# Charger le fichier Excel
file_path = 'NORMES_NOV_24.xlsx'
excel_data = pd.ExcelFile(file_path)

# Liste des groupes d'âge (onglets du fichier)
age_groups = excel_data.sheet_names


if "age_selected" not in st.session_state:
    st.session_state["age_selected"] = False

if "scores_entered" not in st.session_state:
    st.session_state["scores_entered"] = False

if "age_data" not in st.session_state:
    st.session_state["age_data"] = pd.DataFrame()

if "missing_norms" not in st.session_state:
    st.session_state["missing_norms"] = []


# Titre de l'application
st.markdown(
    """
    <div style="text-align: center; font-size: 40px; font-weight: bold;">
        Batterie COMPRENDRE
    </div>
    """,
    unsafe_allow_html=True
)

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
        merged_data["Z-Score"] = pd.to_numeric(merged_data["Z-Score"], errors="coerce")
        merged_data = merged_data.dropna(subset=["Z-Score"])



        # Inverser les Z-scores pour les variables de temps d'inhibition
        time_variables = [
            "Inhibition verbale congruent temps",
            "Inhibition verbale incongruent temps",
            "Inhibition non verbale congruent temps",
            "Inhibition non verbale incongruent temps", 
            "Inhibition verbale interférence temps", 
            "Inhibition non verbale interférence temps"
        ]

        # Appliquer l'inversion des Z-scores uniquement aux variables concernées
        #merged_data.loc[merged_data["Tâche"].isin(time_variables), "Z-Score"] *= -1
        
        # Ajouter une colonne pour les percentiles (%) à partir des Z-scores
        merged_data["Percentile (%)"] = norm.cdf(merged_data["Z-Score"]) * 100

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
        "Inhibition verbale congruent score": "INHIB VC \nscore",
        "Inhibition verbale incongruent score": "INHIB VI \nscore",
        "Inhibition verbale congruent temps": "INHIB VC \ntemps",
        "Inhibition verbale incongruent temps": "INHIB VI \ntemps",
        "Inhibition verbale interférence score": "INHIB V \nscore",
        "Inhibition verbale interférence temps": "INHIB V \ntemps",
        "Inhibition non verbale congruent score": "INHIB NVC \nscore",
        "Inhibition non verbale incongruent score": "INHIB NVI \nscore",
        "Inhibition non verbale congruent temps": "INHIB NVC \ntemps",
        "Inhibition non verbale incongruent temps": "INHIB NVI \ntemps",
        "Inhibition non verbale interférence score": "INHIB NV \nscore",
        "Inhibition non verbale interférence temps": "INHIB NV \ntemps"
    }

    # Ajouter la colonne "Catégorie" pour chaque tâche
    def plot_grouped_scores(data, selected_tasks):
        # Définir les couleurs pour chaque catégorie
        category_colors = {
            "Langage": "#3798da",
            "Mémoire de Travail": "#eca113",
            "Mise à jour": "#e365d6",
            "Inhibition": "#8353da",
            "Autre": "gray"
        }

        # Filtrer les données pour inclure uniquement les tâches sélectionnées
        data = data[data["Tâche"].isin(selected_tasks)]

        # Liste des tâches (abrégées) et leurs Z-scores
        tasks = data["Tâche"].map(task_name_mapping).tolist()
        percentiles = data["Percentile (%)"].tolist()

        positions = np.arange(len(tasks))  # Une position unique par tâche

        # Ajouter une colonne pour les positions dans le DataFrame
        data["Position"] = positions

        # Créer la figure
        fig_width = 14
        fig_height = max(10, len(tasks) * 1.5)
        fig, ax = plt.subplots(figsize=(fig_width, fig_height))

        # Tracer les points pour chaque tâche
        point_colors = data["Catégorie"].map(category_colors)
        ax.scatter(percentiles, positions, color=point_colors, s=100, zorder=3)

        # Ajouter des zones colorées pour les catégories
        ax.fill_betweenx(positions, 0, 3, color="#d44646", alpha=0.2, zorder=1)
        ax.fill_betweenx(positions, 3, 15, color="#f5a72f", alpha=0.2, zorder=1)
        ax.fill_betweenx(positions, 15, 85, color="#60cd72", alpha=0.2, zorder=1)
        ax.fill_betweenx(positions, 85, 97, color="#8ddf9b", alpha=0.2, zorder=1)
        ax.fill_betweenx(positions, 97, 100, color="#aedeb6", alpha=0.2, zorder=1)

        # Ligne de référence Z=0
        ax.axvline(50, color="black", linestyle="--", linewidth=0.8, zorder=2)
        
        ax.set_xlim(0, 100)  # Axe X : percentiles de 0 à 100
        ax.set_ylim(-1, len(tasks))

        # Configurer les ticks et les labels
        ax.set_xticks([0, 3, 15, 50, 85, 97, 100])
        ax.set_xticklabels(["0", "3", "15", "50", "85", "97", "100"], fontsize=12, fontweight="bold", rotation = -35)
        ax.set_yticks(positions)
        ax.set_yticklabels(tasks, fontsize=16, fontweight="bold")
        ax.set_xlabel("Percentiles (%)", fontsize=14)
        ax.set_ylabel("")
        ax.set_title("Résultats Batterie Comprendre", fontsize=24, fontweight="bold")

        last_pos = None  # Commencer avant la première position
        for idx, category in enumerate(category_colors.keys()):
            # Filtrer les données pour cette catégorie
            category_data = data[data["Catégorie"] == category]
            
            # Obtenir les positions et les percentiles pour les tâches dans la catégorie
            category_positions = category_data["Position"].tolist() if not category_data.empty else []
            category_percentiles = category_data["Percentile (%)"].tolist() if not category_data.empty else []

            # Relier les points avec une ligne si la catégorie n'est pas vide
            if category_positions and category_percentiles:
                ax.plot(
                    category_percentiles,  # Les percentiles sur l'axe X
                    category_positions,   # Les positions sur l'axe Y
                    marker="o", linestyle="-", color=category_colors[category],
                    label=category, zorder=4, linewidth=2
                )

        # Ajouter des titres par catégorie sur l'axe Y
        for category, color in category_colors.items():
            # Filtrer les tâches dans la catégorie
            category_data = data[data["Catégorie"] == category]
            
            # Si la catégorie n'est pas vide, ajouter un titre
            if not category_data.empty:
                # Calculer la position moyenne des tâches de la catégorie
                category_positions = category_data["Position"].tolist()
                mid_position = np.mean(category_positions)
                
                # Ajouter le texte pour le titre de la catégorie
                ax.text(
                    x=-15,  # Décalage vers la gauche (en dehors des ticks Y)
                    y=mid_position,
                    s=category.upper(),
                    color=color,
                    fontsize=20,
                    fontweight="bold",
                    ha="right",  # Aligner à droite
                    va="center", 
                    rotation=90
                )

        # Colorer les labels des ticks en fonction des catégories
        for idx, task_label in enumerate(ax.get_yticklabels()):
            if idx < len(data):
                task_category = data.iloc[idx]["Catégorie"]
                task_label.set_color(category_colors.get(task_category, "gray"))

        # Ajuster la mise en page
        plt.subplots_adjust(left=0.3, right=0.95, top=0.85, bottom=0.15)
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

    # Sélection des tâches calculées
    # Sélection des tâches calculées
    st.subheader("Sélectionnez les tâches à afficher dans le graphique")
    calculated_tasks = age_data[~age_data["Z-Score"].isna()]["Tâche"].tolist()
    tasks_by_category = {}
    for category, tasks in categories_mapping.items():
        tasks_in_category = [task for task in tasks if task in calculated_tasks]
        if tasks_in_category:
            tasks_by_category[category] = tasks_in_category

    # Ajouter des boutons pour sélectionner ou désélectionner toutes les tâches
    col1, col2, col3, col4, col5 = st.columns([1, 2, 1, 2, 1])
    with col2:
        if st.button("Tout sélectionner"):
            selected_tasks = calculated_tasks
        else:
            selected_tasks = []

    with col4:
        if st.button("Tout désélectionner"):
            selected_tasks = []

    # Interface utilisateur pour sélectionner les tâches par catégories
    selected_tasks = st.multiselect(
        "Tâches calculées disponibles :", 
        options=calculated_tasks, 
        default=selected_tasks,
        help="Vous pouvez rechercher ou sélectionner des tâches dans la liste."
    )

# Fonction pour sauvegarder le graphique
    def save_graph_and_data(data, selected_tasks):
        # Création des fichiers en mémoire
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as zf:
            # Sauvegarder le graphique
            fig_buffer = io.BytesIO()
            plot_grouped_scores(data, selected_tasks)
            plt.savefig(fig_buffer, format='png', dpi=300, bbox_inches="tight")
            fig_buffer.seek(0)
            zf.writestr(f"{st.session_state['child_id']}_Graphique_Comprendre.png", fig_buffer.read())

            # Sauvegarder le tableau des résultats en Excel
            excel_buffer = io.BytesIO()
            data.to_excel(excel_buffer, index=False, engine="openpyxl")
            excel_buffer.seek(0)
            zf.writestr(f"{st.session_state['child_id']}_Tableau_Comprendre.xlsx", excel_buffer.read())

        buffer.seek(0)
        return buffer

    # Bouton pour télécharger le fichier ZIP
    if st.session_state["scores_entered"] and selected_tasks:
        st.subheader("Téléchargez les résultats")
        zip_file = save_graph_and_data(age_data, selected_tasks)
        st.download_button(
            label="📥 Télécharger le tableau des résultats et le graphique (ZIP)",
            data=zip_file,
            file_name=f"{st.session_state['child_id']}_Resultats_Comprendre.zip",
            mime="application/zip"
        )
