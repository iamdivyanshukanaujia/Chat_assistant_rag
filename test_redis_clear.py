"""
Test Redis clear history functionality
"""
from src.memory import MemoryManager
from src.config import settings
import redis

print("Testing Redis chat history clear...")
print(f"Redis: {settings.redis_host}:{settings.redis_port}")

# Test Redis connection
try:
    r = redis.Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        password=settings.redis_password if settings.redis_password else None,
        db=settings.redis_db
    )
    r.ping()
    print("[OK] Redis is running")
except Exception as e:
    print(f"[ERROR] Redis: {e}")
    print("\nRedis might not be running!")
    exit(1)

# Test memory manager
memory = MemoryManager()
test_session = "test_clear_123"

# Add a test message
history = memory.get_message_history(test_session)
from langchain_core.messages import HumanMessage
history.add_message(HumanMessage(content="Test message"))
print(f"\n[OK] Added test message to session: {test_session}")

# Check it exists
messages = history.messages
print(f"Messages before clear: {len(messages)}")

# Clear it
memory.clear_session(test_session)
print(f"\n[OK] Called clear_session()")

# Check if actually deleted from Redis
key = f"{settings.memory_redis_prefix}:chat:{test_session}"
exists = r.exists(key)
print(f"\nRedis key '{key}' exists: {exists}")

if exists:
    print("[PROBLEM] Key still exists in Redis after clear!")
else:
    print("[GOOD] Key deleted from Redis successfully")

# Verify by reloading
history2 = memory.get_message_history(test_session)
messages_after = history2.messages
print(f"Messages after reload: {len(messages_after)}")

if len(messages_after) == 0:
    print("\n[SUCCESS] Clear history works correctly!")
else:
    print(f"\n[BUG] {len(messages_after)} messages still exist after clear")
