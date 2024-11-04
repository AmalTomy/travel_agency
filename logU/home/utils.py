from io import BytesIO
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.conf import settings
import os
from django.db import models
from django.contrib.auth.models import User
from django.db.models import F
from .models import UserLocation

def get_users_in_area(latitude, longitude, radius_km):
    return UserLocation.objects.annotate(
        distance=((F('latitude') - latitude) ** 2 + (F('longitude') - longitude) ** 2) ** 0.5
    ).filter(distance__lte=radius_km)

def send_notification(user, notification):
    # Your notification sending logic here
    pass

def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result, encoding='UTF-8')
    if not pdf.err:
        return result.getvalue()
    return None

def classify_weather(image_path):
    """Lazy loading of TensorFlow and model only when needed"""
    try:
        # Import TensorFlow only when function is called
        import tensorflow as tf
        from tensorflow.keras.preprocessing.image import img_to_array
        from PIL import Image
        import numpy as np
        from django.conf import settings
        import os

        # Load model only when needed
        model_path = settings.BASE_DIR / 'weather_classification_model.keras'
        if not hasattr(classify_weather, 'model'):
            classify_weather.model = tf.keras.models.load_model(model_path)
            
        # Get class names
        train_dir = 'D:/project/dataset/train'
        if not hasattr(classify_weather, 'weather_classes'):
            classify_weather.weather_classes = sorted(os.listdir(train_dir))

        # Process image
        img = Image.open(image_path).resize((224, 224))
        img_array = img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0)
        img_array /= 255.0

        # Predict
        prediction = classify_weather.model.predict(img_array)
        predicted_class = classify_weather.weather_classes[np.argmax(prediction)]
        return predicted_class

    except Exception as e:
        print(f"Error in weather classification: {str(e)}")
        return "Unknown"