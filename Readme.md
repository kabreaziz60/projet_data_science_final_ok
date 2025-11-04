# Guide pour lancer le projet Chatbot en local

## 1️⃣ Pré-requis
- Python 3.9 ou plus récent  
- pip  
- Git (optionnel si clone depuis dépôt)  
- IDE ou éditeur de code (VS Code, PyCharm...)

## 2️⃣ Récupération du projet
### Option A : Cloner depuis Git
```bash
git clone https://github.com/kabreaziz60/projet_data_science_final.git
cd projet_data_science_final

### Option B : Télécharger ZIP

Décompresse le ZIP

Ouvre le dossier avec ton IDE


3️⃣ Créer un environnement virtuel
python -m venv venv


Activer :

Windows : venv\Scripts\activate

Mac/Linux : source venv/bin/activate

4️⃣ Installer les dépendances
pip install -r requirements.txt


Ou manuellement :

pip install pandas scikit-learn joblib streamlit gradio flask

5 Django
python manage.py runserver


Accéder via http://127.0.0.1:8000

6️⃣ Tester le chatbot

Poser des questions pour vérifier les réponses

Vérifier les logs dans le terminal

7️⃣ Conseils

Toujours activer l'environnement virtuel avant de travailler

Mettre à jour les librairies si besoin :

pip install --upgrade pandas scikit-learn streamlit


Vérifier les chemins des fichiers pour les données et modèles