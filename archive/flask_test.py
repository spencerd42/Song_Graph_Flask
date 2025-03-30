from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

@app.route('/')
def hello_world():
    return render_template('index.html')

@app.route('/print_input', methods=['POST'])
def print_input():
    user_input = request.json.get('input')  # Get input from the JSON payload
    print(f"User Input: {user_input}")  # Print the input to the console
    return jsonify(message="Input received and printed to console!")

if __name__ == '__main__':
    app.run(debug=True)