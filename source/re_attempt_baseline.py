import os
import pandas as pd
from datetime import datetime
from models.model_factory import ModelFactory
from agents.agent_factory import AgentFactory
from problems.exam_reader import ExamReader
from experiments.experiment import Experiment
from experiments.result import Result
from experiments.experiments_file import ExperimentsFile
from details.details_writer import DetailsWriter
from details.details_row import DetailsRow
from details.details_reader import DetailsReader
from dialogs.dialog_writer import DialogWriter
from models.pricing import get_pricing

# Set the model and agent
model_name = "phi-4"  # Replace with your model name
agent_name = "baseline"
attempt_id = 1  # Increment this if needed

# Set the exam
exam_name = "logiqa-en-100"
exam_path = f"../data/exams/{exam_name}.jsonl"

# Step 3: Create the Experiment object (only once)
start_time = pd.Timestamp.now()
experiment = Experiment(model_name, agent_name, exam_name, attempt_id)
experiment.start(start_time)

# Set file paths
details_file_path = f"../data/details/{experiment.name}.csv"
dialogs_folder_path = f"../data/dialogs/{experiment.name}"
results_file_path = f"../data/results/results.csv"

# Create the components
model_factory = ModelFactory()
agent_factory = AgentFactory()
exam_reader = ExamReader()
dialog_writer = DialogWriter()
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

# Step 2: Identify rows with errors (missing or invalid agent answers)
error_rows = [
    row for row in details
    if not details_reader.has_agent_answer(details_file_path, row["problem_id"])
]

print("Printing error rows\n")

for row in error_rows:
    print(row["problem_id"])

# Step 4: Re-run the baseline agent for error rows
for row in error_rows:
    problem_id = row["problem_id"]
    problem = exam.problems[problem_id - 1]  # Problem IDs start from 1

    # Create the details row
    details_row = DetailsRow()
    episode_start_time = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
    details_row.create(problem_id, episode_start_time, experiment, problem)

    # Create the agent
    model = model_factory.create(model_name)
    agent = agent_factory.create(agent_name, model, problem.topic)

    # Create the dialog
    agent.create_dialog()

    # Set the problem
    agent.set_problem(problem)

    # Get the agent's answer
    answer_response = agent.get_answer()
    answer = agent.get_answer_choice(answer_response.text)

    # Log the agent's answer
    is_correct = answer == problem.answer
    score = 1 if is_correct else 0
    details_row.update_answer(answer_response, answer, score)

    # Save the dialog
    dialog_file_path = f"{dialogs_folder_path}/Problem {problem_id}.json"
    dialog_writer.write(dialog_file_path, agent.dialog)

    # Update the details list
    details[problem_id - 1] = details_row  # Update the specific row

# Step 5: Save the updated details to the CSV file
details_writer.write(details, details_file_path)

# Step 6: Calculate the results
experiment.end(datetime.now())  # End the experiment
details_table = pd.DataFrame(details)
pricing = get_pricing(model_name)
results = Result(experiment, details_table, pricing)

# Record the experiment results
experiments = ExperimentsFile()
experiments.load(results_file_path)
experiments.add_row(experiment, results)
experiments.save(results_file_path)

print("Re-attempt completed. Updated details saved to:", details_file_path)
print("Results calculated and saved to:", results_file_path)