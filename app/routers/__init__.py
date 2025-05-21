from app.routers.auth import router as auth_router
from app.routers.users import router as users_router
from app.routers.salons import router as salons_router
from app.routers.services import router as services_router
from app.routers.stylists import router as stylists_router
from app.routers.appointments import router as appointments_router
from app.routers.ratings import router as ratings_router
from app.routers.chatbot import router as chatbot_router

# Export routers
auth = auth_router
users = users_router
salons = salons_router
services = services_router
stylists = stylists_router
appointments = appointments_router
ratings = ratings_router
chatbot = chatbot_router