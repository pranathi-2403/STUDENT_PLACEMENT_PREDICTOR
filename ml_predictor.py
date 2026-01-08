# ml_predictor.py
from score_predictor import predict_score

def get_prediction_from_session(session):
    try:
        input_data = {
            'cgpa': session.get('cgpa', 0),
            'backlogs': session.get('backlogs', 0),
            'certifications': session.get('certificates', 0),
            'aptitude': session.get('aptitude_score', 0),
            'coding': session.get('technical_score', 0),
            'communication': session.get('communication_score', 0),
            'projects': session.get('Projects', 0),
            'hackathon': session.get('hackathons', 0),
            'resume': session.get('resume_score', 0),
            'branch': session.get('Branch', 'CSE')  # Default fallback
        }

        result = predict_score(input_data)
        return {
            'placement_ready': result['placement_readiness'],
            'company_fit': result['company_fit']
        }
    except Exception as e:
        print(f"Prediction error: {e}")
        return {
            'placement_ready': None,
            'company_fit': 'Error'
        }
