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

    return f"You are planning a {duration}-day trip to {destination} with a budget of ${budget}."

if __name__ == '__main__':
    app.run(debug=True)