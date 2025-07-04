import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import joblib
import os

CSV_PATH = 'C:\\Users\\gaaye\\OneDrive\\Documents\\VS Codes\\personalized-traffic-manager\\backend\\route_data.csv'

EXPECTED_COLUMNS = ['preferred_speed', 'vehicle_type', 'route_type', 'recommended_preference']

def train_model():
    df = pd.read_csv(CSV_PATH)
    print(df.columns.tolist())
    missing_cols = [col for col in EXPECTED_COLUMNS if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing columns in CSV: {missing_cols}")

    X = df[['preferred_speed', 'vehicle_type', 'route_type']]
    y = df['recommended_preference']

    le_speed = LabelEncoder()
    le_vehicle = LabelEncoder()
    le_route = LabelEncoder()
    le_output = LabelEncoder()

    X_encoded = pd.DataFrame({
        'speed': le_speed.fit_transform(X['preferred_speed']),
        'vehicle': le_vehicle.fit_transform(X['vehicle_type']),
        'route': le_route.fit_transform(X['route_type'])
    })

    y_encoded = le_output.fit_transform(y)

    model = RandomForestClassifier()
    model.fit(X_encoded, y_encoded)

    joblib.dump(model, 'model.pkl')
    joblib.dump((le_speed, le_vehicle, le_route, le_output), 'encoders.pkl')

    print("Model training completed and saved.")

if not os.path.exists('model.pkl') or not os.path.exists('encoders.pkl'):
    train_model()

def suggest_route_preference(user_profile):
    
    model = joblib.load('model.pkl')
    le_speed, le_vehicle, le_route, le_output = joblib.load('encoders.pkl')

    for key, le in zip(['preferred_speed', 'vehicle_type', 'route_type'], [le_speed, le_vehicle, le_route]):
        if user_profile[key] not in le.classes_:
            raise ValueError(f"Value '{user_profile[key]}' not recognized in '{key}' categories: {list(le.classes_)}")

    X_input = pd.DataFrame([{
        'speed': le_speed.transform([user_profile['preferred_speed']])[0],
        'vehicle': le_vehicle.transform([user_profile['vehicle_type']])[0],
        'route': le_route.transform([user_profile['route_type']])[0]
    }])

    pred_encoded = model.predict(X_input)[0]
    pred_label = le_output.inverse_transform([pred_encoded])[0]
    return pred_label
