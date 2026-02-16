from fastapi import FastAPI
from app.routes.auth import router as auth_router
from app.routes.login import router as login_router
from app.routes.invites import router as invites_router
from app.routes.websockets import router as websocket_router
from app.routes.players import router as players_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}

app.include_router(auth_router)
app.include_router(login_router)
app.include_router(invites_router)
app.include_router(websocket_router)
app.include_router(players_router)