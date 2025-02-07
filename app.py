from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/budget', methods=['POST'])
def budget():
    destination = request.form['destination']
    budget = float(request.form['budget'])
    duration = int(request.form['duration'])

    # Backend validation
    if not destination.replace(" ", "").isalpha():
        return "Error: Destination must only contain letters and spaces."

    try:
        budget = float(budget)
        duration = int(duration)

        if budget < 100:
            return "Error: Budget must be at least $50."
        if duration < 1 or duration > 365:
            return "Error: Trip duration must be between 1 and 1461 days."

    except ValueError:
        return "Error: Invalid number input."

    return f"You are planning a {duration}-day trip to {destination} with a budget of ${budget}."

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)