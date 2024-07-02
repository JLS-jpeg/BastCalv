from flask import Flask, render_template, redirect, url_for, session, request, jsonify
from datetime import timedelta, datetime, time, date
from pony.orm import Database, Required, db_session, select, PrimaryKey, Set, commit, Optional

app = Flask(__name__)
app.secret_key = "super secret key"

# Configuration de la base de données
app.config['PONY'] = {
    'provider': 'mysql',
    'host': 'host.docker.internal',
    'port': 8889,
    'user': 'bastien',
    'passwd': 'bastien',
    'db': 'doodle'
}

# Initialisation de la base de données avec Pony ORM
db = Database()
db.bind(**app.config['PONY'])

class Formateurs(db.Entity):
    id_formateur = PrimaryKey(int, auto=True)
    Nom = Required(str)
    Prenom = Optional(str)
    MDP = Required(str)
    Mail = Required(str, unique=True)
    rendezvous = Set('RDVs')
    id_formation = Set('Formations')

class Formations(db.Entity):
    id_formation = PrimaryKey(int, auto=True)
    Nom = Optional(str)
    id_centre = Optional('Centres')
    id_formateur = Optional('Formateurs')
    rendezvous = Set('RDVs')

class Apprentis(db.Entity):
    id_apprenti = PrimaryKey(int, auto=True)
    Nom = Optional(str)
    Prenom = Optional(str)
    MDP = Required(str)
    Mail = Required(str, unique=True)
    rendezvous = Set('RDVs')

class RDVs(db.Entity):
    id_rdv = PrimaryKey(int, auto=True)
    Date = Required(date)
    Heure = Required(time)
    description = Required(str)
    Duree = Required(time)
    id_formateur = Required(Formateurs)
    id_formation = Required(Formations)
    id_apprenti = Required(Apprentis)
    Mail = Optional(str)
    Telephone = Optional(str)
    Url_invitation = Optional(str)

class Centres(db.Entity):
    id_centre = PrimaryKey(int, auto=True)
    Ville = Required(str)
    Adresse = Required(str)
    formations = Set('Formations')

db.generate_mapping(create_tables=False)

# Routes et fonctions
@app.route('/api/rendezvousapprenti')
@db_session
def api_rendezvousapprenti():
    rendezvous = RDVs.select() 
    events = []

    for rv in rendezvous:
        debut = datetime.combine(rv.Date, rv.Heure)
        fin = (datetime.combine(datetime.min, rv.Duree) - datetime.min) + debut
        events.append({
            'id_rdv': rv.id_rdv,
            'title': f"{rv.description} à {debut.strftime('%H:%M')}",
            'start': debut.isoformat(),
            'end': fin.isoformat(),
            'description': rv.description,
            'id_formateur': rv.id_formateur.id_formateur,
            'id_formation': rv.id_formation.id_formation,
            'id_apprenti': rv.id_apprenti.id_apprenti,
            'mail': rv.Mail,
            'telephone': rv.Telephone,
            'url_invitation': rv.Url_invitation
        })

    return jsonify(events)

@app.route('/api/rendezvous')
@db_session
def api_rendezvous():
    rendezvous = RDVs.select()
    
    events = []
    for rv in rendezvous:
        debut = datetime.combine(rv.Date, rv.Heure)
        fin = (datetime.combine(datetime.min, rv.Duree) - datetime.min) + debut
        events.append({
            'id_rdv': rv.id_rdv,
            'title': f"{rv.description} à {debut.strftime('%H:%M')}",
            'start': debut.isoformat(),
            'end': fin.isoformat(),
            'description': rv.description,
            'id_formateur': rv.id_formateur.id_formateur,
            'id_formation': rv.id_formation.id_formation,
            'id_apprenti': rv.id_apprenti.id_apprenti,
            'mail': rv.Mail,
            'telephone': rv.Telephone,
            'url_invitation': rv.Url_invitation
        })
    
    return jsonify(events)

@app.route('/get_formations_formateurs')
@db_session
def get_formations_formateurs():
    formations = Formations.select()
    formateurs = Formateurs.select()
    apprentis = Apprentis.select()
    
    return jsonify({
        'formations': [{'id': formation.id_formation, 'nom': formation.Nom, 'ville_centre': formation.id_centre.Ville if formation.id_centre else None} for formation in formations],
        'formateurs': [{'id': formateur.id_formateur, 'nom': formateur.Nom} for formateur in formateurs],
        'apprentis': [{'id': apprenti.id_apprenti, 'nom': apprenti.Nom, 'prenom': apprenti.Prenom} for apprenti in apprentis]
    })

