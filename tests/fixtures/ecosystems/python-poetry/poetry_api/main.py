from fastapi import FastAPI
app = FastAPI()

@app.get('/items')
def items():
    return []
