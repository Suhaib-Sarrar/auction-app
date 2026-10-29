from fastapi import FastAPI
from . import models
from .database import engine
from .routers import owner


app = FastAPI()


models.Base.metadata.create_all(engine)


app.include_router(owner.router)
