#!/usr/bin/env python3

# Brian Chairez
# Gangju Li
# Phillip Presuel

"""
This project will
"""

from flask import Flask, request, render_template

app = Flask(__name__)

@app.route('/')
def main():
    print('this is from my web app?')
    return '<html><h1>Hello World!</h1></html>'
