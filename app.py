import requests
from flask import Flask, render_template, request
from config import EXCHANGE_RATE_API_KEY, WEATHERSTACK_API_KEY
import pandas as pd

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

# Function to Get Currency code & symbol from Country Name from RestCountries API
def get_currency_from_country(country_name):
    """Fetch the currency code dynamically for a given country."""
    url = f"https://restcountries.com/v3.1/name/{country_name}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        if isinstance(data, list) and len(data) > 0:
            currencies = data[0].get("currencies", {})
            if currencies:
                currency_code = list(currencies.keys())[0]  # Extract currency code (e.g., EUR)
                currency_symbol = currencies[currency_code].get("symbol", currency_code)  # Extract symbol or fallback to code
                return currency_code, currency_symbol
    return "USD", "$"  # Default to USD if lookup fails

# Exchange Rate API Function
def get_exchange_rate(base_currency="AUD", country=None):
    """Fetch the exchange rate dynamically based on the user's destination country."""
    target_currency, target_symbol = get_currency_from_country(country) if country else ("USD", "$")

    url = f"https://v6.exchangerate-api.com/v6/{EXCHANGE_RATE_API_KEY}/latest/{base_currency}"
    response = requests.get(url)
    data = response.json()

    if "conversion_rates" in data:
        return data["conversion_rates"].get(target_currency, None), target_currency, target_symbol
    return None, target_currency, target_symbol

# Load cost of living dataset
cost_of_living_df = pd.read_csv("cost-of-living_v2.csv")

def get_cost_of_living(city):
    """Fetch cost of living data from the dataset based on the city."""
    # Convert city names to lowercase for matching
    city = city.lower()
    cost_data = cost_of_living_df[cost_of_living_df["city"].str.lower() == city]

    if cost_data.empty:
        return None  # No matching city found
    
    # Convert row to dictionary and exclude city and country
    cost_data_dict = cost_data.iloc[0].to_dict()
    # Remove city and country
    cost_data_dict.pop('city', None)
    cost_data_dict.pop('country', None)
    
    return cost_data_dict

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

        if budget < 50:
            return "Error: Budget must be at least $50."
        if duration < 1 or duration > 730:
            return "Error: Trip duration must be between 1 and 730 days."

    except ValueError:
        return "Error: Invalid number input."

    # Get weather data
    weather = get_weather(destination)

    # Get country from weather data
    country = weather["country"] if weather else None

    # Fetch exchange rate dynamically
    exchange_rate, target_currency, target_symbol = get_exchange_rate("AUD", country)

    # Fetch cost of living data for destination
    cost_of_living = get_cost_of_living(destination)

    if cost_of_living:
        cost_summary = "\n".join([f"{key}: {value}" for key, value in cost_of_living.items()])
    else:
        cost_summary = "Cost of living data unavailable for this destination."

    print("Cost of Living:", cost_of_living)
    print("Exchange Rate:", exchange_rate)
    print("Weather:", weather)

    # Generate Response
    if exchange_rate:
        # **Calculate Daily Budget**
        daily_budget_aud = round(budget / duration, 2)
        converted_budget = round(budget * exchange_rate, 2)
        daily_budget_converted = round(converted_budget / duration, 2)
        formatted_budget = f"({target_currency}) {target_symbol}{converted_budget}"
        formatted_daily_budget = f" ({target_currency}) {target_symbol}{daily_budget_converted}"
    else:
        converted_budget = None
        
    # Construct response message
    response_message = (
        f"You are planning a {duration}-day trip to {destination} with a budget of (AUD) A${budget}.\n"
        f"This is equivalent to {formatted_budget}.\n"
        f"Daily Budget: (AUD) A${daily_budget_aud} per day or {formatted_daily_budget} per day\n"
        f"📍 Location: {weather['city']}, {weather['region']}, {weather['country']}\n"
        f"🕒 Local Time: {weather['local_time']}\n"
        f"🌡 Temperature: {weather['temperature']}°C (Feels like {weather['feels_like']}°C)\n"
        f"💧 Humidity: {weather['humidity']}%\n"
        f"🌧 Precipitation: {weather['precipitation']} mm\n"
        f"☀ UV Index: {weather['uv_index']}\n"
        f"\nCost of Living:\n"
        f"{cost_summary}"
        )

    return response_message

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
