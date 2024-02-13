import tkinter as tk

from config import FONT


class InferenceFromFile(tk.Frame):
    def __init__(self, parent, root):
        super().__init__(parent, bg=root.colour_config["bg"])
        self.root = root

        self.create_widgets()
        self.pack_configure(padx=10, pady=10, fill=tk.BOTH, expand=True)

    def create_widgets(self):
        top_frame = tk.Frame(self, bg=self.root.colour_config["bg"])
        top_frame.pack(fill=tk.X)
        tk.Label(top_frame, text="File", font=(FONT, 16), bg=self.root.colour_config["bg"],
                 fg=self.root.colour_config["fg"]).pack()

        self.file_path_entry = tk.Entry(self, bg=self.root.colour_config["bg"], fg=self.root.colour_config["fg"],
                                        relief=tk.RIDGE, borderwidth=1)
        self.file_path_entry.pack_configure(pady=10, ipady=5, fill=tk.X)

        self.inference_button = tk.Button(self, text="Infer", command=self.infer, bg=self.root.colour_config["bg"],
                                          fg=self.root.colour_config["fg"], relief=tk.RIDGE, borderwidth=1)
        self.inference_button.pack_configure(pady=10, ipady=5, fill=tk.X)

    def infer(self):
        print("Infer from file")


class InferenceFromLive(tk.Frame):
    def __init__(self, parent, root):
        super().__init__(parent, bg=root.colour_config["bg"])
        self.root = root

        self.create_widgets()
        self.pack_configure(padx=10, pady=10, fill=tk.BOTH, expand=True)

    def create_widgets(self):
        top_frame = tk.Frame(self, bg=self.root.colour_config["bg"])
        top_frame.pack(fill=tk.X)
        tk.Label(top_frame, text="From Live Data", font=(FONT, 16), bg=self.root.colour_config["bg"],
                 fg=self.root.colour_config["fg"]).pack()

        self.inference_button = tk.Button(self, text="Infer", command=self.infer, bg=self.root.colour_config["bg"],
                                          fg=self.root.colour_config["fg"], relief=tk.RIDGE, borderwidth=1)
        self.inference_button.pack_configure(pady=10, ipady=5, fill=tk.X)

    def infer(self):
        print("Infer from live data")


class InferenceFrame(tk.Frame):
    def __init__(self, parent, root):
        super().__init__(parent, bg=root.colour_config["bg"])
        self.root = root

        self.create_widgets()
        self.pack_configure(padx=10, pady=10, fill=tk.BOTH, expand=True)

    def create_widgets(self):
        top_frame = tk.Frame(self, bg=self.root.colour_config["bg"])
        top_frame.pack(fill=tk.X)
        tk.Label(top_frame, text="Inference", font=(FONT, 20), bg=self.root.colour_config["bg"],
                 fg=self.root.colour_config["fg"]).pack()

        # Create two frames for the two columns
        left_frame = tk.Frame(self, name="testoo", bg=self.root.colour_config["bg"])
        right_frame = tk.Frame(self, bg=self.root.colour_config["bg"])

        # Left frame is inference from file, right frame is inference from live data
        self.inference_from_file = InferenceFromFile(left_frame, self.root)
        self.inference_from_file.pack(fill='both', expand=True)

        self.inference_from_live = InferenceFromLive(right_frame, self.root)
        self.inference_from_live.pack(fill='both', expand=True)

        # Pack the frames side by side
        left_frame.pack(side='left', fill='both', expand=True)
        right_frame.pack(side='right', fill='both', expand=True)
