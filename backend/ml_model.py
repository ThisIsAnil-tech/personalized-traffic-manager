import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import joblib
import os

def train_model():
    df = pd.read_csv("C:\\Users\\gaaye\\OneDrive\\Documents\\mini project\\input_sample.csv")
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

if not os.path.exists('model.pkl'):
    train_model()

def suggest_route_preference(user_profile):
    model = joblib.load('model.pkl')
    le_speed, le_vehicle, le_route, le_output = joblib.load('encoders.pkl')

    def safe_transform(encoder, value):
        if value in encoder.classes_:
            return encoder.transform([value])[0]
        fallback = encoder.classes_[0]
        print(f"⚠️ Warning: '{value}' not in encoder classes {list(encoder.classes_)}. Falling back to '{fallback}'.")
        return encoder.transform([fallback])[0]

    speed = safe_transform(le_speed, user_profile.get('preferred_speed', 'medium'))
    vehicle = safe_transform(le_vehicle, user_profile.get('vehicle_type', le_vehicle.classes_[0]))
    route = safe_transform(le_route, user_profile.get('route_type', le_route.classes_[0]))

    X_input = pd.DataFrame([{
        'speed': speed,
        'vehicle': vehicle,
        'route': route
    }])

    pred_encoded = model.predict(X_input)[0]
    pred_label = le_output.inverse_transform([pred_encoded])[0]
    print(le_route.classes_)

    print(f"Preferred speed: {user_profile.get('preferred_speed', 'medium')}")
    print(f'vehicle type: {user_profile.get("vehicle_type", le_vehicle.classes_[0])}')
    print(f"route type: {user_profile.get('route_type', le_route.classes_[0])}")
    print(f'predicted route preference: {pred_label}')
    return pred_label
