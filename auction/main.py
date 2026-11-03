from fastapi import FastAPI
from . import models
from .database import engine
from .routers import user,product,auth,bid


app = FastAPI()


models.Base.metadata.create_all(engine)


app.include_router(user.router)
app.include_router(product.router)
app.include_router(auth.router)
app.include_router(bid.router)
