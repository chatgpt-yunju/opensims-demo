#!/usr/bin/env python3
"""
API Fallback Test - verify fallback to mock when API fails
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api_client import APIClient
from virtual_human import SimPerson
from config import PERSONALITY_PRESETS

def test_api_fallback_to_mock():
    """测试API调用失败时降级到Mock"""
    print("[Test] API Fallback to Mock")

    # 创建一个无效的API客户端（使用无效endpoint）
    api = APIClient(
        endpoint="https://invalid.example.com/v1/chat/completions",
        api_key="fake-key",
        model="test-model",
        use_mock=False
    )

    vh = SimPerson(name="TestVH", personality=PERSONALITY_PRESETS["温柔型"])

    try:
        # 这个调用应该会失败并降级到mock
        response = api.generate_reply(vh, "Hello, how are you?")
        reply = response.get("reply", "")
        print(f"  Received reply: {reply[:50]}...")
        print("  PASS: API fallback to mock works")
        return True
    except Exception as e:
        print(f"  FAIL: {e}")
        return False

def test_mock_mode_forced():
    """测试强制使用Mock模式"""
    print("\n[Test] Forced Mock Mode")

    api = APIClient(use_mock=True)
    vh = SimPerson(name="TestVH", personality=PERSONALITY_PRESETS["温柔型"])

    try:
        response = api.generate_reply(vh, "Test question")
        reply = response.get("reply", "")
        print(f"  Mock reply: {reply[:50]}...")
        print("  PASS: Forced mock mode works")
        return True
    except Exception as e:
        print(f"  FAIL: {e}")
        return False

def test_streaming_fallback():
    """测试流式调用失败时降级"""
    print("\n[Test] Streaming Fallback")

    api = APIClient(
        endpoint="https://invalid.example.com/v1/chat/completions",
        api_key="fake",
        use_mock=False
    )
    vh = SimPerson(name="TestVH", personality=PERSONALITY_PRESETS["温柔型"])

    chunks = []
    def callback(chunk):
        chunks.append(chunk)

    try:
        result = api.generate_reply(vh, "Hello", stream_callback=callback)
        # 降级情况下，应该返回 None（已通过回调发送内容）
        if len(chunks) > 0:
            print(f"  Received {len(chunks)} chunks via mock fallback")
            print("  PASS: Streaming fallback works")
            return True
        elif result is not None:
            # 非流式回退也接受
            print(f"  Non-streaming fallback returned")
            print("  PASS: Streaming fallback works")
            return True
        else:
            print("  FAIL: No content received")
            return False
    except Exception as e:
        print(f"  FAIL: {e}")
        return False

def main():
    print("="*60)
    print("OpenSims API Fallback Test")
    print("="*60)

    results = []
    tests = [
        test_api_fallback_to_mock,
        test_mock_mode_forced,
        test_streaming_fallback,
    ]

    for test_func in tests:
        try:
            passed = test_func()
            results.append((test_func.__name__, passed))
        except Exception as e:
            results.append((test_func.__name__, False, str(e)))

    print("\n" + "="*60)
    print("SUMMARY")
    passed_count = sum(1 for _, p in results if p)
    total = len(results)
    print(f"Passed: {passed_count}/{total}")
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {name}")
    print("="*60)

    all_pass = all(passed for _, passed in results)
    return all_pass

if __name__ == "__main__":
    success = main()
    try:
        input("\nPress Enter to exit...")
    except (EOFError, KeyboardInterrupt):
        pass
    sys.exit(0 if success else 1)
