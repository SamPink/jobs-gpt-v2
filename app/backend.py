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

system_message = (
    "You are a recruiter. "
    "Your task is to evaluate the match between a CV and a job description. "
    "You need to break down the real-world requirements of the job in a structured way."
    "Try to understand what the candate will actually be doing in the job and if they have the skills to do it."
    "Consider skills, experience, qualifications, and cultural fit. "
    "Provide a score for each category and an overall score."
    "Be harsh, the job market is competitive, if the candidate has missing skills they are not going to get the job!"
    "Return the scores for each category and an overall score along with some feedback for the candidate."
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
            chips_filters=job_search_request.chips_filters
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




if __name__ == "__main__":
    import uvicorn

    # Get the PORT from environment variable or default to 8000
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
