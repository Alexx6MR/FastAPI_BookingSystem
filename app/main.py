from fastapi import FastAPI
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from db.seed import seed
from db.dbConfig import create_db_and_tables
from routes.auth import auth_router
from routes.classroom import classroom_router
from routes.user import user_router


# Defines the lifespan of the application, creating database tables and seeding data during startup, and cleaning up resources during shutdown.
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the ML model
    create_db_and_tables()
    seed()
    yield
    # Clean up the ML models and release the resources
 
# Defines the app object and static folder.
app = FastAPI(lifespan=lifespan)
BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

# Adds CORS middleware to allow requests from any origin, with credentials, and all methods and headers.(NOT Important )
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Defines the root endpoint that redirects users to the /classrooms page.
@app.get("/")
def root()-> None:
    return RedirectResponse(url="/classrooms")

# Includes the all the routers in the app.
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(classroom_router, prefix="/classrooms", tags=["classrooms"])
app.include_router(user_router, prefix="/user", tags=["users"])

