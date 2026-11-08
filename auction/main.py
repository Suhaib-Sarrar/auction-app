from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from . import models
from .database import engine
from .routers import user, product, auth, bid,notifications


app = FastAPI()


models.Base.metadata.create_all(engine)


app.include_router(user.router)
app.include_router(product.router)
app.include_router(auth.router)
app.include_router(bid.router)
app.include_router(notifications.router)


app.mount("/app", StaticFiles(directory="auction_HTML", html=True), name="frontend")
