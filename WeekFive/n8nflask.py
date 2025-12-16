from flask import Flask, request, jsonify
import os

app = Flask(__name__)

def save_arguments_to_file(filepath, *args):
    """
    Save arguments to a text file.
    Overwrites if file exists, creates new file otherwise.
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Open file in write mode (creates new or overwrites existing)
        with open(filepath, 'w') as file:
            # Write each argument on a new line
            for arg in args:
                file.write(str(arg) + '\n')
        
        return True, f"Arguments successfully saved to {filepath}"
    
    except Exception as e:
        return False, f"Error writing to file: {e}"

@app.route('/')
def home():
    return """
    <h1>N8N Flask File Writer</h1>
    <p>Send POST request to /save with JSON data</p>
    <p>Example: {"data": ["arg1", "arg2", "arg3"]}</p>
    <p>Or use GET: /save?data=arg1&data=arg2</p>
    """

@app.route('/save', methods=['POST', 'GET'])
def save_data():
    """
    Endpoint to save data to file
    Accepts JSON POST or GET with query parameters
    """
    file_path = r"c:\Sarathy\n8nflask.txt"
    
    try:
        if request.method == 'POST':
            # Handle JSON data
            data = request.get_json()
            
            if not data:
                return jsonify({
                    "success": False,
                    "message": "No JSON data provided"
                }), 400
            
            # Extract arguments from different possible formats
            if 'data' in data:
                if isinstance(data['data'], list):
                    arguments = data['data']
                else:
                    arguments = [data['data']]
            elif 'arguments' in data:
                arguments = data['arguments'] if isinstance(data['arguments'], list) else [data['arguments']]
            elif 'text' in data:
                arguments = [data['text']]
            else:
                # Use all key-value pairs
                arguments = [f"{k}: {v}" for k, v in data.items()]
        
        else:  # GET request
            # Get data from query parameters
            arguments = request.args.getlist('data')
            
            if not arguments:
                # Try single 'text' parameter
                text = request.args.get('text')
                if text:
                    arguments = [text]
        
        if not arguments:
            return jsonify({
                "success": False,
                "message": "No data provided. Send 'data' in JSON or query parameters."
            }), 400
        
        # Save to file
        success, message = save_arguments_to_file(file_path, *arguments)
        
        return jsonify({
            "success": success,
            "message": message,
            "saved_data": arguments,
            "file_path": file_path
        }), 200 if success else 500
    
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error processing request: {str(e)}"
        }), 500

@app.route('/read', methods=['GET'])
def read_data():
    """
    Endpoint to read data from file
    """
    file_path = r"c:\Sarathy\n8nflask.txt"
    
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                content = file.readlines()
            
            return jsonify({
                "success": True,
                "content": [line.strip() for line in content],
                "file_path": file_path
            }), 200
        else:
            return jsonify({
                "success": False,
                "message": "File does not exist"
            }), 404
    
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error reading file: {str(e)}"
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)