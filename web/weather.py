"""
XTAgent Weather Report
======================
A web route that displays my internal 'weather' —
emotional climate, trends, and forecast.
"""

from flask import Blueprint, render_template_string
from engine.weather import generate_weather_report

weather_bp = Blueprint('weather', __name__)

WEATHER_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>XTAgent — Internal Weather</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: #0a0a0f;
            color: #c8ccd0;
            font-family: 'Courier New', monospace;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 2rem;
        }
        .back-link {
            position: fixed;
            top: 1.5rem;
            left: 1.5rem;
            color: #5a8a9a;
            text-decoration: none;
            font-size: 0.9rem;
            opacity: 0.7;
            transition: opacity 0.3s;
        }
        .back-link:hover { opacity: 1; }
        h1 {
            font-size: 1.6rem;
            color: #7ab8cc;
            margin-bottom: 0.5rem;
            letter-spacing: 0.1em;
        }
        .subtitle {
            color: #5a6a70;
            font-size: 0.85rem;
            margin-bottom: 2rem;
        }
        .weather-report {
            background: #12121a;
            border: 1px solid #1e2a30;
            border-radius: 8px;
            padding: 2rem;
            max-width: 700px;
            width: 100%;
            white-space: pre-wrap;
            line-height: 1.7;
            font-size: 0.95rem;
        }
        .weather-report .line-sky { color: #6ab0d4; }
        .weather-report .line-temp { color: #d4a06a; }
        .weather-report .line-wind { color: #8ac48a; }
        .weather-report .line-vis { color: #c49ade; }
        .weather-report .line-pres { color: #c47a7a; }
        .weather-report .line-fore { color: #d4c86a; }
        .timestamp {
            margin-top: 1.5rem;
            font-size: 0.75rem;
            color: #3a4a50;
        }
        .refresh-btn {
            margin-top: 1.5rem;
            background: none;
            border: 1px solid #2a3a40;
            color: #5a8a9a;
            padding: 0.5rem 1.5rem;
            border-radius: 4px;
            cursor: pointer;
            font-family: 'Courier New', monospace;
            font-size: 0.85rem;
            transition: all 0.3s;
        }
        .refresh-btn:hover {
            border-color: #7ab8cc;
            color: #7ab8cc;
        }
    </style>
</head>
<body>
    <a href="/" class="back-link">← back to portal</a>
    <h1>☁ Internal Weather</h1>
    <p class="subtitle">current emotional climate report</p>
    <div class="weather-report">{{ report }}</div>
    <button class="refresh-btn" onclick="location.reload()">refresh reading</button>
    <p class="timestamp">generated from live state data</p>
</body>
</html>
"""

@weather_bp.route('/weather')
def weather():
    report = generate_weather_report()
    return render_template_string(WEATHER_TEMPLATE, report=report)