from dataclasses import dataclass


@dataclass
class Prompt:
    """
    Data model representing a prompt.

    Attributes:
        prompt_id (str): Unique identifier for the prompt.
        text (str): The prompt text content.
    """

    prompt_id: str
    text: str
