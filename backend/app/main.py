from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import jokes

app = FastAPI(title="Jokes API", version="1.0.0")

app.add_middleware(

    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jokes.router, prefix="/api/v1")