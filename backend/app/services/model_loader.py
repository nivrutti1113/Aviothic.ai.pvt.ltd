# Model loading service
import tensorflow as tf
from ..config import Config

class ModelLoader:
    def __init__(self):
        self.model = None
        self.load_model()
    
    def load_model(self):
        """Load the trained model"""
        try:
            self.model = tf.keras.models.load_model(Config.MODEL_PATH)
        except Exception as e:
            print(f"Error loading model: {e}")
            self.model = None
    
    def predict(self, image_data):
        """Make prediction using the loaded model"""
        if self.model is None:
            raise Exception("Model not loaded")
        
        # Preprocess image_data as needed
        # prediction = self.model.predict(image_data)
        # return prediction
        return 0.5  # Dummy prediction