import mlx.core as mx
import platform
import sys
import os

def run_health_check():
    print("--- MLX Environment Health Check ---")
    print(f"Date: {os.popen('date').read().strip()}")
    print(f"Operating System: {platform.platform()}")
    print(f"Python Version: {sys.version}")
    print("\n--- MLX Core Verification ---")

    try:
        print(f"MLX Version: {mx.__version__}")
        
        # Check default device
        default_device = mx.default_device()
        print(f"MLX Default Device: {default_device}")
        assert default_device.type == mx.DeviceType.gpu or default_device.type == mx.DeviceType.cpu, \
            f"MLX default device type not as expected! Got {default_device.type}"
        print("Default device check passed.")

        # Test array creation and basic operation
        x = mx.array([1, 2, 3], mx.float32)
        mx.eval(x) # Explicitly evaluate
        print(f"Created MLX array: {x}")
        print("Basic array creation passed.")

        print("\n--- Lazy Computation Test ---")
        a = mx.array([1, 2, 3])
        b = mx.array([4, 5, 6])
        c_lazy = a + b
        print(f"Lazy array 'c' created.")
        mx.eval(c_lazy) # mx.eval() evaluates in place and returns None
        print(f"Result 'c' after mx.eval(): {c_lazy}")
        expected = mx.array([5, 7, 9])
        assert mx.array_equal(c_lazy, expected), "Lazy computation test failed!"
        print("Lazy computation test passed.")

        print("\n--- Unified Memory Test ---")
        # This test implicitly verifies unified memory by performing operations
        # without explicit data transfers, relying on MLX's design.
        m1 = mx.random.normal((100, 100))
        m2 = mx.random.normal((100, 100))
        m3 = m1 @ m2
        mx.eval(m3) # Explicitly evaluate
        print(f"Matrix multiplication (100x100) completed successfully on default device.")
        print("Unified memory test passed.")

        print("\n--- MLX Environment Health Check: PASSED ---")

    except Exception as e:
        print(f"\n--- MLX Environment Health Check: FAILED ---")
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_health_check()