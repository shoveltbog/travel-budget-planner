import requests
from flask import Flask, render_template, request
from config import EXCHANGE_RATE_API_KEY, WEATHERSTACK_API_KEY

app = Flask(__name__)

# Weatherstack API Function
def get_weather(city):
    """Fetch current weather data for a given city."""
    BASE_URL = "http://api.weatherstack.com/current"
    params = {
        "access_key": WEATHERSTACK_API_KEY,
        "query": city
    }

    response = requests.get(BASE_URL, params=params)
    data = response.json()

    # Handle API errors properly
    if "error" in data:
        print(f"API Error: {data['error']['info']}")
        return None

    # Extract weather details
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
        return None

# Function to Get Currency from Country Name
def get_currency_from_country(country_name):
    """Fetch the currency code dynamically for a given country."""
    url = f"https://restcountries.com/v3.1/name/{country_name}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        if isinstance(data, list) and len(data) > 0:
            return list(data[0]["currencies"].keys())[0]
    return "USD"

# Exchange Rate API Function
def get_exchange_rate(base_currency="AUD", country=None):
    """Fetch the exchange rate dynamically for a given country."""
    target_currency = get_currency_from_country(country) if country else "USD"

    url = f"https://v6.exchangerate-api.com/v6/{EXCHANGE_RATE_API_KEY}/latest/{base_currency}"
    response = requests.get(url)
    data = response.json()

    if "conversion_rates" in data:
        return data["conversion_rates"].get(target_currency, None), target_currency
    return None, target_currency

# Flask Routes
@app.route('/')
def home():
    return render_template("index.html")

@app.route('/budget', methods=['POST'])
def budget():
    """Handles user input, fetches weather & exchange rates, and returns a response."""
    destination = request.form['destination']
    budget = request.form['budget']
    duration = request.form['duration']

    # Validate inputs
    if not destination.replace(" ", "").isalpha():
        return "Error: Destination must only contain letters and spaces."

    try:
        budget = float(budget)
        duration = int(duration)

        if budget < 100:
            return "Error: Budget must be at least $100."
        if duration < 1 or duration > 365:
            return "Error: Trip duration must be between 1 and 365 days."

    except ValueError:
        return "Error: Invalid number input."

    # Get weather data
    weather = get_weather(destination)

    # Get country from weather data
    country = weather["country"] if weather else None

    # Fetch exchange rate dynamically
    exchange_rate, target_currency = get_exchange_rate("AUD", country)

    # Generate Response
    if exchange_rate:
        converted_budget = round(budget * exchange_rate, 2)
        return (f"You are planning a {duration}-day trip to {destination} with a budget of AUD ${budget}.\n"
                f"This is equivalent to {target_currency} ${converted_budget}.\n"
                f"📍 Location: {weather['city']}, {weather['region']}, {weather['country']}\n"
                f"🕒 Local Time: {weather['local_time']}\n"
                f"🌡 Temperature: {weather['temperature']}°C (Feels like {weather['feels_like']}°C)\n"
                f"💧 Humidity: {weather['humidity']}%\n"
                f"🌧 Precipitation: {weather['precipitation']} mm\n"
                f"☀ UV Index: {weather['uv_index']}\n")
    else:
        return f"You are planning a {duration}-day trip to {destination} with a budget of AUD ${budget}. Unable to fetch exchange rates."

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
