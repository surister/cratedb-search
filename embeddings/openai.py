import tiktoken
from openai import OpenAI


def num_tokens_from_string(string: str, encoding_name: str) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens


def get_embedding(content: str, token, model="text-embedding-3-small") -> list[int]:
    client = OpenAI(api_key=token)
    response = client.embeddings.create(
        input=content,
        model=model
    )
    return response.data[0].embedding
