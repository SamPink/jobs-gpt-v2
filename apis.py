import os
from openai import OpenAI
from serpapi import GoogleSearch
from dotenv import load_dotenv

load_dotenv()


class OpenAIClient:
    def __init__(self):
        self.openai_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_key:
            raise EnvironmentError("Please set OPENAI_API_KEY environment variable.")
        self.client = OpenAI(api_key=self.openai_key)

    def summarize_job(self, description):
        try:
            response = self.client.chat.completions.create(
                model="gpt-4-1106-preview",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant. Please summarize the following job description in JSON format. try to break down the real world requirements of the job in a structured way",
                    },
                    {
                        "role": "user",
                        "content": f"Here is the job description: {description}",
                    },
                ],
                response_format={"type": "json_object"},
            )
            return response.choices[0].message.content
        except Exception as e:
            raise e

    def summarize_cv(self, cv):
        try:
            response = self.client.chat.completions.create(
                model="gpt-4-1106-preview",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant. Please summarize the following CV in JSON format. try to break down the real world requirements of the job in a structured way",
                    },
                    {
                        "role": "user",
                        "content": f"Here is the CV: {cv}",
                    },
                ],
                response_format={"type": "json_object"},
            )
            return response.choices[0].message.content
        except Exception as e:
            raise e

    def cv_job_match(self, cv, job_description):
        try:
            response = self.client.chat.completions.create(
                model="gpt-4-1106-preview",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a helpful assistant. "
                            "Your task is to evaluate the match between a CV and a job description. "
                            "Consider skills, experience, qualifications, and cultural fit. "
                            "Provide a score for each category and an overall score."
                            "Be harsh, the job market is competitive, if the candidate has missing skills they are not going to get the job!"
                            "return a json object with the scores for each category and an overall score along with some feedback for the candidate."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Please evaluate the following CV against the job description: {job_description}\n\nCV: {cv}",
                    },
                ],
                response_format={"type": "json_object"},
            )
            return response.choices[0].message.content
        except Exception as e:
            raise e


class SerpAPIClient:
    def __init__(self):
        self.serpapi_key = os.getenv("SERP_API_KEY")
        if not self.serpapi_key:
            raise EnvironmentError("Please set SERP_API_KEY environment variable.")

    def search_jobs(self, query, location):
        try:
            search = GoogleSearch(
                {
                    "engine": "google_jobs",
                    "q": query,
                    "location": location,
                    "hl": "en",
                    "api_key": self.serpapi_key,
                }
            )
            return search.get_dict().get("jobs_results", [])
        except Exception as e:
            raise e
