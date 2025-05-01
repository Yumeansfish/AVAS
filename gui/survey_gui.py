import os
import json
import tkinter as tk
from tkinter import messagebox

from core.config import SURVEY_JSON_PATH
os.makedirs(os.path.dirname(SURVEY_JSON_PATH), exist_ok=True)

class SurveyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Survey Builder")
        self.questions = []

        # Container for question frames
        self.question_frames = []
        self.questions_container = tk.Frame(root)
        self.questions_container.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        # Button to add a new question
        self.add_question_btn = tk.Button(root, text="Add Question", command=self.add_question)
        self.add_question_btn.pack(pady=5)

        # Button to save the survey
        self.save_btn = tk.Button(root, text="Save Survey", command=self.save_survey)
        self.save_btn.pack(pady=10)

        # Load any existing survey data
        self.load_existing_survey()

    def load_existing_survey(self):
        """Load survey data from JSON if it exists."""
        if os.path.exists(SURVEY_JSON_PATH):
            try:
                with open(SURVEY_JSON_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.questions = data.get("questions", [])
                    self.render_questions()
            except json.JSONDecodeError:
                messagebox.showerror("Error", "The survey file is not a valid JSON.")

    def render_questions(self):
        """Clear current UI and render questions from loaded data."""
        for frame in self.question_frames:
            frame.destroy()
        self.question_frames = []

        for q in self.questions:
            self.add_question(q["text"], q["options"], from_load=True)

    def add_question(self, text="New Question", options=None, from_load=False):
        """Add a question frame to the UI."""
        if options is None:
            options = ["Option 1", "Option 2", "Option 3"]

        frame = tk.Frame(self.questions_container, bd=2, relief=tk.GROOVE, padx=10, pady=5)
        children = self.questions_container.pack_slaves()
        if children:
            frame.pack(before=children[-1], fill=tk.X)
        else:
            frame.pack(side=tk.TOP, fill=tk.X)

        label = tk.Label(frame, text=f"Question {len(self.question_frames)+1}", font=("Arial", 10, "bold"))
        label.pack(anchor="w")

        entry = tk.Entry(frame, width=50)
        entry.insert(0, text)
        entry.pack(pady=2)

        answers_container = tk.Frame(frame)
        answers_container.pack(fill=tk.X, padx=10, pady=5)

        answer_entries = []

        def update_answer_labels():
            for idx, ans_frame in enumerate(answers_container.winfo_children()):
                ans_label = ans_frame.winfo_children()[0]
                ans_label.config(text=f"Answer {idx+1}:")

        def delete_answer(ans_frame):
            ans_frame.destroy()
            update_answer_labels()

        def add_answer(answer_text=""):
            ans_frame = tk.Frame(answers_container)
            ans_frame.pack(fill=tk.X, pady=1)

            ans_label = tk.Label(ans_frame, text=f"Answer {len(answers_container.winfo_children())+1}:", width=10, anchor="w")
            ans_label.pack(side=tk.LEFT)

            ans_entry = tk.Entry(ans_frame, width=40)
            ans_entry.insert(0, answer_text)
            ans_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

            delete_btn = tk.Button(ans_frame, text="Remove", command=lambda: delete_answer(ans_frame))
            delete_btn.pack(side=tk.RIGHT, padx=5)

            answer_entries.append(ans_entry)
            update_answer_labels()

        for opt in options:
            add_answer(opt)

        add_ans_btn = tk.Button(frame, text="Add Answer", command=lambda: add_answer())
        add_ans_btn.pack(pady=2)

        def delete_question():
            frame.destroy()
            self.question_frames.remove(frame)
            self.update_question_labels()

        delete_q_btn = tk.Button(frame, text="Delete Question", fg="red", command=delete_question)
        delete_q_btn.pack(pady=2)

        self.question_frames.append(frame)
        if not from_load:
            self.questions.append({"text": text, "options": options})

        self.update_question_labels()

    def update_question_labels(self):
        """Update question numbering labels."""
        for idx, frame in enumerate(self.question_frames):
            frame.winfo_children()[0].config(text=f"Question {idx+1}")

    def save_survey(self):
        """Collect all questions and answers, and write to JSON."""
        self.questions = []
        for frame in self.question_frames:
            children = frame.winfo_children()
            question_text = children[1].get()
            answers_container = children[2]
            opts = []
            for ans_frame in answers_container.winfo_children():
                ans_entry = ans_frame.winfo_children()[1]
                opts.append(ans_entry.get())
            self.questions.append({"text": question_text, "options": opts})

        data = {"questions": self.questions}
        with open(SURVEY_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        messagebox.showinfo("Success", f"Survey saved to {SURVEY_JSON_PATH}")

if __name__ == "__main__":
    root = tk.Tk()
    app = SurveyApp(root)
    root.mainloop()












