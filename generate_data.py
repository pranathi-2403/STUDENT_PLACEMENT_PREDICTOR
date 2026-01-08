# ===== generate_data.py =====
import pandas as pd
import numpy as np

np.random.seed(42)
num_samples = 5000

cgpa = np.round(np.random.uniform(5.0, 10.0, num_samples), 2)
backlogs = np.random.randint(0, 5, num_samples)
certifications = np.random.randint(0, 10, num_samples)
internship = np.random.randint(0, 3, num_samples)
aptitude = np.random.randint(0, 11, num_samples)
coding = np.random.randint(0, 11, num_samples)
communication = np.random.randint(0, 11, num_samples)
projects = np.random.randint(0, 8, num_samples)
hackathon = np.random.randint(0, 2, num_samples)
resume = np.random.randint(1, 11, num_samples)
branch_codes = ['CSE', 'ECE', 'MECH', 'CIVIL', 'ISE', 'AI&DS']
branch = np.random.choice(branch_codes, num_samples)

# Map branch to marks
branch_map = {'CSE': 5, 'ISE': 5, 'ECE': 4, 'MECH': 2, 'CIVIL': 2, 'AI&DS': 5}
branch_marks = [branch_map.get(b, 2) for b in branch]

# Placement scoring based on your custom logic
placement_scores = []
placement_readiness = []
for i in range(num_samples):
    score = (
        cgpa[i] * 2 +
        certifications[i] * 2 +
        internship[i] * 5 +
        projects[i] * 2 +
        aptitude[i] * 1.5 +
        coding[i] * 1.5 +
        communication[i] * 1.5 +
        resume[i] +
        hackathon[i] * 3 +
        branch_marks[i]
    )
    score += backlogs[i] * (-3)

    # Clamp score to range 19 to 95
    score = max(19, min(95, score))

    placement_scores.append(score)
    placement_readiness.append(1 if score >= 75 else 0)

# Company fit based on score and CGPA
company_fit = []
for i in range(num_samples):
    if placement_readiness[i] == 1:
        if cgpa[i] >= 8 and placement_scores[i] >= 85:
            company_fit.append("Tier 1")
        elif cgpa[i] >= 6 and placement_scores[i] >= 65:
            company_fit.append("Tier 2")
        elif placement_scores[i] >= 50:
            company_fit.append("Tier 3")
        else:
            company_fit.append("Not Eligible")
    else:
        company_fit.append("Not Eligible")

data = pd.DataFrame({
    'cgpa': cgpa,
    'backlogs': backlogs,
    'certifications': certifications,
    'internship': internship,
    'aptitude': aptitude,
    'coding': coding,
    'communication': communication,
    'projects': projects,
    'hackathon': hackathon,
    'resume': resume,
    'branch': branch,
    'placement_readiness': placement_readiness,
    'company_fit': company_fit,
    'placement_score': placement_scores
})

data.to_csv('data/placement_data.csv', index=False)
print("Generated data saved to 'data/placement_data.csv'")
