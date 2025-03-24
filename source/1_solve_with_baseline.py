# Import packages
import os
import time
from datetime import datetime
import pandas as pd
from models.model_factory import ModelFactory
from agents.agent_factory import AgentFactory
from problems.exam_reader import ExamReader
from experiments.experiment import Experiment
from experiments.result import Result
from experiments.experiments_file import ExperimentsFile
from details.details_writer import DetailsWriter
from details.details_row import DetailsRow
from dialogs.dialog_writer import DialogWriter
from models.pricing import get_pricing

# Set the models
model_names = [
    "phi-4"
]

# Set the agent
agent_name = "baseline"

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
dialog_writer = DialogWriter()

# Loop through each model
for model_name in model_names:

    # Loop through each exam
    for exam_name in exam_names:

        # Set the experiment parameters
        start_time = pd.Timestamp.now()
        experiment = Experiment(model_name, agent_name, exam_name, attempt_id)
        experiment.start(start_time)

        # Set file and folder paths
        exam_path = f"../data/exams/{exam_name}.jsonl"
        dialogs_folder_path = f"../data/dialogs/{experiment.name}"
        details_file_path = f"../data/details/{experiment.name}.csv"
        results_file_path = f"../data/results/results.csv"
   
        # Create the folders
        os.makedirs(dialogs_folder_path, exist_ok=True)
        os.makedirs(os.path.dirname(details_file_path), exist_ok=True)
        os.makedirs(os.path.dirname(results_file_path), exist_ok=True)
        
        # Create the details table
        details = []

        # Load the exam
        exam = exam_reader.read(exam_path)

        # Loop through each exam problem
        for i, problem in enumerate(exam.problems):
            problem_id = i + 1
      
            # DEBUG: Answer only the first n problems
            if i >= 10:
                break
            
            
            # Create the details row
            details_row = DetailsRow()
            episode_start_time = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
            details_row.create(problem_id, episode_start_time, experiment, problem)

            # Create the agent
            model = model_factory.create(experiment.model_name)
            agent = agent_factory.create(experiment.agent_name, model, problem.topic)

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
            details.append(details_row)

        # End the experiment
        experiment.end(datetime.now())
        details_table = pd.DataFrame(details)
        pricing = get_pricing(experiment.model_name)
        results = Result(experiment, details_table, pricing)

        # Record the experiment details
        details_writer = DetailsWriter()
        details_writer.write(details, details_file_path)

        # Record the experiment results
        experiments = ExperimentsFile()
        experiments.load(results_file_path)
        experiments.add_row(experiment, results)
        experiments.save(results_file_path)