import streamlit as st
import os
import json
#from PyPDF2 import PdfReader
import base64
#import fitz


if "submitted" not in st.session_state:
    st.session_state.submitted = False
if "loading" not in st.session_state:
    st.session_state.loading = False
if "interim" not in st.session_state:
    st.session_state.interim = False
if "main_interface" not in st.session_state:
    st.session_state.main_interface = False

if not st.session_state.submitted:
    st.title("Upload Question Paper and Answer Sheet")
    question_paper = st.file_uploader("Upload Question Paper", type=["pdf"])
    answer_sheet = st.file_uploader("Upload Answer Sheet", type=["pdf"])

    if st.button("Submit"):
        if question_paper and answer_sheet:
            st.session_state.loading = True
        else:
            st.warning("Please upload both the question paper and answer sheet.")

if st.session_state.loading:
    with st.spinner("Processing... Please wait."):
        st.session_state.submitted = True
        st.session_state.loading = False
        st.session_state.interim = True

if st.session_state.interim:
    st.title("PDF Preview and Instructions")
    
    col1, col2 = st.columns([3,1])

    with col1:
        st.subheader("Answer Sheet")
        answer_sheet = "1.pdf"
        with open(answer_sheet, "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode("utf-8")
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="500" height="900" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)

    with col2:
        st.subheader("OCR Results")
        txt_path = "1.txt"
        if os.path.exists(txt_path):
            with open(txt_path, "r", encoding="utf-8") as file:
                instructions = file.read()
            html = f"""
            <div style="height: 700px; width: 500px; overflow-y: scroll; border: 2px solid #ccc; padding: 10px;">
            {instructions}
            </div>
            """
            st.markdown(html, unsafe_allow_html=True)


        

    if st.button("Go to Evaluation"):
        st.session_state.interim = False
        st.session_state.main_interface = True
        st.rerun()

if st.session_state.main_interface:
    
    
    base_path = "Students_Answer_Sheets"

    folder_names = ["Select an Answer Sheet"] + [folder for folder in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, folder))]
    selected_folder = st.sidebar.selectbox("Select an Answer Sheet", folder_names)

    if selected_folder != "Select an Answer Sheet":
        folder_path = os.path.join(base_path, selected_folder)

        structured_data_path = os.path.join(folder_path, "structured.json")
        feedback_path = os.path.join(folder_path, "feedback.json")
        grades_path = os.path.join(folder_path, "grading.json")
        evaluation_path = os.path.join(folder_path, "evaluation.json")



        with open(structured_data_path) as f:
            questions_data = json.load(f)

        with open(evaluation_path) as f:
            evaluation_data = json.load(f)

        with open(grades_path) as f:  
            grades_data = json.load(f)

        with open(feedback_path) as feedback_file:
            feedback_data = json.load(feedback_file)

        if 'index' not in st.session_state:
            st.session_state.index = 0

        def navigate(direction):
            if direction == "next" and st.session_state.index < len(questions_data['answers']) - 1:
                st.session_state.index += 1
            elif direction == "previous" and st.session_state.index > 0:
                st.session_state.index -= 1
            for key in list(st.session_state.keys()):
                if key.startswith("checkbox_"):
                    st.session_state[key] = False


        st.sidebar.write("### Answer Sheet Details")
        st.sidebar.write(f"**Student Name:** `{selected_folder}`")
        st.sidebar.write(f"**Current Question Number:** {st.session_state.index + 1}")

        st.sidebar.markdown("---")

        col3, col4 = st.sidebar.columns([6, 5])
        with col3:
            if st.button("Previous Question"):
                navigate("previous")

        with col4:
            if st.button("Next Question"):
                navigate("next")

        # if st.sidebar.button("Previous question", key="prev"):
        #     navigate("previous")
        # if st.sidebar.button("Next question", key="next"):
        #     navigate("next")

        if st.sidebar.button("Go back to First Question"):
            st.session_state.index = 0 
            for key in list(st.session_state.keys()):
                if key.startswith("checkbox_"):
                    st.session_state[key] = False

        total_questions = len(questions_data['answers'])
        desired_question = st.sidebar.number_input(
        "Go to Question Number:",
        min_value=1,  
        max_value=total_questions,  
        value=st.session_state.index + 1,  
        step=1  
        )

        if st.sidebar.button("Go"):
            st.session_state.index = desired_question - 1
            for key in list(st.session_state.keys()):
                if key.startswith("checkbox_"):
                    st.session_state[key] = False

        st.sidebar.markdown("---")

        formatted_grade = f"{grades_data['total_marks']:.2f}"
        st.sidebar.write(f"**Total Marks:** {formatted_grade}") 

        final_feedback = feedback_data.get("final_feedback", "")
        #st.sidebar.markdown(final_feedback)

        show_feedback = st.sidebar.checkbox("Show Feedback for the Student")
        if show_feedback:
            st.sidebar.markdown(final_feedback)

        col2, col3 = st.columns([3, 3])


        with col2:
            current_question = questions_data['answers'][st.session_state.index]
            question_text = current_question['question_text'].replace("\\n", "\n").replace("\\n\\n", "\n\n").replace("\n\n", "<br>").replace("\n", "<br>")
            student_answer = current_question['student_answer'].replace("\\n", "\n").replace("\\n\\n", "\n\n").replace("\n\n", "<br>").replace("\n", "<br>").replace("`", "")
            question_number = current_question['question_number']

            grade = grades_data.get(str(question_number), "N/A")

            eval_key = str(question_number)
            evaluations = evaluation_data[eval_key]['student_answer_evaluations']

            #st.write("### Question")
            st.info(f"**Q{question_number}:** {question_text}")

            highlighted_answer = student_answer 

            for i, (rubric, details) in enumerate(evaluations.items(), start=1):
                relevant_portion = details['relevant_portion_student'].replace("\\n", "\n").replace("\\n\\n", "\n\n").replace("\n\n", "<br>").replace("\n", "<br>")
                if st.session_state.get(f"checkbox_{i}", False):
                    color = 'green' if details['evaluation'] else 'red'
                    highlighted_answer = highlighted_answer.replace(
                        relevant_portion,
                        f"<span style='background-color:{color}; color: white;'>{relevant_portion}</span>"
                    )


            st.markdown(f"**Student Answer:** <br> {highlighted_answer}", unsafe_allow_html=True)

            st.markdown("---")

            st.markdown(f"<div style='font-size: 20px;'><strong>Grade for this question:</strong> {grade}</div>", unsafe_allow_html=True)
            st.write("")

            st.checkbox("Show Feedback for current answer", key="show_feedback")    
            current_feedback = feedback_data.get(str(question_number), "")
            if st.session_state.get("show_feedback", False):
                st.markdown(current_feedback)

        with col3:
            condition = details['evaluation']
            st.write("### Rubric Evaluation")
            for i, (rubric, details) in enumerate(evaluations.items(), start=1):
                rubric_name = f"Rubric {i}"
                explanation = details['explanation']
                st.checkbox(rubric, key=f"checkbox_{i}")

                if st.session_state.get(f"checkbox_{i}", False):
                    st.warning(f"{explanation}") 

    else:
        st.header("Please select an answer sheet from the sidebar")