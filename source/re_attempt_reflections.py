import os
import pandas as pd
from datetime import datetime
from models.model_factory import ModelFactory
from agents.agent_factory import AgentFactory
from problems.exam_reader import ExamReader
from details.details_writer import DetailsWriter
from details.details_row import DetailsRow
from details.details_reader import DetailsReader
from dialogs.dialog_writer import DialogWriter
from dialogs.dialog_reader import DialogReader

# Set the model and agent
model_name = "phi-4"  # Replace with your model name
agent_name = "reflection"
attempt_id = 1  # Increment this if needed

# Set the exam
exam_name = "logiqa-en-100"
exam_path = f"../data/exams/{exam_name}.jsonl"

# Set file paths
previous_experiment_name = f"{model_name} - baseline - {exam_name}"
current_reflection_name = f"{model_name} - {agent_name} - {exam_name}"
details_file_path = f"../data/details/{previous_experiment_name}.csv"
problem_dialogs_folder_path = f"../data/dialogs/{previous_experiment_name}"
reflection_dialogs_folder_path = f"../data/dialogs/{current_reflection_name}"

# Create the components
model_factory = ModelFactory()
agent_factory = AgentFactory()
exam_reader = ExamReader()
dialog_writer = DialogWriter()
dialog_reader = DialogReader()
details_writer = DetailsWriter()
details_reader = DetailsReader()

# Load the exam
exam = exam_reader.read(exam_path)

# Step 1: Read the details.csv file
if os.path.exists(details_file_path):
    details_df = pd.read_csv(details_file_path)
    details = details_df.to_dict("records")
else:
    details = []
    
print("Printing all rows:")
for row in details:
    print(row["problem_id"])

# Step 2: Identify rows with errors (failed or timed-out requests)
error_rows = [
    row for row in details
    if "Error" in str(row["response"]) or pd.notna(row["error"]) and row["error"] != ""
]

print("Printing error rows")
for row in error_rows:
    print(row["problem_id"])

# Step 3: Re-run the reflection agent for error rows
for row in error_rows:
    problem_id = row["problem_id"]
    problem = exam.problems[problem_id - 1]  # Problem IDs start from 1

    # Create the agent
    model = model_factory.create(model_name)
    reflect_agent = agent_factory.create(agent_name, model, problem.topic)

    # Create the new dialog
    reflect_agent.create_dialog()

    # Load the previous dialog
    reflection_dialog_file_path = f"{problem_dialogs_folder_path}/Problem {problem_id}.json"
    dialog = dialog_reader.read(reflection_dialog_file_path)

    # Create the user prompt
    problem_text = str(problem)
    solution_text = dialog.get_all()[4].content
    correct_answer = problem.answer
    user_prompt = problem_text + "\n"
    user_prompt += solution_text + "\n"
    user_prompt += "\n --- \n"
    user_prompt += f"Correct Answer: {correct_answer}\n"
    if not details_reader.has_agent_answer(details_file_path, problem_id):
        user_prompt += "Error: You did not provide your answer in the correct format.\n"
        user_prompt += "Your answer must be stated as 'Action: Answer(\"[ANSWER_CHOICE]\")';\n"
        user_prompt += "where [ANSWER_CHOICE] is the letter of the correct answer choice.\n"

    # Get the agent's reflection
    reflection_response = reflect_agent.reflect(user_prompt)

    # Save the dialog
    reflection_dialog_file_path = f"{reflection_dialogs_folder_path}/Problem {problem_id}.json"
    dialog_writer.write(reflection_dialog_file_path, reflect_agent.dialog)

    # Update the details list
    details[problem_id - 1] = {
        "problem_id": problem_id,
        "response": reflection_response.text,
        "error": reflection_response.text if reflection_response.has_error else "",
        "score": 1 if reflection_response.text == correct_answer else 0,
    }

# Step 4: Save the updated details to the CSV file
details_writer.write(details, details_file_path)

print("Re-attempt completed. Updated details saved to:", details_file_path)