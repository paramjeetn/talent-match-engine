import google.generativeai as genai
import json
import re

# Configure the Gemini API key
genai.configure(api_key="YOUR_GEMINI_API_KEY")

def generate_resume_from_profile(stringified_profile):
    """
    Generate a resume JSON object using the student's profile details from a stringified JSON input.
    """

    # Create the dynamic prompt using the student profile
    prompt = f"""
    The following stringified JSON represents a student profile:
    
    ```json
    {stringified_profile}
    ```
    
    Using the details provided in the above profile, generate a **detailed resume JSON** with a professional structure. Also, include an **ATS analysis** to improve the resume.

    ### ✅ Resume Structure:
    {{
      "personal_information": {{
        "full_name": "Full Name",
        "email": "Valid email",
        "phone_number": "Phone number",
        "linkedin_profile": "LinkedIn (if available)",
        "github_profile": "GitHub (if available)",
        "summary": "Brief professional summary"
      }},
      "education": {{
        "degree": "Degree and major",
        "university": "University name",
        "graduation_year": "Year",
        "cgpa": "GPA (if available)"
      }},
      "work_experience": [
        {{
          "job_title": "Job Title",
          "company": "Company Name",
          "location": "Location",
          "start_date": "YYYY-MM-DD",
          "end_date": "YYYY-MM-DD",
          "responsibilities": ["Task 1", "Task 2"],
          "achievements": ["Achievement 1", "Achievement 2"]
        }}
      ],
      "skills": {{
        "technical": ["Skill 1", "Skill 2"],
        "soft": ["Skill 1", "Skill 2"]
      }},
      "projects": [
        {{
          "title": "Project Title",
          "description": "Brief project description",
          "technologies": ["Tech 1", "Tech 2"],
          "url": "GitHub URL (if available)"
        }}
      ],
      "ats_analysis": {{
        "strengths": ["List of resume strengths"],
        "weaknesses": ["List of weaknesses"],
        "suggestions": ["Suggested improvements for ATS ranking"]
      }}
    }}

    Ensure that:
    - The **JSON is valid** and strictly follows the structure.
    - The **ATS analysis is accurate**, giving useful suggestions for improvement.
    - The **data is filled from the provided profile**, adding missing sections if necessary.
    """

    # Call Gemini API
    model = genai.GenerativeModel("gemini-1.5-pro")
    response = model.generate_content(prompt)

    # Extract JSON object from response
    match = re.search(r'\{.*\}', response.text, re.DOTALL)
    if match:
        json_str = match.group(0)  # Extract matched JSON
        try:
            return json.loads(json_str)  # Return parsed JSON
        except json.JSONDecodeError as e:
            print("❌ Failed to parse JSON:", e)
            print("🔍 Response content:", response.text)  # Debugging
            return None
    else:
        print("❌ Failed to extract JSON from response.")
        return None


# Example student profile
stringified_profile = json.dumps({
    "name": "John Doe",
    "university": "Massachusetts Institute of Technology",
    "personalInfo": {
        "dateOfBirth": "1998-07-15",
        "phoneNumber": "+1 123 456 7890",
        "address": "Cambridge, MA, USA"
    },
    "education": {
        "degree": "Bachelor of Science",
        "major": "Computer Science and Engineering",
        "year": 2020,
        "cgpa": 3.85
    },
    "skills": [
        {"name": "Java", "level": "Advanced"},
        {"name": "Python", "level": "Intermediate"},
        {"name": "JavaScript", "level": "Advanced"},
        {"name": "C++", "level": "Intermediate"},
        {"name": "SQL", "level": "Advanced"}
    ],
    "certifications": [
        {
            "name": "AWS Certified Solutions Architect - Associate",
            "issuer": "Amazon Web Services",
            "date": "2022-06-10",
            "credentialUrl": "https://aws.amazon.com/certification/"
        }
    ],
    "projects": [
        {
            "title": "E-commerce Platform",
            "description": "Developed a full-stack e-commerce platform using React, Node.js, and MongoDB.",
            "technologies": ["React", "Node.js", "MongoDB"],
            "url": "https://github.com/example/e-commerce-platform"
        }
    ],
    "internships_or_work_experience": [
        {
            "job_title": "Software Engineering Intern",
            "organization": "Google",
            "location": "Mountain View, CA",
            "start_date": "2019-06-01",
            "end_date": "2019-09-01",
            "key_responsibilities": [
                "Developed and tested new features for Google Maps",
                "Improved the performance of existing code"
            ],
            "achievements": [
                "Successfully launched a new feature that improved user engagement by 10%"
            ],
            "description": "Worked as a Software Engineering Intern at Google."
        }
    ]
})

# Generate and analyze the resume
resume_json = generate_resume_from_profile(stringified_profile)

# Print the generated resume with ATS analysis
print(json.dumps(resume_json, indent=2))
