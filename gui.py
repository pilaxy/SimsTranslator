import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import sys
import io
from threading import Thread, Event
from translator import XmlTranslator  # Assuming XmlTranslator class is in xml_translator.py

class XmlTranslatorGUI:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("XML Translator")
        self.root.geometry("600x700")

        self.files = []
        self.source_lang = ctk.StringVar(value="en")
        self.target_lang = ctk.StringVar(value="de")
        self.char_limit = ctk.IntVar(value=5000)

        self.processing = False
        self.stop_event = Event()
        self.stdout_redirect = None

        self.create_widgets()

    def create_widgets(self):
        # File selection
        file_frame = ctk.CTkFrame(self.root)
        file_frame.pack(padx=20, pady=20, fill="x")

        ctk.CTkLabel(file_frame, text="XML Files:").pack(anchor="w")
        self.file_listbox = ctk.CTkTextbox(file_frame, height=100)
        self.file_listbox.pack(fill="x", expand=True)

        file_button_frame = ctk.CTkFrame(file_frame)
        file_button_frame.pack(fill="x", pady=(10, 0))

        ctk.CTkButton(file_button_frame, text="Add Files", command=self.add_files).pack(side="left", padx=(0, 10))
        ctk.CTkButton(file_button_frame, text="Clear Files", command=self.clear_files).pack(side="left")

        # Language selection
        lang_frame = ctk.CTkFrame(self.root)
        lang_frame.pack(padx=20, pady=20, fill="x")

        ctk.CTkLabel(lang_frame, text="Source Language:").pack(side="left")
        ctk.CTkEntry(lang_frame, textvariable=self.source_lang, width=50).pack(side="left", padx=(0, 20))

        ctk.CTkLabel(lang_frame, text="Target Language:").pack(side="left")
        ctk.CTkEntry(lang_frame, textvariable=self.target_lang, width=50).pack(side="left")

        # Character limit
        char_limit_frame = ctk.CTkFrame(self.root)
        char_limit_frame.pack(padx=20, pady=20, fill="x")

        ctk.CTkLabel(char_limit_frame, text="Characters per Batch:").pack(side="left")
        ctk.CTkEntry(char_limit_frame, textvariable=self.char_limit, width=100).pack(side="left")

        # Process/Stop button
        self.process_button = ctk.CTkButton(self.root, text="Process Files", command=self.toggle_processing)
        self.process_button.pack(pady=20)

        # Log box
        log_frame = ctk.CTkFrame(self.root)
        log_frame.pack(padx=20, pady=20, fill="both", expand=True)

        ctk.CTkLabel(log_frame, text="Log:").pack(anchor="w")
        self.log_box = ctk.CTkTextbox(log_frame, height=200)
        self.log_box.pack(fill="both", expand=True)

    def add_files(self):
        new_files = filedialog.askopenfilenames(filetypes=[("XML files", "*.xml")])
        self.files.extend(new_files)
        self.update_file_listbox()

    def clear_files(self):
        self.files.clear()
        self.update_file_listbox()

    def update_file_listbox(self):
        self.file_listbox.delete("1.0", "end")
        for file in self.files:
            self.file_listbox.insert("end", f"{file}\n")

    def toggle_processing(self):
        if not self.processing:
            self.start_processing()
        else:
            self.stop_processing()

    def start_processing(self):
        if not self.files:
            messagebox.showwarning("No Files", "Please add XML files to process.")
            return

        self.processing = True
        self.stop_event.clear()
        self.process_button.configure(text="Stop", fg_color="red", hover_color="dark red")

        # Clear the log box
        self.log_box.delete("1.0", "end")

        # Redirect stdout to the log box
        self.redirect_stdout()

        # Start processing in a separate thread
        Thread(target=self._process_files, daemon=True).start()

    def stop_processing(self):
        self.stop_event.set()
        self.processing = False
        self.process_button.configure(text="Process Files", fg_color=["#3a7ebf", "#1f538d"], hover_color=["#325882", "#14375e"])
        print("\nProcessing stopped by user.")

    def _process_files(self):
        translator = XmlTranslator(
            source_language=self.source_lang.get(),
            target_language=self.target_lang.get(),
            char_limit_per_batch=self.char_limit.get()
        )

        for input_file in self.files:
            if self.stop_event.is_set():
                break

            output_file = f"{os.path.splitext(input_file)[0]}_{self.target_lang.get()}.xml"
            translator.parse_and_translate_xml(input_file, output_file)

        self.root.after(0, self.finish_processing)

    def finish_processing(self):
        self.processing = False
        self.process_button.configure(text="Process Files", fg_color=["#3a7ebf", "#1f538d"], hover_color=["#325882", "#14375e"])

        if self.stop_event.is_set():
            status_message = "\nFile processing was stopped by the user."
        else:
            status_message = "\nAll files have been processed successfully."

        print(status_message)
        self.restore_stdout()

        messagebox.showinfo("Processing Status", status_message)

    def redirect_stdout(self):
        self.stdout_redirect = io.StringIO()
        self.old_stdout = sys.stdout
        sys.stdout = self.stdout_redirect

        def update_log():
            if self.stdout_redirect:
                output = self.stdout_redirect.getvalue()
                if output:
                    self.log_box.insert("end", output)
                    self.log_box.see("end")
                    self.stdout_redirect.truncate(0)
                    self.stdout_redirect.seek(0)
            if self.processing:
                self.root.after(100, update_log)

        self.root.after(100, update_log)

    def restore_stdout(self):
        sys.stdout = self.old_stdout

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = XmlTranslatorGUI()
    app.run()
