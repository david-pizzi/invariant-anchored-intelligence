"""
Pre-load qwen2.5-1.5b model into Foundry Local service.
"""
from foundry_local import FoundryLocalManager
import sys

print("=" * 60)
print("Loading qwen2.5-1.5b model...")
print("=" * 60)

try:
    # Initialize with longer timeout for large model
    print("\n⏳ Initializing FoundryLocalManager...")
    print("   This may take a minute for first-time download...\n")
    
    manager = FoundryLocalManager("qwen2.5-1.5b")
    
    print(f"\n✅ Success!")
    print(f"   Endpoint: {manager.endpoint}")
    print(f"   Model ID: {manager.get_model_info('qwen2.5-1.5b').id}")
    print(f"\n   Model is now ready for use in experiments.")
    
except Exception as e:
    print(f"\n❌ Error loading model: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
