"""
Quick test to verify Foundry Local installation and basic functionality.

Run this to check:
1. Foundry CLI is installed
2. Python SDK is available
3. Can load and run a small model locally
"""

import sys
import subprocess
import json

def test_cli_installed():
    """Test if foundry CLI is available."""
    print("=" * 60)
    print("TEST 1: Checking Foundry CLI installation")
    print("=" * 60)
    try:
        result = subprocess.run(
            ["foundry", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f"✓ Foundry CLI found: {result.stdout.strip()}")
            return True
        else:
            print(f"✗ Foundry CLI error: {result.stderr}")
            return False
    except FileNotFoundError:
        print("✗ Foundry CLI not found in PATH")
        print("  Install from: https://learn.microsoft.com/en-us/azure/ai-foundry/foundry-local/get-started")
        return False
    except Exception as e:
        print(f"✗ Error checking CLI: {e}")
        return False

def test_service_status():
    """Check if Foundry Local service is running."""
    print("\n" + "=" * 60)
    print("TEST 2: Checking Foundry Local service status")
    print("=" * 60)
    try:
        result = subprocess.run(
            ["foundry", "service", "status"],
            capture_output=True,
            text=True,
            timeout=10
        )
        print(result.stdout)
        if "running" in result.stdout.lower():
            print("✓ Service is running")
            return True
        else:
            print("⚠ Service may not be running (will auto-start)")
            return True  # SDK can auto-start
    except Exception as e:
        print(f"⚠ Could not check status: {e}")
        return True  # SDK can handle this

def test_python_sdk():
    """Test if foundry-local-sdk Python package is available."""
    print("\n" + "=" * 60)
    print("TEST 3: Checking Python SDK installation")
    print("=" * 60)
    try:
        import foundry_local
        print(f"✓ foundry-local-sdk package found")
        print(f"  Module path: {foundry_local.__file__}")
        return True
    except ImportError as e:
        print(f"✗ foundry-local-sdk not installed")
        print(f"  Install with: pip install foundry-local-sdk")
        return False

def test_openai_sdk():
    """Test if openai package is available."""
    print("\n" + "=" * 60)
    print("TEST 4: Checking OpenAI SDK installation")
    print("=" * 60)
    try:
        import openai
        print(f"✓ openai package found")
        print(f"  Version: {openai.__version__ if hasattr(openai, '__version__') else 'unknown'}")
        return True
    except ImportError:
        print(f"✗ openai package not installed")
        print(f"  Install with: pip install openai")
        return False

def test_model_inference():
    """Test loading and running a small model."""
    print("\n" + "=" * 60)
    print("TEST 5: Testing model loading and inference")
    print("=" * 60)
    print("This will download a small model (~500MB) on first run...")
    print("Using: qwen2.5-0.5b (smallest available model)")
    
    try:
        from foundry_local import FoundryLocalManager
        import openai
        
        print("\n⏳ Initializing Foundry Local Manager...")
        # Use smallest model for quick test
        manager = FoundryLocalManager("qwen2.5-0.5b")
        
        print(f"✓ Service started at: {manager.endpoint}")
        print(f"✓ Model loaded: {manager.get_model_info('qwen2.5-0.5b').id}")
        
        # Test inference
        print("\n⏳ Testing inference with simple prompt...")
        client = openai.OpenAI(
            base_url=manager.endpoint,
            api_key=manager.api_key
        )
        
        response = client.chat.completions.create(
            model=manager.get_model_info("qwen2.5-0.5b").id,
            messages=[{"role": "user", "content": "Say 'test successful' in 3 words"}],
            max_tokens=20
        )
        
        result = response.choices[0].message.content
        print(f"✓ Model response: {result}")
        print(f"\n✅ INFERENCE TEST PASSED - Foundry Local is working!")
        return True
        
    except Exception as e:
        print(f"\n✗ Inference test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("\n" + "🔍" * 30)
    print("FOUNDRY LOCAL INSTALLATION TEST")
    print("🔍" * 30 + "\n")
    
    results = {}
    
    # Run tests
    results['cli'] = test_cli_installed()
    if results['cli']:
        results['service'] = test_service_status()
    else:
        results['service'] = False
        print("\nSkipping remaining tests - CLI not found")
        print_summary(results)
        return
    
    results['python_sdk'] = test_python_sdk()
    results['openai_sdk'] = test_openai_sdk()
    
    # Only test inference if all prerequisites pass
    if all([results['python_sdk'], results['openai_sdk']]):
        results['inference'] = test_model_inference()
    else:
        results['inference'] = False
        print("\nSkipping inference test - missing dependencies")
    
    print_summary(results)

def print_summary(results):
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name.replace('_', ' ').title()}")
    
    if all(results.values()):
        print("\n🎉 All tests passed! Foundry Local is ready to use.")
        print("\nNext steps:")
        print("  - Foundry Local is working correctly")
        print("  - You can now use it for IAI Authority implementation")
    else:
        print("\n⚠️  Some tests failed. See details above.")
        print("\nTroubleshooting:")
        if not results.get('cli'):
            print("  1. Install Foundry Local:")
            print("     https://learn.microsoft.com/en-us/azure/ai-foundry/foundry-local/get-started")
        if not results.get('python_sdk'):
            print("  2. Install Python SDK: pip install foundry-local-sdk")
        if not results.get('openai_sdk'):
            print("  3. Install OpenAI SDK: pip install openai")

if __name__ == "__main__":
    main()
