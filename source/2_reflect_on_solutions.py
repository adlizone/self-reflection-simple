# Import packages
import os
import pandas as pd
import openai
from models.model_factory import ModelFactory
from agents.agent_factory import AgentFactory
from problems.exam_reader import ExamReader
from details.details_reader import DetailsReader
from dialogs.dialog_reader import DialogReader
from dialogs.dialog_writer import DialogWriter

# Set the models
model_names = [
    "phi-4"
]


# Set the agent name
agent_name = "reflection"

# Set the exams
exam_names = [
    "logiqa-en-100",
]

# Set the attempt id
attempt_id = 1

# Create the components
model_factory = ModelFactory()
agent_factory = AgentFactory()
exam_reader = ExamReader()
details_reader = DetailsReader()
dialog_reader = DialogReader()
dialog_writer = DialogWriter()

# Loop through each model
for model_name in model_names:

    # Loop through each exam
    for exam_name in exam_names:

        # Set file and folder paths
        start_time = pd.Timestamp.now()
        previous_experiment_name = f"{model_name} - baseline - {exam_name}"
        current_reflection_name = f"{model_name} - {agent_name} - {exam_name}"
        exam_file_path = f"../data/exams/{exam_name}.jsonl"
        details_file_path = f"../data/details/{previous_experiment_name}.csv"
        problem_dialogs_folder_path = f"../data/dialogs/{previous_experiment_name}"
        reflection_dialogs_folder_path = f"../data/dialogs/{current_reflection_name}"

        # Create the folders
        os.makedirs(reflection_dialogs_folder_path, exist_ok=True)
     
        print(reflection_dialogs_folder_path)

        # Load the exam
        exam = exam_reader.read(exam_file_path)

        # Loop through each exam problem
        for i, problem in enumerate(exam.problems):
            problem_id = i + 1

            # # DEBUG: Answer only the first n problems
            #if i >= 10:
            #    break

            # Skip the problem if it was already answered correctly
            if details_reader.is_correct(details_file_path, problem_id):
                continue
            
            print(problem_id)

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