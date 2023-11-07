import streamlit as st
import openai
from serpapi import GoogleSearch

import os

openai_key = os.getenv("OPENAI_API_KEY")
serpapi_key = os.getenv("SERPAPI_API_KEY")


# Function to perform the job search
def job_search(query, location, serpapi_key):
    params = {
        "engine": "google_jobs",
        "q": query,
        "location": location,
        "hl": "en",
        "api_key": serpapi_key,
    }

    search = GoogleSearch(params)
    results = search.get_dict()
    return results.get("jobs_results", [])


# Function to summarize job descriptions using OpenAI
def summarize_job(job_details, openai_key):
    # Initialize OpenAI with the API key
    openai.api_key = openai_key

    # Generate a summary using GPT-4
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4-1106-preview",  # Make sure to use the appropriate model ID
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant. Please summarize the following job description in JSON format. try to break down the real world requirements of the job in a structured way",
                },
                {
                    "role": "user",
                    "content": f"Here is the job description: {job_details}",
                },
            ],
            response_format={"type": "json_object"},  # Enable JSON mode
        )
        summary = response.choices[0].message[
            "content"
        ]  # Access the content key in the JSON response
        return summary
    except openai.error.OpenAIError as e:
        st.error(f"An error occurred with OpenAI: {e}")
        return "No summary available."


# Streamlit app
def main():
    st.title("Job Search with SerpApi and Summary with OpenAI")

    # User input for job search
    query = st.text_input("Job Title", "Python ir35")
    location = st.text_input("Location", "London")

    # When the 'Search' button is clicked, perform the job search and summarize
    if st.button("Search"):
        if serpapi_key and openai_key:
            jobs = job_search(query, location, serpapi_key)
            if jobs:
                for job in jobs:
                    st.subheader(job.get("title", "No Title"))
                    st.write("Company:", job.get("company_name", "No Company Name"))
                    st.write("Location:", job.get("location", "No Location"))
                    job_details = job.get("description", "No Description")
                    summary = summarize_job(job_details, openai_key)
                    st.json(summary)  # Display the JSON summary in a formatted way
                    st.write("---")
            else:
                st.error(
                    "No jobs found or there was an error in the search. Please try again."
                )
        else:
            st.error("Please enter valid SerpApi and OpenAI API Keys.")


if __name__ == "__main__":
    main()
