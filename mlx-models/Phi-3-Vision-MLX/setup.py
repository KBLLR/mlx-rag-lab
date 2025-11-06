from setuptools import setup, find_packages

setup(
    name="phi-3-vision-mlx",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        'mlx',
        'gradio>=4.31.5',
        'huggingface_hub',
        'datasets',
        'Pillow',
        'requests',
        'matplotlib',
        'transformers',
        'pydantic>=2.0.0',  # Added this line
        'fastapi>=0.100.0',
        'starlette>=0.27.0',
    ],
    entry_points={
        'console_scripts': [
            'phi3v=phi_3_vision_mlx.phi_3_vision_mlx:chat_ui',
        ],
    },
)