@app.route('/ajouter_rendezvous', methods=['POST'])
@db_session
def ajouter_rendezvous():
    date_str = request.form['date']
    heure_str = request.form['heure']
    description = request.form['description']
    duree_str = request.form['duree']
    formateur_id = request.form['formateur']
    formation_id = request.form['formation']
    apprenti_id = request.form['apprenti']
    mail = request.form['mail']
    telephone = request.form['telephone']
    url_invitation = request.form['url_invitation']

    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'status': 'error', 'message': 'Invalid date format'}), 400

    try:
        # Try different time formats
        heure_obj = datetime.strptime(heure_str, '%H:%M:%S').time()
    except ValueError:
        try:
            heure_obj = datetime.strptime(heure_str, '%H:%M').time()
        except ValueError:
            return jsonify({'status': 'error', 'message': 'Invalid time format'}), 400

    try:
        # Convert duration to a time object
        duree_parts = duree_str.split(':')
        duree_obj = time(hour=int(duree_parts[0]), minute=int(duree_parts[1]))
    except (ValueError, IndexError):
        return jsonify({'status': 'error', 'message': 'Invalid duration format'}), 400

    formateur = Formateurs.get(id_formateur=formateur_id)
    formation = Formations.get(id_formation=formation_id)
    apprenti = Apprentis.get(id_apprenti=apprenti_id)

    if not formateur or not formation or not apprenti:
        return jsonify({'status': 'error', 'message': 'Invalid formateur, formation, or apprenti ID'}), 400

    RDVs(Date=date_obj, Heure=heure_obj, description=description, Duree=duree_obj, 
         id_formateur=formateur, id_formation=formation, id_apprenti=apprenti,
         Mail=mail, Telephone=telephone, Url_invitation=url_invitation)
    
    commit()
    return jsonify({'status': 'success'})

@app.route('/detailsRDV')
@db_session
def detailsRDV():
    id_rdv = request.args.get('id_rdv')
    rendezvous = RDVs.get(id_rdv=id_rdv)
    if rendezvous:
        return jsonify({
            'id_rdv': rendezvous.id_rdv,
            'date': rendezvous.date.isoformat(),
            'heure': rendezvous.heure.isoformat(),
            'description': rendezvous.description,
            'duree': str(rendezvous.duree),
            'id_formateur': rendezvous.formateur.id_formateur,
            'id_formation': rendezvous.formation.id_formation,
            'id_apprenti': rendezvous.apprenti.id_apprenti,
            'mail': rendezvous.mail,
            'telephone': rendezvous.telephone,
            'url_invitation': rendezvous.url_invitation
        })
    return jsonify({'status': 'not found'}), 404

# Autres routes
@app.route('/')
def accueil():
    return render_template('accueil.jinja')

@app.route('/loginformateurs', methods=['GET', 'POST'])
@db_session
def loginformateurs():
    if request.method == 'POST':
        mail = request.form['mail']
        password = request.form['MDP']
        user = get_formateurs(mail)
        if user and check_password_hash(user.MDP, password):
            session['mail'] = mail
            session['prenom'] = user.Prenom
            return redirect(url_for('formateurs'))
    
    return render_template('connectformateurs.jinja')

@app.route('/loginapprentis', methods=['GET', 'POST'])
@db_session
def loginapprentis():
    if request.method == 'POST':
        mail = request.form['mail']
        password = request.form['MDP']
        user = get_apprentis(mail)
        if user and check_password_hash(user.MDP, password):
            session['mail'] = mail
            session['prenom'] = user.Prenom
            return redirect(url_for('apprentis'))
    
    return render_template('accueil.jinja')

@app.route('/logout')
def logout():
    session.pop('mail', None)
    session.pop('prenom', None)
    return redirect(url_for('accueil'))

@app.route('/centres.jinja')
def centres():
    return render_template('centres.jinja')

@app.route('/connectformateurs.jinja')
def connect():
    return render_template('connectformateurs.jinja')

@app.route('/espaceformateurs.jinja')
def formateurs():
    if 'mail' in session:
        prenom = session['prenom']
        return render_template('espaceformateurs.jinja', prenom=prenom)
    else:
        return redirect(url_for('loginformateurs'))

@app.route('/espaceapprentis.jinja')
def apprentis():
    if 'mail' in session:
        prenom = session['prenom']
        return render_template('espaceapprentis.jinja', prenom=prenom)
    else:
        return redirect(url_for('loginapprentis'))

@db_session
def get_formateurs(mail):
    user = Formateurs.get(Mail=mail)
    return user

@db_session
def get_apprentis(mail):
    user = Apprentis.get(Mail=mail)
    return user

if __name__ == '__main__':
    app.run(debug=True)
