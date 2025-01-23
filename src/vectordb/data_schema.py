from docarray import BaseDoc
from docarray.typing import NdArray

class MemoryMessage(BaseDoc):
    text: str = ''
    insertionOrdinal: int
    embedding: NdArray[1536]
    origin_messages: str