import webbrowser
import threading
from app import app  

def run_server():
    app.run(port=5000, debug=True, use_reloader=False)

# Start the Flask app in a background thread
threading.Thread(target=run_server).start()

# Open browser window automatically
webbrowser.open("http://127.0.0.1:5000")
