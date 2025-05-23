import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import speech_recognition as sr
import os
from pathlib import Path
import time
import socket


class SpeechRecognitionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Speech Recognition Tool")
        self.root.geometry("600x500")

        # Initialize recognizer
        self.r = sr.Recognizer()

        # Audio files directory
        self.audio_dir = "audio_files/"
        Path(self.audio_dir).mkdir(exist_ok=True)

        # UI Elements
        self.create_widgets()

    def create_widgets(self):
        # Notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # File Processing Tab
        self.file_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.file_tab, text="Process Audio Files")

        # Microphone Tab
        self.mic_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.mic_tab, text="Microphone Input")

        # Output Console
        self.console = tk.Text(self.root, height=10, state=tk.DISABLED)
        self.console.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # File Processing Tab Content
        self.setup_file_tab()

        # Microphone Tab Content
        self.setup_mic_tab()

    def setup_file_tab(self):
        # File selection
        file_frame = ttk.LabelFrame(self.file_tab, text="Audio Files")
        file_frame.pack(fill=tk.X, padx=5, pady=5)

        self.file_listbox = tk.Listbox(file_frame, height=5, selectmode=tk.MULTIPLE)
        self.file_listbox.pack(fill=tk.X, padx=5, pady=5)

        btn_frame = ttk.Frame(file_frame)
        btn_frame.pack(fill=tk.X, pady=5)

        ttk.Button(btn_frame, text="Add Files", command=self.add_files).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(btn_frame, text="Remove Selected", command=self.remove_files).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(btn_frame, text="Clear All", command=self.clear_files).pack(
            side=tk.LEFT, padx=2
        )

        # Processing options
        options_frame = ttk.LabelFrame(self.file_tab, text="Processing Options")
        options_frame.pack(fill=tk.X, padx=5, pady=5)

        self.offline_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame,
            text="Offline Recognition (Sphinx)",
            variable=self.offline_var,
        ).pack(anchor=tk.W)

        self.online_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame, text="Online Recognition (Google)", variable=self.online_var
        ).pack(anchor=tk.W)

        # Process button
        ttk.Button(
            self.file_tab, text="Process Files", command=self.process_files
        ).pack(pady=10)

    def setup_mic_tab(self):
        # Microphone settings
        settings_frame = ttk.LabelFrame(self.mic_tab, text="Microphone Settings")
        settings_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(settings_frame, text="Timeout (seconds):").pack(anchor=tk.W)
        self.timeout_var = tk.IntVar(value=10)
        ttk.Entry(settings_frame, textvariable=self.timeout_var).pack(
            fill=tk.X, padx=5, pady=2
        )

        ttk.Label(settings_frame, text="Phrase Limit (seconds):").pack(anchor=tk.W)
        self.phrase_var = tk.IntVar(value=15)
        ttk.Entry(settings_frame, textvariable=self.phrase_var).pack(
            fill=tk.X, padx=5, pady=2
        )

        # Recognition options
        options_frame = ttk.LabelFrame(self.mic_tab, text="Recognition Options")
        options_frame.pack(fill=tk.X, padx=5, pady=5)

        self.mic_offline_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame,
            text="Offline Recognition (Sphinx)",
            variable=self.mic_offline_var,
        ).pack(anchor=tk.W)

        self.mic_online_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame,
            text="Online Recognition (Google)",
            variable=self.mic_online_var,
        ).pack(anchor=tk.W)

        # Record button
        ttk.Button(
            self.mic_tab, text="Start Recording", command=self.start_recording
        ).pack(pady=10)

    def add_files(self):
        files = filedialog.askopenfilenames(
            title="Select Audio Files",
            filetypes=(("WAV files", "*.wav"), ("All files", "*.*")),
        )
        for file in files:
            self.file_listbox.insert(tk.END, file)

    def remove_files(self):
        selected = self.file_listbox.curselection()
        for i in reversed(selected):
            self.file_listbox.delete(i)

    def clear_files(self):
        self.file_listbox.delete(0, tk.END)

    def process_files(self):
        files = self.file_listbox.get(0, tk.END)
        if not files:
            messagebox.showwarning("No Files", "Please add audio files to process")
            return

        self.log_message("\nProcessing audio files...")

        socket.setdefaulttimeout(30)  # 30 seconds timeout

        for file_path in files:
            if not os.path.isfile(file_path):
                self.log_message(f"Warning: File not found - {file_path}")
                continue

            self.log_message(f"\nProcessing: {os.path.basename(file_path)}")

            try:
                with sr.AudioFile(file_path) as source:
                    audio_text = self.r.listen(source)

                    # Offline recognition
                    if self.offline_var.get():
                        try:
                            self.log_message(
                                "Attempting offline recognition with Sphinx..."
                            )
                            text = self.r.recognize_sphinx(audio_text)
                            self.log_message("Sphinx result:")
                            self.log_message(text)
                        except Exception as e:
                            self.log_message(f"Offline recognition failed: {e}")

                    # Online recognition
                    if self.online_var.get():
                        max_retries = 3
                        for attempt in range(max_retries):
                            try:
                                self.log_message(
                                    f"Attempt {attempt+1}/{max_retries} with Google..."
                                )
                                text = self.r.recognize_google(
                                    audio_text, language="en-US"
                                )
                                self.log_message("Google recognition result:")
                                self.log_message(text)
                                break
                            except sr.RequestError as e:
                                self.log_message(
                                    f"Network error on attempt {attempt+1}: {e}"
                                )
                                if attempt < max_retries - 1:
                                    wait_time = 2**attempt
                                    self.log_message(
                                        f"Retrying in {wait_time} seconds..."
                                    )
                                    time.sleep(wait_time)
                                else:
                                    self.log_message("All retries failed.")
                            except sr.UnknownValueError:
                                self.log_message(
                                    "Google could not understand the audio"
                                )
                                break
                            except Exception as e:
                                self.log_message(f"Error during recognition: {e}")
                                if attempt < max_retries - 1:
                                    self.log_message("Retrying...")
                                    time.sleep(1)
                                else:
                                    self.log_message("All retries failed.")
            except Exception as e:
                self.log_message(f"Error processing file: {e}")

        self.log_message("\nProcessing complete.")

    def start_recording(self):
        self.log_message("\nStarting microphone recording...")

        timeout = self.timeout_var.get()
        phrase_limit = self.phrase_var.get()

        try:
            with sr.Microphone() as source:
                self.log_message("Adjusting for ambient noise...")
                self.r.adjust_for_ambient_noise(source, duration=1)
                self.r.pause_threshold = 1

                self.log_message(
                    f"Speak now (timeout: {timeout}s, limit: {phrase_limit}s)..."
                )
                try:
                    audio = self.r.listen(
                        source, timeout=timeout, phrase_time_limit=phrase_limit
                    )
                    self.log_message("Processing your speech...")

                    # Offline recognition
                    if self.mic_offline_var.get():
                        try:
                            self.log_message(
                                "Attempting offline recognition with Sphinx..."
                            )
                            text = self.r.recognize_sphinx(audio)
                            self.log_message("Sphinx thinks you said:")
                            self.log_message(text)
                        except ImportError:
                            self.log_message(
                                "PocketSphinx not installed. Install with: pip install pocketsphinx"
                            )
                        except Exception as e:
                            self.log_message(f"Offline recognition failed: {e}")

                    # Online recognition
                    if self.mic_online_var.get():
                        max_retries = 3
                        for attempt in range(max_retries):
                            try:
                                self.log_message(
                                    f"Attempt {attempt+1}/{max_retries} with Google..."
                                )
                                text = self.r.recognize_google(audio)
                                self.log_message("Google thinks you said:")
                                self.log_message(text)
                                break
                            except sr.RequestError as e:
                                self.log_message(
                                    f"Network error on attempt {attempt+1}: {e}"
                                )
                                if attempt < max_retries - 1:
                                    wait_time = 2**attempt
                                    self.log_message(
                                        f"Retrying in {wait_time} seconds..."
                                    )
                                    time.sleep(wait_time)
                                else:
                                    self.log_message("All retries failed.")
                            except sr.UnknownValueError:
                                self.log_message("Could not understand audio")
                                break
                            except Exception as e:
                                self.log_message(f"Error during recognition: {e}")
                                if attempt < max_retries - 1:
                                    self.log_message("Retrying...")
                                    time.sleep(1)
                                else:
                                    self.log_message("All retries failed.")
                except sr.WaitTimeoutError:
                    self.log_message("No speech detected within timeout period")
                except Exception as e:
                    self.log_message(f"Error while listening: {e}")
        except Exception as e:
            self.log_message(f"Error initializing microphone: {e}")
            self.log_message("Check microphone connection and permissions")

    def log_message(self, message):
        self.console.config(state=tk.NORMAL)
        self.console.insert(tk.END, message + "\n")
        self.console.config(state=tk.DISABLED)
        self.console.see(tk.END)
        self.root.update()


if __name__ == "__main__":
    root = tk.Tk()
    app = SpeechRecognitionApp(root)
    root.mainloop()
