
import mlx.core as mx

try:
    print(f"MLX Version: {mx.__version__}")
    x = mx.array([1, 2, 3], mx.float32)
    print(f"Created MLX array: {x}")
    
    # Check the default device MLX is configured to use
    default_device = mx.default_device()
    print(f"MLX default device: {default_device}")
    print(f"Type of default_device.type: {type(default_device.type)}")
    print(f"Value of default_device.type: {default_device.type}")
    assert default_device.type == mx.DeviceType.gpu or default_device.type == mx.DeviceType.cpu, "MLX default device type not as expected!"
    
    print("Core MLX installation verified successfully.")
except Exception as e:
    print(f"Error during MLX verification: {e}")
    import sys
    sys.exit(1)
