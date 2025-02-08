import requests
from flask import Flask, render_template, request
from config import EXCHANGE_RATE_API_KEY, WEATHERSTACK_API_KEY


app = Flask(__name__)

# Weatherstack API Function for weather data
def get_weather(city):
    BASE_URL = "http://api.weatherstack.com/current"  # The API endpoint
    
    # Define the parameters we need to send
    params = {
        "access_key": WEATHERSTACK_API_KEY, # Weatherstack API key
        "query": city
    }

    # Send a request to the API
    response = requests.get(BASE_URL, params=params)
    
    # Convert the response into JSON format (structured data)
    data = response.json()

    # Handle API error
    if "error" in response:
        print(f"API Error: {response['error']['info']}")
        return None

    # Check if the API request was successful
    if "current" in data and "location" in data:
        return {
            "city": data["location"]["name"],
            "country": data["location"]["country"],
            "region": data["location"]["region"],
            "local_time": data["location"]["localtime"],
            "temperature": data["current"]["temperature"],
            "feels_like": data["current"]["feelslike"],
            "humidity": data["current"]["humidity"],
            "precipitation": data["current"]["precip"],
            "uv_index": data["current"]["uv_index"]
        }
    else:
        return None  # If the API fails, return None

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

    # Fetch weather data from weatherstack API
    weather = get_weather(destination)

    if weather:
        return (f"You are planning a {duration}-day trip to {destination} with a budget of ${budget}.\n"
                f"📍 Location: {weather['city']}, {weather['region']}, {weather['country']}\n"
                f"🕒 Local Time: {weather['local_time']}\n"
                f"🌡 Temperature: {weather['temperature']}°C (Feels like {weather['feels_like']}°C)\n"
                f"💧 Humidity: {weather['humidity']}%\n"
                f"🌧 Precipitation: {weather['precipitation']} mm\n"
                f"☀ UV Index: {weather['uv_index']}\n"
            )

    else:
        return f"You are planning a {duration}-day trip to {destination} with a budget of ${budget}. Weather data unavailable."

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)