"""
Ingest all files from data/source directory
"""
from src.system import SystemInitializer

print("Initializing system...")
system = SystemInitializer()
system.initialize_all(load_initial_data=False)

print("\nIngesting all files from data/source/...")
files_processed = system.ingestion_manager.ingest_directory("data/source")

print(f"\n[SUCCESS] Processed {files_processed} files!")
print("\nNow restart your backend:")
print("  python -m backend.main")
