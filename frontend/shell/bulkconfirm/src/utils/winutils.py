import os
import clipboard
import ctypes

def startfile(file_path):
    # Use the Windows API to start the file
    os.startfile(file_path)

def show_message_box(title, message):
    # Define the MessageBox function parameters
    MessageBox = ctypes.windll.user32.MessageBoxW
    MB_OK = 0x0
    # Call the MessageBox function
    result = MessageBox(None, message, title, MB_OK)
    return result

def copy_to_clipboard(text):
    # Copy the text to the clipboard
    clipboard.copy(text)