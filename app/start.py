import streamlit as st
from apis import OpenAIClient, SerpAPIClient
from match import evaluate_cv, EvaluationResponse

openai_client = OpenAIClient()
serpapi_client = SerpAPIClient()


def get_job_details(job):
    return {
        "title": job.get("title", "No Title"),
        "company_name": job.get("company_name", "No Company Name"),
        "location": job.get("location", "No Location"),
        "description": job.get("description", "No Description"),
        "apply_link": serpapi_client.get_apply_link(job.get("job_id")),
        # Assuming thumbnail URL is part of the job dictionary
        "thumbnail": job.get("thumbnail", "https://via.placeholder.com/150"),
    }


def display_job_and_evaluate_cv(job_details, user_cv):
    if not user_cv:
        st.warning("Please paste your CV above before searching.")
        return

    # Card for job details
    with st.container():
        st.image(job_details["thumbnail"], width=100)
        st.markdown(f"### {job_details['title']} at {job_details['company_name']}")
        st.markdown(f"📍 {job_details['location']}")
        st.markdown(
            f"[Apply Here]({job_details['apply_link']})", unsafe_allow_html=True
        )
        # st.markdown("#### Job Description")
        # st.write(job_details["description"])

    # Evaluate the CV against the job description
    evaluation: EvaluationResponse = evaluate_cv(job_details["description"], user_cv)

    # Overall Score highlighted
    st.subheader("Overall Score")
    st.progress(evaluation.overall_score / 100)
    st.caption(f"{evaluation.overall_score}")

    # Non-editable feedback display
    st.subheader("Feedback")
    st.write(evaluation.feedback)
    st.write("Matching Skills: ", evaluation.matching_skills)
    st.write("Missing Skills: ", evaluation.missing_skills)

    # Display the evaluation
    st.subheader("Candidate Evaluation")
    st.progress(evaluation.score_skills / 100)
    st.caption(f"Skills Score: {evaluation.score_skills}")
    st.progress(evaluation.score_experience / 100)
    st.caption(f"Experience Score: {evaluation.score_experience}")
    st.progress(evaluation.score_qualifications / 100)
    st.caption(f"Qualifications Score: {evaluation.score_qualifications}")
    st.progress(evaluation.score_cultural_fit / 100)
    st.caption(f"Cultural Fit Score: {evaluation.score_cultural_fit}")


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
    st.title("AI Job Search, Summary, and CV Evaluation")

    st.markdown(
        """
        This app uses the [OpenAI API](https://platform.openai.com/docs/overview) to summarize job descriptions and CVs, 
        and the [SerpAPI](https://serpapi.com/) to search for jobs.
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
