import streamlit as st
import openai
from serpapi import GoogleSearch
import os

# Load API keys from environment variables
openai_key = os.getenv("OPENAI_API_KEY")
serpapi_key = os.getenv("SERP_API_KEY")

if not openai_key or not serpapi_key:
    raise EnvironmentError(
        "Missing API keys. Please set OPENAI_API_KEY and SERPAPI_API_KEY."
    )

# Initialize OpenAI with the API key
openai.api_key = openai_key


def get_job_details(job):
    try:
        return {
            "title": job.get("title", "No Title"),
            "company_name": job.get("company_name", "No Company Name"),
            "location": job.get("location", "No Location"),
            "description": job.get("description", "No Description"),
        }
    except Exception as e:
        st.error(f"An error occurred while fetching job details: {e}")
        return None


def summarize_job(description):
    try:
        response = openai.ChatCompletion.create(
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
        return response.choices[0].message["content"]
    except Exception as e:
        st.error(f"An error occurred with OpenAI: {e}")
        return None


# Streamlit app
def main():
    st.title("Job Search and Summary")

    # User input for job search
    query = st.text_input("Job Title", "Python ir35")
    location = st.text_input("Location", "London")

    # When the 'Search' button is clicked, perform the job search and summarize
    if st.button("Search"):
        try:
            search = GoogleSearch(
                {
                    "engine": "google_jobs",
                    "q": query,
                    "location": location,
                    "hl": "en",
                    "api_key": serpapi_key,
                }
            )
            jobs = search.get_dict().get("jobs_results", [])
        except Exception as e:
            st.error(f"An error occurred during search: {e}")
            return

        for job in jobs:
            job_details = get_job_details(job)
            if job_details:
                st.subheader(job_details["title"])
                st.write("Company:", job_details["company_name"])
                st.write("Location:", job_details["location"])
                summary = summarize_job(job_details["description"])
                if summary:
                    st.json(summary)  # Display the JSON summary in a formatted way
                st.write("---")


if __name__ == "__main__":
    main()
