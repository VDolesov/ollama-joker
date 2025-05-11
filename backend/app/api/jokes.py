from fastapi import APIRouter
from ..services.generator import JokeGenerator

router = APIRouter()
joke_generator = JokeGenerator()

@router.get("/jokes")
async def get_joke(topic: str = "программистов"):
    joke = await joke_generator.generate(topic)
    return {"joke": joke}
@router.post("/clear_cache")
async def clear_cache():
    message = await joke_generator.clear_cache()
    return {"message": message}