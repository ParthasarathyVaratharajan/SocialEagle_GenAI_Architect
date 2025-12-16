import pyautogui
import sys

def save_arguments_to_file(filepath, *args):
    """
    Save command line arguments to a text file.
    Overwrites if file exists, creates new file otherwise.
    """
    try:
        # Open file in write mode (creates new or overwrites existing)
        with open(filepath, 'w') as file:
            # Write each argument on a new line
            for arg in args:
                file.write(str(arg) + '\n')
        
        print(f"Arguments successfully saved to {filepath}")
        return True
    
    except Exception as e:
        print(f"Error writing to file: {e}")
        return False

# Main execution
if __name__ == "__main__":
    # Define the file path
    file_path = r"c:\Sarathy\n8nflask.txt"
    
    # Get command line arguments (excluding script name)
    arguments = sys.argv[1:]
    
    # If no arguments provided, you can use pyautogui to get input
    if not arguments:
        print("No command line arguments provided.")
        user_input = pyautogui.prompt("Enter text to save:")
        if user_input:
            arguments = [user_input]
    
    # Save arguments to file
    if arguments:
        save_arguments_to_file(file_path, *arguments)
    else:
        print("No data to save.")