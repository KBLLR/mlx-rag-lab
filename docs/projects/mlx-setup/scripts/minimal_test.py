
import mlx.core as mx
import time

print(f"MLX Version: {mx.__version__}")
print(f"Default device: {mx.default_device()}")

try:
    print("Creating a small array...")
    a = mx.random.normal((100, 100))
    mx.eval(a) # Force evaluation
    print("Small array created successfully.")

    print("\nAttempting a small matrix multiplication...")
    b = mx.random.normal((100, 100))
    c = a @ b
    mx.eval(c) # Force evaluation
    print("Matrix multiplication successful.")

except Exception as e:
    print(f"\nAn error occurred: {e}")

print("\nScript finished.")
