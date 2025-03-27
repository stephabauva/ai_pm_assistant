from fasthtml.fastapp import FastHTML
from fastapi import FastAPI
from fasthtml.common import *

# Create FastAPI app with FastHTML integration
app = FastHTML()

# Define the root route
@app.get('/')
def home():
    return (
        Title("AI-Powered Product Management Assistant"),
        Main(
            H1("AI-Powered Product Management Assistant"),
            P("Welcome to your PM Assistant"),
            cls="container"
        )
    )

# Run the app
if __name__ == '__main__':
    serve(host='localhost', port=5001)