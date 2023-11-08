import streamlit as st
from apis import OpenAIClient, SerpAPIClient


def get_job_details(job):
    return {
        "title": job.get("title", "No Title"),
        "company_name": job.get("company_name", "No Company Name"),
        "location": job.get("location", "No Location"),
        "description": job.get("description", "No Description"),
    }


def display_job_and_evaluate_cv(openai_client, job_details, user_cv):
    # check the user has entered a CV
    if not user_cv:
        st.warning("Please paste your CV above before searching.")
        return
    with st.container():
        st.write("Job Title:", job_details["title"])
        st.write("Company Name:", job_details["company_name"])
        st.write("Location:", job_details["location"])
        summary = openai_client.summarize_job(job_details["description"])
        if summary:
            st.json(summary)

        cv = openai_client.summarize_cv(user_cv)
        evaluation = openai_client.cv_job_match(cv, summary)
        if evaluation:
            st.markdown("### Evaluation Results")
            st.json(evaluation)


def main():
    st.title("Job Search, Summary, and CV Evaluation")

    openai_client = OpenAIClient()
    serpapi_client = SerpAPIClient()

    # User input for job search
    query = st.text_input("Job Title", "Python Developer")
    location = st.text_input("Location", "London")
    user_cv = st.text_area("Paste your CV here", height=300)

    session_state = st.session_state
    if "current_job_index" not in session_state:
        session_state.current_job_index = 0
    if "jobs" not in session_state:
        session_state.jobs = []

    # Search button and results handling
    if st.button("Search Jobs"):
        if not user_cv:
            st.warning("Please paste your CV above before searching.")
            return
        try:
            results = serpapi_client.search_jobs(query, location)
            session_state.jobs = results
            session_state.current_job_index = 0
            if not results:
                st.info("No jobs found. Try different search criteria.")
                return
            job_details = get_job_details(results[session_state.current_job_index])
            display_job_and_evaluate_cv(openai_client, job_details, user_cv)
        except Exception as e:
            st.error(f"An error occurred during search: {e}")

    # Next Job button
    if st.button("Next Job"):
        if session_state.jobs and (
            session_state.current_job_index + 1 < len(session_state.jobs)
        ):
            session_state.current_job_index += 1
            job_details = get_job_details(
                session_state.jobs[session_state.current_job_index]
            )
            display_job_and_evaluate_cv(openai_client, job_details, user_cv)
        else:
            st.info("You've reached the end of the job list.")


if __name__ == "__main__":
    main()
