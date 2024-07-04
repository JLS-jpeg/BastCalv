from pony.orm import db_session, commit
from flask import Flask
from flask_bcrypt import Bcrypt
from app import db, Formateurs, Apprentis, app  # Importez les classes et l'application principale

# Utilisez Flask-Bcrypt avec l'application Flask existante
bcrypt = Bcrypt(app)

@db_session
def update_passwords():
    # Mettre à jour les mots de passe des formateurs
    formateurs = Formateurs.select()
    for formateur in formateurs:
        if formateur.MDP and not formateur.MDP.startswith("$2b$"):
            hashed_password = bcrypt.generate_password_hash(formateur.MDP).decode('utf-8')
            formateur.MDP = hashed_password
    
    # Mettre à jour les mots de passe des apprentis
    apprentis = Apprentis.select()
    for apprenti in apprentis:
        if apprenti.MDP and not apprenti.MDP.startswith("$2b$"):
            hashed_password = bcrypt.generate_password_hash(apprenti.MDP).decode('utf-8')
            apprenti.MDP = hashed_password
    
    commit()

def main():
    update_passwords()
    print("Mots de passe mis à jour avec succès!")

if __name__ == '__main__':
    main()
