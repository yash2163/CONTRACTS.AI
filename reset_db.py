from src.database import Base, engine

print("Dropping old tables...")
Base.metadata.drop_all(bind=engine)
print("Old tables dropped.")

print("Creating new tables...")
Base.metadata.create_all(bind=engine)
print("New tables created successfully!")