from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return {"message": "Hello from Flask inside Minikube via Gunicorn!"}

if __name__ == '__main__':
    app.run()
