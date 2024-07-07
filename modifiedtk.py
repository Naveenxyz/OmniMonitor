import random
import pyautogui
import os
import shutil
from datetime import datetime, timedelta
import time
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import multiprocessing
import signal
import json
import sqlite3

from llm import get_llm_out, check_if_show_popup

def get_latest_history():
    conn = sqlite3.connect('tasks.db')  # Replace with your actual database name
    cursor = conn.cursor()
    
    # Assuming your table is named 'tasks' and has columns 'id', 'task', 'priority'
    cursor.execute("SELECT * FROM history ORDER BY timestamp DESC LIMIT 1")
    result = cursor.fetchone()
    
    conn.close()
    
    if result:
        return result  # Return the task description
    else:
        return "No priority task found"

class ScreenshotApp:
    def __init__(self, run_duration_minutes=5):
        self.save_directory = os.path.join(os.getcwd(), "images")
        self.interval = 10  # Time between screenshots in seconds
        self.max_screenshots = 10  # Maximum number of screenshots to keep
        self.screenshots = []
        self.is_running = multiprocessing.Value('b', True)
        self.queue = multiprocessing.Queue()
        self.run_duration = timedelta(minutes=run_duration_minutes)
        self.start_time = datetime.now()

        # Delete all files in the directory at start
        self.clear_directory()

        # Ensure the directory exists
        os.makedirs(self.save_directory, exist_ok=True)

    def clear_directory(self):
        if os.path.exists(self.save_directory):
            for filename in os.listdir(self.save_directory):
                file_path = os.path.join(self.save_directory, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print(f'Failed to delete {file_path}. Reason: {e}')

    def start(self):
        # Start the screenshot process
        self.process = multiprocessing.Process(target=self.take_screenshots)
        self.process.start()

        # Start checking for popups in the main thread
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the main window
        self.root.after(10 * 1000, self.check_for_popup)
        self.root.after(100, self.check_time_limit)
        self.root.mainloop()

    def take_screenshots(self):
        while self.is_running.value:
            screenshot = self.take_screenshot()
            if self.check_condition(screenshot):
                self.queue.put(screenshot)
            time.sleep(self.interval)

    def take_screenshot(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"
        filepath = os.path.join(self.save_directory, filename)

        screenshot = pyautogui.screenshot()
        screenshot.save(filepath)
        print(f"Screenshot saved as {filepath}")
        get_llm_out(f"images/{filename}")

        self.screenshots.append(filepath)

        if len(self.screenshots) > self.max_screenshots:
            oldest_file = self.screenshots.pop(0)
            if os.path.exists(oldest_file):
                os.remove(oldest_file)
                print(f"Deleted old screenshot: {oldest_file}")

        return screenshot

    def check_condition(self, screenshot):
        # Implement your condition here
        # For example, check if the screenshot contains a specific color or pattern
        # Return True if the condition is met, False otherwise
        return True  # Placeholder: always show popup

    def check_for_popup(self):
        try:
            screenshot = self.queue.get_nowait()
            self.show_popup("memes")
        except multiprocessing.queues.Empty:
            pass
        finally:
            # Schedule the next check
            self.root.after(1000, self.check_for_popup)
    # def show_popup(self, relative_directory):
    #     metadata = json.loads(get_latest_history()[3])
    #     if not check_if_show_popup():
    #         print("Not showing popup as it is not necessary to show")
    #         return

    # # Get the absolute path of the directory
    #     current_dir = os.path.dirname(os.path.abspath(__file__))
    #     directory = os.path.join(current_dir, relative_directory)

    # # Check if directory exists
    #     if not os.path.isdir(directory):
    #         print(f"Directory not found: {directory}")
    #         return

    # # Get list of image files in the directory
    #     image_files = [f for f in os.listdir(directory) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]
    
    #     if not image_files:
    #         print(f"No image files found in the directory: {directory}")
    #         return

    # # Select a random image file
    #     random_image = random.choice(image_files)
    #     image_path = os.path.join(directory, random_image)

    # # Open the image
    #     try:
    #         original_image = Image.open(image_path)
    #     except IOError:
    #         print(f"Error opening image: {image_path}")
    #         return

    #     popup = tk.Toplevel(self.root)
    #     popup.title("Image Alert")
    #     popup.geometry("400x600")  # Adjusted size
    #     popup.overrideredirect(True)  # Remove window decorations

    # # Calculate dimensions for resizing
    #     max_width, max_height = 380, 380  # Maximum dimensions for the image
    #     original_width, original_height = original_image.size
    #     aspect_ratio = original_width / original_height

    #     if original_width > original_height:
    #         new_width = min(original_width, max_width)
    #         new_height = int(new_width / aspect_ratio)
    #     else:
    #         new_height = min(original_height, max_height)
    #         new_width = int(new_height * aspect_ratio)

    # # Resize the image
    #     resized_image = original_image.resize((new_width, new_height), Image.LANCZOS)

    # # Convert PIL Image to PhotoImage
    #     photo = ImageTk.PhotoImage(resized_image)

    # # Create image label
    #     image_label = ttk.Label(popup, image=photo)
    #     image_label.image = photo  # Keep a reference
    #     image_label.pack(pady=5)

    # # Display metadata information
    #     whats_on_the_screen = metadata.get('metadata', {}).get('whats_on_the_screen', 'N/A')
    #     text_to_show = metadata.get('metadata', {}).get('text', 'Please enter the validation text below to dismiss:')

    #     screen_label = ttk.Label(popup, text=f"What's on the screen: {whats_on_the_screen}")
    #     screen_label.pack(pady=5)

    #     text_label = ttk.Label(popup, text=text_to_show)
    #     text_label.pack(pady=5)

    # # Add validation text input
    #     validation_text = "12345"  # The validation text to be matched
    #     input_var = tk.StringVar()

    #     def validate_input(*args):
    #         if input_var.get() == validation_text:
    #             dismiss_button.config(state=tk.NORMAL)
    #         else:
    #             dismiss_button.config(state=tk.DISABLED)

    #     input_var.trace_add('write', validate_input)
    #     validation_entry = ttk.Entry(popup, textvariable=input_var)
    #     validation_entry.pack(pady=5)

    # # Add dismiss button
    #     dismiss_button = ttk.Button(popup, text="Dismiss", command=popup.destroy, state=tk.DISABLED)
    #     dismiss_button.pack(pady=10)

    # # Center the popup on the screen
    #     popup.update_idletasks()
    #     width = popup.winfo_width()
    #     height = popup.winfo_height()
    #     x = (popup.winfo_screenwidth() // 2) - (width // 2)
    #     y = (popup.winfo_screenheight() // 2) - (height // 2)
    #     popup.geometry('{}x{}+{}+{}'.format(width, height, x, y))

    #     print(f"Popup created with random image: {random_image}")
    def show_popup(self, relative_directory):
        if not check_if_show_popup():
            print("Not showing popup as it is not necessary to show")
            return
        metadata = json.loads(get_latest_history()[3])
        print("metadata", metadata)

        # Get the absolute path of the directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        directory = os.path.join(current_dir, relative_directory)

        # Check if directory exists
        if not os.path.isdir(directory):
            print(f"Directory not found: {directory}")
            return

        # Get list of image files in the directory
        image_files = [f for f in os.listdir(directory) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]
        
        if not image_files:
            print(f"No image files found in the directory: {directory}")
            return

        # Select a random image file
        random_image = random.choice(image_files)
        image_path = os.path.join(directory, random_image)

        try:
            original_image = Image.open(image_path)
        except IOError:
            print(f"Error opening image: {image_path}")
            return

        popup = tk.Toplevel(self.root)
        popup.title("Random Image Alert")
        popup.geometry("400x450")  # Increased height for additional widgets
        # popup.overrideredirect(True)
        popup.lift()
        popup.attributes('-topmost', True)

        # Calculate dimensions for resizing
        max_width, max_height = 380, 380
        original_width, original_height = original_image.size
        aspect_ratio = original_width / original_height

        if original_width > original_height:
            new_width = min(original_width, max_width)
            new_height = int(new_width / aspect_ratio)
        else:
            new_height = min(original_height, max_height)
            new_width = int(new_height * aspect_ratio)

        resized_image = original_image.resize((new_width, new_height), Image.LANCZOS)
        photo = ImageTk.PhotoImage(resized_image)

        image_label = tk.Label(popup, image=photo)
        image_label.image = photo
        image_label.pack(pady=5)

        text_below_image = tk.Label(popup, text=metadata["text"], wraplength=380)
        text_below_image.pack(pady=5)

        validation_text = metadata["typing_text"]
        validation_label = tk.Label(popup, text=f"Please enter this text to dismiss: {validation_text}", wraplength=380)
        validation_label.pack(pady=5)

        input_var = tk.StringVar()
        validation_entry = tk.Entry(popup, textvariable=input_var)
        validation_entry.pack(pady=5)

        message_label = tk.Label(popup, text="")
        message_label.pack(pady=5)

        def check_input():
            if input_var.get() == validation_text:
                message_label.config(text="Correct! You can now dismiss the popup.")
                popup.destroy()
                dismiss_button.config(state=tk.NORMAL)
            else:
                message_label.config(text="Incorrect. Please try again.")
                dismiss_button.config(state=tk.DISABLED)

        check_button = tk.Button(popup, text="Dismiss", command=check_input)
        check_button.pack(pady=5)

        dismiss_button = tk.Button(popup, text="Dismiss", command=popup.destroy, state=tk.DISABLED)
        # dismiss_button.pack(pady=5)

        # Center the popup on the screen
        popup.update_idletasks()
        width = popup.winfo_width()
        height = popup.winfo_height()
        x = (popup.winfo_screenwidth() // 2) - (width // 2)
        y = (popup.winfo_screenheight() // 2) - (height // 2)
        popup.geometry('{}x{}+{}+{}'.format(width, height, x, y))

        print(f"Popup created with random image: {random_image}")

        validation_entry.focus_set()
        popup.wait_window(popup)
    


    def crop_center(self, pil_img, crop_width, crop_height):
        img_width, img_height = pil_img.size
        return pil_img.crop(((img_width - crop_width) // 2,
                             (img_height - crop_height) // 2,
                             (img_width + crop_width) // 2,
                             (img_height + crop_height) // 2))

    def check_time_limit(self):
        if datetime.now() - self.start_time > self.run_duration:
            print("Time limit reached. Stopping the application.")
            self.stop()
        else:
            self.root.after(30*1000, self.check_time_limit)  # Check every second

    def stop(self):
        print("Stopping the application...")
        self.is_running.value = False
        if self.process.is_alive():
            self.process.terminate()
            self.process.join()
        self.root.quit()
        self.root.destroy()

def signal_handler(signum, frame):
    print("Interrupt received, stopping the application...")
    if 'app' in globals():
        app.stop()

def main():
    global app
    signal.signal(signal.SIGINT, signal_handler)
    app = ScreenshotApp(run_duration_minutes=2)  # Run for 5 minutes
    app.start()

if __name__ == "__main__":
    main()