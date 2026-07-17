from flask import Flask, render_template, request
from analyzer import analyze_folder

app = Flask(__name__)

@app.route("/")
def dashboard():
    log_dir = request.args.get("logdir", "logs")  # allow ?logdir=logs
    data = analyze_folder(log_dir)
    return render_template("dashboard.html", data=data)

if __name__ == "__main__":
    # Run: http://127.0.0.1:5000
    app.run(debug=True)