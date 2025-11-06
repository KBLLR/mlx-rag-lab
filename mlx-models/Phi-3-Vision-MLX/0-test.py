from phi_3_vision_mlx import generate

response = generate('What is shown in this image?', 'https://collectionapi.metmuseum.org/api/collection/v1/iiif/344291/725918/main-image')
print(response)
