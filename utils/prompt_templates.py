from string import Template

SKILL_ASSESSMENT_PROMPT = Template("""
You are a skill assessment expert. Please evaluate the following skills and create 
appropriate assessment questions:

Skills: $skills

Please generate:
1. Technical questions
2. Practical scenarios
3. Knowledge assessment
""")

RESUME_REVIEW_PROMPT = Template("""
As a professional resume reviewer, please analyze the following resume:

Resume Content:
$resume_content

Please provide:
1. Overall assessment
2. Strengths
3. Areas for improvement
4. ATS compatibility suggestions
5. Industry-specific recommendations
""")

INTERVIEW_ASSESSMENT_PROMPT = Template("""
As an interview assessor, please evaluate the following video interview transcript:

Interview Transcript:
$interview_transcript

Please assess:
1. Communication skills
2. Technical knowledge
3. Problem-solving ability
4. Cultural fit
5. Areas for improvement
""")