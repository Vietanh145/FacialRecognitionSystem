from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
import os
import face_recognition
import numpy as np
import base64
from PIL import Image
import io
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///smart_guest.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database Models
class Account(UserMixin, db.Model):
    accountId = db.Column(db.Integer, primary_key=True)
    accountName = db.Column(db.String(100), unique=True, nullable=False)
    status = db.Column(db.String(20), nullable=False)
    images = db.relationship('Image', backref='account', lazy=True)
    logs = db.relationship('Log', backref='account', lazy=True)
    roles = db.relationship('Role', secondary='role_account', backref='accounts')

    def get_id(self):
        return str(self.accountId)

class Image(db.Model):
    imageId = db.Column(db.Integer, primary_key=True)
    imageContext = db.Column(db.String(255), nullable=False)
    accountId = db.Column(db.Integer, db.ForeignKey('account.accountId'), nullable=False)
    face_encoding = db.Column(db.LargeBinary)  # Store face encoding as binary

class Role(db.Model):
    roleId = db.Column(db.Integer, primary_key=True)
    roleFunc = db.Column(db.String(50), nullable=False)

class RoleAccount(db.Model):
    roleId = db.Column(db.Integer, db.ForeignKey('role.roleId'), primary_key=True)
    userId = db.Column(db.Integer, db.ForeignKey('account.accountId'), primary_key=True)

class Log(db.Model):
    logId = db.Column(db.Integer, primary_key=True)
    accountId = db.Column(db.Integer, db.ForeignKey('account.accountId'), nullable=False)
    timeIn = db.Column(db.DateTime, nullable=False)
    timeOut = db.Column(db.DateTime)
    ipAddress = db.Column(db.String(50))
    status = db.Column(db.String(20), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return Account.query.get(int(user_id))

def save_face_encoding(image_data):
    # Convert base64 image to numpy array
    image_data = image_data.split(',')[1]
    image_bytes = base64.b64decode(image_data)
    image = Image.open(io.BytesIO(image_bytes))
    image_array = np.array(image)
    
    # Detect face and get encoding
    face_locations = face_recognition.face_locations(image_array)
    if not face_locations:
        return None
    
    face_encoding = face_recognition.face_encodings(image_array, face_locations)[0]
    return face_encoding

def compare_faces(known_encodings, face_encoding_to_check, tolerance=0.6):
    if len(known_encodings) == 0:
        return False
    
    distances = face_recognition.face_distance(known_encodings, face_encoding_to_check)
    return any(distance <= tolerance for distance in distances)

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        account_name = request.form.get('accountName')
        user = Account.query.filter_by(accountName=account_name).first()
        if user:
            login_user(user)
            # Create log entry
            log = Log(
                accountId=user.accountId,
                timeIn=datetime.now(),
                ipAddress=request.remote_addr,
                status='active'
            )
            db.session.add(log)
            db.session.commit()
            return redirect(url_for('dashboard'))
        flash('Invalid account name')
    return render_template('login.html')

@app.route('/face-login', methods=['POST'])
def face_login():
    data = request.get_json()
    image_data = data.get('image')
    
    if not image_data:
        return jsonify({'success': False, 'message': 'No image data provided'})
    
    face_encoding = save_face_encoding(image_data)
    if face_encoding is None:
        return jsonify({'success': False, 'message': 'No face detected'})
    
    # Get all accounts with their face encodings
    accounts = Account.query.all()
    for account in accounts:
        known_encodings = [np.frombuffer(img.face_encoding) for img in account.images if img.face_encoding]
        if compare_faces(known_encodings, face_encoding):
            login_user(account)
            # Create log entry
            log = Log(
                accountId=account.accountId,
                timeIn=datetime.now(),
                ipAddress=request.remote_addr,
                status='active'
            )
            db.session.add(log)
            db.session.commit()
            return jsonify({'success': True})
    
    return jsonify({'success': False, 'message': 'Face not recognized'})

@app.route('/add-face', methods=['POST'])
@login_required
def add_face():
    data = request.get_json()
    image_data = data.get('image')
    
    if not image_data:
        return jsonify({'success': False, 'message': 'No image data provided'})
    
    face_encoding = save_face_encoding(image_data)
    if face_encoding is None:
        return jsonify({'success': False, 'message': 'No face detected'})
    
    # Save image to static folder
    filename = f"face_{current_user.accountId}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Save image
    image_data = image_data.split(',')[1]
    image_bytes = base64.b64decode(image_data)
    with open(filepath, 'wb') as f:
        f.write(image_bytes)
    
    # Create image record
    image = Image(
        imageContext=filename,
        accountId=current_user.accountId,
        face_encoding=face_encoding.tobytes()
    )
    db.session.add(image)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/delete-face/<int:image_id>', methods=['DELETE'])
@login_required
def delete_face(image_id):
    image = Image.query.get_or_404(image_id)
    if image.accountId != current_user.accountId:
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    # Delete image file
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], image.imageContext)
    if os.path.exists(filepath):
        os.remove(filepath)
    
    # Delete database record
    db.session.delete(image)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/logout')
@login_required
def logout():
    # Update last log entry
    last_log = Log.query.filter_by(
        accountId=current_user.accountId,
        timeOut=None
    ).order_by(Log.timeIn.desc()).first()
    
    if last_log:
        last_log.timeOut = datetime.now()
        last_log.status = 'inactive'
        db.session.commit()
    
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True) 