from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import requests
from ml_model import suggest_route_preference
import os
from encoder_utils import MultiFeatureEncoder
import io
import csv
from flask import Response
from flask import send_file
encoder = MultiFeatureEncoder()

app = Flask(__name__, static_folder=os.path.join(os.path.pardir, 'static'))
app.secret_key = 'ajdh72n3!@#JADH83hjs8^2hd@LDF'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

ORS_API_KEY = os.environ.get('ORS_API_KEY', '5b3ce3597851110001cf6248be9e2370c69144ff8d3dbc3a9c675974') 

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    is_speed_driver = db.Column(db.Boolean, default=False)
    vehicle_type = db.Column(db.String(20), default='petrol')
    prefers_quick = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False) 

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

VALID_VEHICLE_TYPES = ['bike', 'car', 'truck']

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        is_speed_driver = request.form.get('speed_driver') == 'yes'
        vehicle_type = request.form.get('vehicle_type')
        prefers_quick = request.form.get('prefers_quick') == 'yes' 
        is_admin = request.form.get('is_admin') == 'yes'

        if vehicle_type not in VALID_VEHICLE_TYPES:
            flash(f"Invalid vehicle type. Choose from {VALID_VEHICLE_TYPES}", "error")
            return redirect(url_for('register'))

        if User.query.filter_by(username=username).first():
            flash('User already exists!', 'error')
            return redirect(url_for('register'))

        new_user = User(
            username=username,
            password=password,
            is_speed_driver=is_speed_driver,
            vehicle_type=vehicle_type,
            prefers_quick=prefers_quick,
            is_admin= is_admin
        )
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('index'))
        flash('Invalid credentials!', 'error')
        return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    return render_template('index.html')

def geocode(location):
    url = f"https://api.openrouteservice.org/geocode/search?api_key={ORS_API_KEY}&text={location}"
    response = requests.get(url)

    if response.status_code != 200:
        print(f"Geocoding failed! Status code: {response.status_code}")
        print(f"Response content: {response.text}")
        return None

    try:
        res = response.json()
        if not res or 'features' not in res or len(res['features']) == 0:
            return None
        coords = res['features'][0]['geometry']['coordinates']  
        return coords
    except Exception as e:
        print(f"JSON decode error: {e}")
        print(f"Response content: {response.text}")
        return None


@app.route('/download_users_csv')
@login_required 
def download_users_csv_for_all():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('index'))
 
    
    users = User.query.all()

    headers = [
        'id', 'username', 'is_speed_driver', 'vehicle_type', 'is_admin'
    ]

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(headers)

    for user in users:
        writer.writerow([
            user.id,
            user.username,
            'Yes' if user.is_speed_driver else 'No',
            user.vehicle_type,
            #'Yes' if user.prefers_quick else 'No',
            'Yes' if user.is_admin else 'No'
        ])

    response = Response(output.getvalue(), mimetype='text/csv')
    response.headers["Content-Disposition"] = "attachment; filename=all_users_data.csv"
    
    return response

@app.route('/make_admin/<username>')
@login_required
def make_admin(username):
    if app.debug: 
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You must be an admin to use this feature.', 'error')
            return redirect(url_for('index'))

        user = User.query.filter_by(username=username).first()
        if user:
            user.is_admin = True
            db.session.commit()
            flash(f'User {username} is now an admin!', 'success')
        else:
            flash(f'User {username} not found.', 'error')
        return redirect(url_for('index'))
    else:
        return "Admin promotion not allowed in production mode.", 403

@app.route('/route', methods=['POST'])
@login_required
def get_route():
    try:
        data = request.get_json()
        print("📥 Incoming data:", data)

        if not data:
            return jsonify({'error': 'No data received'}), 400

        from_loc = data.get('from')
        to_loc = data.get('to')

        start_coords = geocode(from_loc)
        end_coords = geocode(to_loc)

        if not start_coords or not end_coords:
            return jsonify({'error': 'Could not geocode one or both locations'}), 400

        ml_route_type = "fastest" if current_user.prefers_quick else "shortest" 

        user_profile = {
            "preferred_speed": "fast" if current_user.is_speed_driver else "medium",
            "vehicle_type": current_user.vehicle_type,
            "route_type": ml_route_type
        }
        
        route_preference = suggest_route_preference(user_profile)

        headers = {
            'Authorization': ORS_API_KEY,
            'Content-Type': 'application/json'
        }

        payload = {
            'coordinates': [start_coords, end_coords],
            'preference': route_preference
        }

        response = requests.post(
            'https://api.openrouteservice.org/v2/directions/driving-car/geojson',
            json=payload,
            headers=headers
        )

        print(f"🌍 ORS API Request URL: {response.request.url}")
        print(f"🌍 ORS API Request Payload: {payload}")
        print(f"🌍 ORS API Response Status: {response.status_code}")
        # print(f"🌍 ORS API Response Content: {response.text}")

        if response.status_code != 200:
            return jsonify({'error': 'Failed to get route from API', 'details': response.text}), response.status_code

        return jsonify(response.json())

    except Exception as e:
        print("🔥 Error in /route:", e)
        return jsonify({'error': str(e)}), 400
    
if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    with app.app_context():
        print("\n📍 Available Routes:")
        for rule in app.url_map.iter_rules():
            methods = ','.join(rule.methods)
            print(f"{rule.endpoint:20s} | {methods:20s} | {rule}")

    app.run(debug=True)