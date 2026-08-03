from fastapi import FastAPI

app = FastAPI(title='AI Finance System')

@app.get('/')
def root():
    return {'message': 'AI Finance System is running successfully'}