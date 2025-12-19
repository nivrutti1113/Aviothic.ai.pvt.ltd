# Report generation module
def generate_report(prediction_result):
    """
    Generate a medical report based on the prediction result
    """
    report_template = f"""
    AVIOTHIC AI MEDICAL REPORT
    ==========================
    
    Prediction: {prediction_result['prediction']}
    Confidence: {prediction_result['confidence'] * 100:.2f}%
    Model Version: {prediction_result['model_version']}
    
    Note: This is an AI-assisted diagnosis. Please consult with a medical professional for final diagnosis.
    """
    
    return report_template.strip()