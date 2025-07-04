from sklearn.preprocessing import LabelEncoder
import numpy as np

class MultiFeatureEncoder:
    def __init__(self):
        self.vehicle_encoder = LabelEncoder()
        self.vehicle_classes = ['bike', 'car', 'truck','plane']
        self.vehicle_encoder.fit(self.vehicle_classes)
        
        self.fuel_encoder = LabelEncoder()
        self.fuel_classes = ['petrol', 'diesel', 'electric','hydrogen']
        self.fuel_encoder.fit(self.fuel_classes)

    def encode_vehicle(self, vehicle_type):
        if vehicle_type not in self.vehicle_classes:
            print(f"Warning: '{vehicle_type}' not in vehicle classes {self.vehicle_classes}. Falling back to 'bike'.")
            vehicle_type = 'bike'
        return self.vehicle_encoder.transform([vehicle_type])[0]

    def encode_fuel(self, fuel_type):
        if fuel_type not in self.fuel_classes:
            print(f"Warning: '{fuel_type}' not in fuel classes {self.fuel_classes}. Falling back to 'petrol'.")
            fuel_type = 'petrol'
        return self.fuel_encoder.transform([fuel_type])[0]

    def decode_vehicle(self, encoded_value):
        return self.vehicle_encoder.inverse_transform([encoded_value])[0]

    def decode_fuel(self, encoded_value):
        return self.fuel_encoder.inverse_transform([encoded_value])[0]


if __name__ == "__main__":
    encoder = MultiFeatureEncoder()

    vehicles = ['car', 'bike', 'plane']   
    fuels = ['diesel', 'petrol', 'hydrogen']  

    for v in vehicles:
        print(f"Vehicle '{v}' encoded as: {encoder.encode_vehicle(v)}")

    for f in fuels:
        print(f"Fuel '{f}' encoded as: {encoder.encode_fuel(f)}")
