import streamlit as st
from apis import OpenAIClient, SerpAPIClient

openai_client = OpenAIClient()
serpapi_client = SerpAPIClient()


def get_job_details(job):
    return {
        "title": job.get("title", "No Title"),
        "company_name": job.get("company_name", "No Company Name"),
        "location": job.get("location", "No Location"),
        "description": job.get("description", "No Description"),
        "apply_link": serpapi_client.get_apply_link(job.get("job_id")),
    }


def display_job_and_evaluate_cv(job_details, user_cv):
    # check the user has entered a CV
    if not user_cv:
        st.warning("Please paste your CV above before searching.")
        return
    with st.container():
        st.write("Job Title:", job_details["title"])
        st.write("Company Name:", job_details["company_name"])
        st.write("Location:", job_details["location"])
        st.markdown(
            f"[Apply Here]({job_details['apply_link']})", unsafe_allow_html=True
        )
        summary = openai_client.summarize_job(job_details["description"])
        st.markdown("### Job Summary")
        if summary:
            st.json(summary)

        cv = openai_client.summarize_cv(user_cv)
        evaluation = openai_client.cv_job_match(cv, summary)
        if evaluation:
            st.markdown("### Evaluation Results")
            st.json(evaluation)


def extract_text_from_pdf(pdf_file):
    import fitz  # PyMuPDF

    text = ""
    # Ensure the file stream is in bytes
    file_stream = pdf_file.read()
    try:
        # Open the stream using 'fitz'
        with fitz.open(stream=file_stream, filetype="pdf") as doc:
            for page in doc:
                text += page.get_text()
    except Exception as e:
        # Handle exceptions that may occur
        raise e
    return text


def extract_text_from_docx(docx_file):
    from docx import Document

    doc = Document(docx_file)
    return "\n".join([paragraph.text for paragraph in doc.paragraphs])


def main():
    st.title("Job Search, Summary, and CV Evaluation")

    st.markdown(
        """
        This app uses the [OpenAI API](https://platform.openai.com/docs/overview) to summarize job descriptions and CVs, 
        and the [SerpAPI](https://serpapi.com/) to search for jobs.
        Once you click the 'Search Jobs' button, the app will search for jobs using the SerpAPI, and summarize the job description.
        After this an evaluation will be performed on the CV and job description using the (below the job description).
        """
    )

    # User input for job search
    query = st.text_input("Job Title", "Python Developer")
    location = st.text_input("Location", "London")
    # user_cv = st.text_area("Paste your CV here", height=300)

    # Upload CV as a file, PDF, Word, or text
    user_cv = st.file_uploader("Upload CV", type=["pdf", "txt", "docx"])

    # Convert uploaded file to text
    if user_cv:
        with st.spinner("Processing file..."):
            try:
                if user_cv.type == "application/pdf":
                    user_cv_text = extract_text_from_pdf(user_cv)
                elif user_cv.type == "text/plain":
                    user_cv_text = user_cv.read().decode("utf-8")
                elif (
                    user_cv.type
                    == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                ):
                    user_cv_text = extract_text_from_docx(user_cv)
                else:
                    st.error(
                        "Unsupported file type. Please upload a PDF, DOCX, or TXT file."
                    )
                    user_cv_text = None
            except Exception as e:
                st.error(f"An error occurred during file processing: {e}")
                user_cv_text = None
    else:
        user_cv_text = None

    # Session state initialization
    session_state = st.session_state
    if "current_job_index" not in session_state:
        session_state.current_job_index = 0
    if "jobs" not in session_state:
        session_state.jobs = []

    # Search button and results handling
    if st.button("Search Jobs"):
        if not user_cv_text:
            st.warning("Please paste your CV above before searching.")
            return
        try:
            with st.spinner("Finding you a job..."):
                extracted_skills = openai_client.extract_skills_from_cv(user_cv_text)
                # Combine extracted skills with the original query
                enhanced_query = f"{query} {' '.join(extracted_skills)}"

                results = serpapi_client.search_jobs(query, location, enhanced_query)
                session_state.jobs = results
                session_state.current_job_index = 0
                if not results:
                    st.info("No jobs found. Try different search criteria.")
                    return
                job_details = get_job_details(results[session_state.current_job_index])
                display_job_and_evaluate_cv(job_details, user_cv_text)
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
            display_job_and_evaluate_cv(job_details, user_cv_text)
        else:
            st.info("You've reached the end of the job list.")


if __name__ == "__main__":
    main()
