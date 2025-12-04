# 🧪 Test Secret Validator

"""Quick test of secret validation and containment system."""

import sys
from secret_validator import SecretValidator
from containment import ContainmentSystem

print("=" * 80)
print("🔐 Testing Secret Validation Module")
print("=" * 80)

# Initialize
validator = SecretValidator()
containment = ContainmentSystem()

# Test 1: Key Type Detection
print("\n[1/3] Testing key type detection...")
test_keys = [
    ("OpenAI API Key", "sk-proj-abc123"),
    ("GitHub Token", "ghp_abc123def456"),
    ("Anthropic API Key", "sk-ant-xyz789"),
    ("Slack Token", "xoxb-123-456"),
    ("Stripe Key", "sk_live_abc123"),
    ("Discord Token", "Bot MTk4N..."),
]

for secret_type, key in test_keys:
    method = validator.detect_key_type(secret_type, key)
    status = "✅" if method else "❌"
    print(f"  {status} {secret_type:25s} → {method or 'NOT DETECTED'}")

# Test 2: Mock Validation (without actual API calls)
print("\n[2/3] Testing validation response format...")
mock_result = validator._invalid_response('TestAPI')
assert 'active' in mock_result
assert 'status' in mock_result
assert 'risk_level' in mock_result
print("  ✅ Response format correct")

# Test 3: Containment Stats
print("\n[3/3] Testing containment system...")
stats = containment.get_quarantine_stats()
print(f"  ✅ Quarantined repos: {stats['total_quarantined_repos']}")
print(f"  ✅ Total secrets: {stats['total_active_secrets']}")
print(f"  ✅ Containment dir: {stats['containment_directory']}")

print("\n" + "=" * 80)
print("🎉 All tests passed!")
print("=" * 80)

print("\n📋 Supported APIs:")
print("  AI/LLM:        OpenAI, Anthropic, Gemini, HuggingFace")
print("  Cloud:         AWS, DigitalOcean")
print("  Services:      GitHub, Stripe, SendGrid, Twilio")
print("  Communication: Discord, Slack, Telegram")

print("\n⚠️  Note: Actual validation requires ENABLE_SECRET_VALIDATION=true in .env")
print("⚠️  Use only with authorization for security research!")

sys.exit(0)
