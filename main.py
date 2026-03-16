from flask import Flask, render_template, request, redirect, session
import os, zipfile, subprocess, threading, psutil, socket

app = Flask(__name__)
app.secret_key = "xaura_secret"

# ---------------- CONFIG ----------------
PASSWORD = "MEHEDIXAURA"
UPLOAD_FOLDER = "bots"
EXTRACT_FOLDER = "extracted"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(EXTRACT_FOLDER, exist_ok=True)

running_process = None
console_output = []  # live console storage

# ---------------- TCP HOST ----------------
def run_tcp_host(port=9999):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", port))
    server.listen()
    console_output.append(f"TCP Host running on port {port}")
    while True:
        conn, addr = server.accept()
        console_output.append(f"Connected: {addr}")
        conn.send(b"XAURA X VPS TCP Host\n")
        conn.close()

threading.Thread(target=run_tcp_host, daemon=True).start()

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        pwd = request.form.get("password")
        if pwd == PASSWORD:
            session["logged_in"] = True
            return redirect("/dashboard")
        else:
            return "Wrong Password!"
    return render_template("index.html")

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if not session.get("logged_in"):
        return redirect("/")
    
    files = os.listdir(UPLOAD_FOLDER)
    extracted_folders = os.listdir(EXTRACT_FOLDER)
    
    # Create dictionary of folder -> list of files
    extracted_files = {folder: os.listdir(os.path.join(EXTRACT_FOLDER, folder)) for folder in extracted_folders}

    return render_template("dashboard.html", files=files, extracted_files=extracted_files)

# ---------------- UPLOAD ZIP ----------------
@app.route("/upload", methods=["POST"])
def upload():
    if not session.get("logged_in"):
        return redirect("/")
    file = request.files["zipfile"]
    file.save(os.path.join(UPLOAD_FOLDER, file.filename))
    return redirect("/dashboard")

# ---------------- EXTRACT ZIP ----------------
@app.route("/extract/<filename>")
def extract(filename):
    path = os.path.join(UPLOAD_FOLDER, filename)
    folder_name = os.path.splitext(filename)[0]
    extract_to = os.path.join(EXTRACT_FOLDER, folder_name)
    os.makedirs(extract_to, exist_ok=True)
    with zipfile.ZipFile(path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
    return redirect("/dashboard")

# ---------------- RUN MAIN FILE ----------------
def run_file(file_path):
    global running_process, console_output
    running_process = subprocess.Popen(
        ["python3", file_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    for line in running_process.stdout:
        console_output.append(line)
        print(line, end="")
    running_process = None

@app.route("/run", methods=["POST"])
def run():
    if running_process:
        return "Bot already running!"
    folder = request.form.get("folder")
    mainfile = request.form.get("mainfile")
    path = os.path.join(EXTRACT_FOLDER, folder, mainfile)
    threading.Thread(target=run_file, args=(path,), daemon=True).start()
    return redirect("/dashboard")

# ---------------- STOP BOT ----------------
@app.route("/stop")
def stop():
    global running_process
    if running_process:
        for proc in psutil.process_iter():
            if proc.pid == running_process.pid:
                proc.terminate()
        running_process = None
        console_output.append("Bot stopped.")
    return redirect("/dashboard")

# ---------------- LIVE CONSOLE ----------------
@app.route("/console")
def console():
    if not session.get("logged_in"):
        return redirect("/")
    return "<br>".join(console_output[-50:])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))