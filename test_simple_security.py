#!/usr/bin/env python3
"""
Simple test to verify Flask after_request decorator works
"""

from flask import Flask

app = Flask(__name__)

@app.after_request
def add_security_headers(response):
    print("🔒 After request called!")
    response.headers['X-Test-Header'] = 'Working'
    return response

@app.route('/')
def index():
    return "Hello World!"

if __name__ == '__main__':
    print("Starting simple Flask app...")
    app.run(host='0.0.0.0', port=5001, debug=True)
