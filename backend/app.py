from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field
import asyncio
import instructor
from openai import AsyncOpenAI


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


# Patch the OpenAI client for asynchronous use
async_client = instructor.apatch(AsyncOpenAI())

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


async def async_evaluate_cv(job_description, cv):
    user_message = f"""
    Job Description: {job_description}
    ---
    CV: {cv}
    """
    try:
        response = await async_client.chat.completions.create(
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
async def evaluate_cv_endpoint(
    cv_request: CVRequest, background_tasks: BackgroundTasks
):
    return await async_evaluate_cv(cv_request.job_description, cv_request.cv)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
