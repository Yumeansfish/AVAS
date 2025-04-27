import os
import json
import tkinter as tk
from tkinter import messagebox



# Current script directory
CURRENT_DIR = os.path.dirname(__file__)
# Target directory: one level above the current script, then into data/surveys
SURVEY_DIR = os.path.join(CURRENT_DIR, "..", "data", "surveys")
os.makedirs(SURVEY_DIR, exist_ok=True)

# Survey file name
SURVEY_JSON_PATH = os.path.join(SURVEY_DIR, "questions.json")

class SurveyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Survey Builder")
        self.questions = []

        # Question container
        self.question_frames = []
        self.questions_container = tk.Frame(root)
        self.questions_container.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        # Button area
        self.add_question_btn = tk.Button(root, text="+ Add Question", command=self.add_question)
        self.add_question_btn.pack(pady=5)

        self.save_btn = tk.Button(root, text="Save", command=self.save_survey)
        self.save_btn.pack(pady=10)

        # Load existing survey
        self.load_existing_survey()

    def load_existing_survey(self):
        """Load existing survey JSON"""
        if os.path.exists(SURVEY_JSON_PATH):
            try:
                with open(SURVEY_JSON_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.questions = data.get("questions", [])
                    self.render_questions()
            except json.JSONDecodeError:
                messagebox.showerror("Error", "Survey file format is invalid. Please check the JSON structure manually.")

    def render_questions(self):
        """Clear the UI and re-render questions"""
        for frame in self.question_frames:
            frame.destroy()
        self.question_frames = []

        for q_data in self.questions:
            self.add_question(q_data["text"], q_data["options"], from_load=True)

    def add_question(self, text="New Question", options=None, from_load=False):
        """Add a new question"""
        if options is None:
            options = ["Option 1", "Option 2", "Option 3"]

        # Create a frame for the question
        question_frame = tk.Frame(self.questions_container, bd=2, relief=tk.GROOVE, padx=10, pady=5)
        # Ensure the new question always appears above the "+ Add Question" button
        children = self.questions_container.pack_slaves()
        if children:
            question_frame.pack(before=children[-1], fill=tk.X)
        else:
            question_frame.pack(side=tk.TOP, fill=tk.X)

        # Question number label
        question_number = len(self.question_frames) + 1
        question_label = tk.Label(question_frame, text=f"Question {question_number}", font=("Arial", 10, "bold"))
        question_label.pack(anchor="w")

        # Question entry
        question_entry = tk.Entry(question_frame, width=50)
        question_entry.insert(0, text)
        question_entry.pack(pady=2)

        # Container for answers
        answers_container = tk.Frame(question_frame)
        answers_container.pack(fill=tk.X, padx=10, pady=5)

        # List to store answer entry widgets (mainly for initial state)
        answer_entries = []

        # Update answer numbering
        def update_answer_numbers():
            for idx, answer_frame in enumerate(answers_container.winfo_children()):
                # Each answer's first widget is the label
                answer_label = answer_frame.winfo_children()[0]
                answer_label.config(text=f"Answer {idx+1}:")

        # Delete a specific answer
        def delete_answer(answer_frame):
            answer_frame.destroy()
            update_answer_numbers()

        # Add a new answer entry
        def add_answer_entry(answer_text=""):
            answer_frame = tk.Frame(answers_container)
            answer_frame.pack(fill=tk.X, pady=1)
            # Answer number label
            answer_label = tk.Label(answer_frame, text=f"Answer {len(answers_container.winfo_children())+1}:", width=10, anchor="w")
            answer_label.pack(side=tk.LEFT)
            # Answer entry
            answer_entry = tk.Entry(answer_frame, width=40)
            answer_entry.insert(0, answer_text)
            answer_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            # Delete answer button on the right
            delete_answer_btn = tk.Button(answer_frame, text="Delete", command=lambda: delete_answer(answer_frame))
            delete_answer_btn.pack(side=tk.RIGHT, padx=5)
            answer_entries.append(answer_entry)
            update_answer_numbers()

        # Initialize default answers
        for option in options:
            add_answer_entry(option)

        # "+ Add Answer" button
        add_answer_btn = tk.Button(question_frame, text="+ Add Answer", command=lambda: add_answer_entry())
        add_answer_btn.pack(pady=2)

        # Delete question button
        def delete_question():
            question_frame.destroy()
            if question_frame in self.question_frames:
                self.question_frames.remove(question_frame)
            self.update_question_numbers()

        delete_question_btn = tk.Button(question_frame, text="Delete", fg="red", command=delete_question)
        delete_question_btn.pack(pady=2)

        # Add the new question to the list
        self.question_frames.append(question_frame)
        if not from_load:
            self.questions.append({"text": text, "options": options})

        self.update_question_numbers()

    def update_question_numbers(self):
        """Update the numbering for all questions"""
        for idx, frame in enumerate(self.question_frames):
            # The first child is the question number label
            frame.winfo_children()[0].config(text=f"Question {idx+1}")

    def save_survey(self):
        """Save the survey to JSON"""
        self.questions = []
        for frame in self.question_frames:
            children = frame.winfo_children()
            # children[0]: question number label
            # children[1]: question entry
            # children[2]: answers container
            # children[3]: + Add Answer button
            # children[4]: Delete button
            question_text = children[1].get()
            answers_container = children[2]
            options = []
            for answer_frame in answers_container.winfo_children():
                # In each answer frame: [0] is the label, [1] is the entry, [2] is the delete button
                entry = answer_frame.winfo_children()[1]
                options.append(entry.get())
            self.questions.append({"text": question_text, "options": options})

        survey_data = {"questions": self.questions}
        with open(SURVEY_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(survey_data, f, indent=4, ensure_ascii=False)
        messagebox.showinfo("Success", f"Survey saved to {SURVEY_JSON_PATH}")

if __name__ == "__main__":
    root = tk.Tk()
    app = SurveyApp(root)
    root.mainloop()











