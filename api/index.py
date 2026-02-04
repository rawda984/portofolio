import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Charger les variables d'environnement
load_dotenv()

app = Flask(__name__)
# Autoriser le Frontend à parler au Backend
CORS(app) 

# CONFIGURATION BASE DE DONNÉES
# En local : sqlite
# Sur Vercel (Supabase) : postgresql://user:pass@host/db
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///site.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- MODÈLES DE LA BASE DE DONNÉES ---
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=db.func.current_timestamp())

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(200), default='https://picsum.photos/400/250')

# Créer les tables au démarrage (pour la démo locale)
with app.app_context():
    db.create_all()

# --- ROUTES API ---

# 1. Récupérer tous les messages (Pour l'Admin)
@app.route('/api/messages', methods=['GET'])
def get_messages():
    messages = Message.query.order_by(Message.date.desc()).all()
    output = []
    for msg in messages:
        output.append({
            'id': msg.id,
            'name': msg.name,
            'email': msg.email,
            'message': msg.message,
            'date': msg.date.strftime('%Y-%m-%d %H:%M:%S')
        })
    return jsonify(output)

# 2. Contact : Sauvegarder en BDD + Envoyer Email
@app.route('/api/contact', methods=['POST'])
def contact():
    data = request.json
    
    # Sauvegarder dans la BDD
    new_msg = Message(name=data['name'], email=data['email'], message=data['message'])
    db.session.add(new_msg)
    db.session.commit()
    
    # Envoyer l'email
    send_email(data['name'], data['email'], data['message'])
    
    return jsonify({'status': 'success', 'message': 'Message envoyé et sauvegardé !'})

def send_email(name, user_email, user_message):
    try:
        EMAIL_USER = os.environ.get('EMAIL_USER')
        EMAIL_PASS = os.environ.get('EMAIL_PASS')
        
        if not EMAIL_USER or not EMAIL_PASS:
            print("Email non configuré dans .env")
            return

        msg = MIMEMultipart()
        msg['From'] = EMAIL_USER
        msg['To'] = EMAIL_USER # On s'envoie le message à soi-même
        msg['Subject'] = f"Nouveau contact de {name} depuis le Portfolio"

        body = f"Nom: {name}\nEmail: {user_email}\n\nMessage:\n{user_message}"
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.send_message(msg)
        server.quit()
        print("Email envoyé avec succès")
    except Exception as e:
        print(f"Erreur email: {e}")

# 3. Récupérer les projets
@app.route('/api/projects', methods=['GET'])
def get_projects():
    projects = Project.query.all()
    output = []
    for p in projects:
        output.append({
            'id': p.id,
            'title': p.title,
            'description': p.description,
            'image_url': p.image_url
        })
    return jsonify(output)

# 4. Ajouter un projet (Admin)
@app.route('/api/projects', methods=['POST'])
def add_project():
    data = request.json
    new_proj = Project(title=data['title'], description=data['description'], image_url=data.get('image_url'))
    db.session.add(new_proj)
    db.session.commit()
    return jsonify({'status': 'success'})

# 5. Supprimer un projet (Admin)
@app.route('/api/projects/<int:id>', methods=['DELETE'])
def delete_project(id):
    project = Project.query.get_or_404(id)
    db.session.delete(project)
    db.session.commit()
    return jsonify({'status': 'deleted'})

# Route racine pour tester si Vercel marche
@app.route('/')
def home():
    return "Backend Portfolio actif !"

if __name__ == '__main__':
    app.run(debug=True, port=5000)