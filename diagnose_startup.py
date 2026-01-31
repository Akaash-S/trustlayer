import sys
import os
import traceback

print("🔍 Starting Diagnostic Check...")

# 1. Add CWD to path (same as proxy_addon.py)
cwd = os.getcwd()
if cwd not in sys.path:
    sys.path.append(cwd)
    print(f"✅ Added {cwd} to sys.path")

# 2. Try importing Dependencies
try:
    print("⏳ Importing Presidio...")
    import presidio_analyzer
    print(f"✅ Presidio version: {presidio_analyzer.__version__}")
except ImportError:
    print("❌ FAILED to import presidio_analyzer")
    print(traceback.format_exc())
    sys.exit(1)

# 3. Try importing App Modules
try:
    print("⏳ Importing App Modules (Redaction)...")
    from app.modules.redaction import redact_text
    print("✅ Redaction module loaded")
except Exception:
    print("❌ FAILED to import app.modules.redaction")
    print(traceback.format_exc())
    sys.exit(1)

try:
    print("⏳ Importing App Modules (Database)...")
    from app.core.database import init_db
    print("✅ Database module loaded")
except Exception:
    print("❌ FAILED to import app.core.database")
    print(traceback.format_exc())
    sys.exit(1)

# 4. Try Loading Models (This is where it likely crashes)
try:
    print("⏳ Testing Redaction Engine (Model Load)...")
    res = redact_text("My name is John")
    print(f"✅ Model Works! Result: {res.items}")
except Exception:
    print("❌ FAILED to run Redaction (Model Issue?)")
    print(traceback.format_exc())
    sys.exit(1)

print("🎉 DIAGNOSTIC PASSED: The code is fine. The issue is likely checking the right port.")
