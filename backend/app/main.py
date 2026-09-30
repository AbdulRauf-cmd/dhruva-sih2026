from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import init_db, engine
from app.routers import auth, expeditions, cargo, inventory, personnel, emergency, sync_router, admin, dashboard, audit, demo

app = FastAPI(title='DHRUVA', description='Polar Expedition Management Platform', version='1.0.0')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(auth.router)
app.include_router(expeditions.router)
app.include_router(cargo.router)
app.include_router(inventory.router)
app.include_router(personnel.router)
app.include_router(emergency.router)
app.include_router(sync_router.router)
app.include_router(admin.router)
app.include_router(dashboard.router)
app.include_router(audit.router)
app.include_router(demo.router)

@app.on_event('startup')
def startup():
    init_db(engine)
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        from app.seed import seed_data
        seed_data(db)
    finally:
        db.close()

@app.get('/api/health')
def health():
    return {'status': 'ok', 'node_id': settings.NODE_ID, 'role': settings.NODE_ROLE}
