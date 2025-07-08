from litellm import completion
from typing import List
from pydantic import BaseModel


class SmartNotes(BaseModel):
    title: str
    notes: str
    references: List[str]


class SmartNotesBase(BaseModel):
    user_id: str
    file_name: str
    smart_notes: SmartNotes


response = completion(
    model="gpt-4.1-mini",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is the capital of France?"}
    ]
)

print(response)
