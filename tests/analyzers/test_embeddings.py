# import os
# from app.analyzers.embeddings import embed_text, embed_images, split_and_embed_text

# def test_embed_text():
#     sample_text = "This is a sample text to test the text embedding function."
    
#     embeddings = embed_text(sample_text)
#     embeddings_2 = split_and_embed_text(sample_text)
    
#     assert embeddings is not None, "Embeddings should not be None."
#     assert embeddings_2 is not None, "Embeddings 2 should not be None."
#     assert len(embeddings) > 0, "Embeddings should not be empty."
#     assert len(embeddings_2) > 0, "Embeddings 2 should not be empty."
#     print("Text embeddings generated successfully!")
    

# def test_embed_images():
#     # Ensure you have an image file for testing
#     test_image_path = "./tests/analyzers/test_image.jpg"
#     assert os.path.exists(test_image_path), "Test image file does not exist."

#     embeddings = embed_images(test_image_path)
    
#     assert embeddings is not None, "Embeddings should not be None."
#     assert len(embeddings.embedding) > 0, "Embeddings should not be empty."
#     print("Image embeddings generated successfully!")

