from flask import Flask, render_template,request
import threading
import subprocess
from dotenv import set_key

app = Flask(__name__)

def run_script():
    subprocess.run(["python", "bot.py"])

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/run-bot', methods=['POST'])
def run_bot():
    receiver_email = request.form['receiver_email']
    min_stipend = int(request.form['min_stipend'])
    max_duration = int(request.form['max_duration'])
    keywords = [k.strip().lower() for k in request.form.getlist('keywords')]


    set_key(".env", "RECEIVER", receiver_email)
    set_key(".env", "MIN_STIPEND", str(min_stipend))
    set_key(".env", "MAX_DURATION", str(max_duration))
    set_key(".env", "KEYWORDS", ','.join(keywords))
 
    threading.Thread(target=run_script).start()
    return "Automation started! Check your browser."


if __name__ == "__main__":
    app.run(debug=True)
