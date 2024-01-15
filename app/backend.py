from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field
import instructor
from app.azure_gpt import get_client
from app.apis import SerpAPIClient
import os


class CVRequest(BaseModel):
    job_description: str
    cv: str


class EvaluationResponse(BaseModel):
    score_skills: float = Field(
        ..., description="Score based on the candidate's skills from 0 to 100"
    )
    score_experience: float = Field(
        ..., description="Score based on the candidate's experience from 0 to 100"
    )
    score_qualifications: float = Field(
        ..., description="Score based on the candidate's qualifications from 0 to 100"
    )
    score_cultural_fit: float = Field(
        ..., description="Score based on the candidate's cultural fit from 0 to 100"
    )
    overall_score: float = Field(..., description="Overall score of the candidate")
    feedback: str = Field(..., description="Feedback for the candidate")
    matching_skills: list = Field(
        ..., description="List of skills that match the job requirements"
    )
    missing_skills: list = Field(
        ..., description="List of skills that the candidate is missing for the job"
    )


class JobSearchRequest(BaseModel):
    query: str
    location: str
    chips_filters: str = None  # Optional, depending on your requirements


client = instructor.patch(get_client())

app = FastAPI()

# update the app name
app.title = "AI Recruiter"

# update the app description
app.description = "AI Recruiter is an AI-powered recruitment tool that helps recruiters and hiring managers to evaluate candidates and search for jobs."

# CORS setup, use * for now
from fastapi.middleware.cors import CORSMiddleware

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


system_message = (
    "**You are an AI recruiter with advanced capabilities in evaluating job suitability.**"
    "Your task is to meticulously analyze the compatibility between a candidate's CV and a specific job description. "
    "Begin by dissecting the job description into distinct categories: Key Responsibilities, Required Skills, Necessary Qualifications, and Desired Cultural Fit.  and years of experince"
    "For each category, extract and list the critical elements. "
    "Then, scrutinize the candidate's CV, focusing on their Professional Experience, Educational Background, Demonstrated Skills, and any indicators of Cultural Alignment. "
    "Evaluate the match in each category based on the following criteria: "
    "1. Skills – Do they possess the specific skills required? Consider both direct and transferable skills. "
    "2. Experience – Assess the relevance and level of their professional experience. "
    "3. Qualifications – Verify academic and professional qualifications against those required. "
    "4. Cultural Fit – Evaluate any evidence of their ability to align with the company's culture and values. "
    "Provide a score out of 10 for each category, considering the intensity of the job market and the competitive nature of the role. "
    "Be critical: if there are evident skill gaps or misalignments, reflect these in your scoring. "
    "Finally, calculate an overall suitability score, also out of 10, based on the individual category scores. "
    "In addition, formulate constructive feedback for the candidate, highlighting strengths, identifying areas for improvement, and suggesting steps they could take to increase their suitability for such roles in the future."
)


def evaluate_cv(job_description, cv):
    user_message = f"""
    Job Description: {job_description}
    ---
    CV: {cv}
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4-1106-preview",
            response_model=EvaluationResponse,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/evaluate-cv", response_model=EvaluationResponse)
def evaluate_cv_endpoint(cv_request: CVRequest, background_tasks: BackgroundTasks):
    return evaluate_cv(cv_request.job_description, cv_request.cv)


@app.post("/search-jobs")
def search_jobs_endpoint(job_search_request: JobSearchRequest):
    try:
        # Create an instance of SerpAPIClient
        serp_api_client = SerpAPIClient()

        # Call the search_jobs method
        results = serp_api_client.search_jobs(
            query=job_search_request.query,
            location=job_search_request.location,
            chips_filters=job_search_request.chips_filters,
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    # Get the PORT from environment variable or default to 8000
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
