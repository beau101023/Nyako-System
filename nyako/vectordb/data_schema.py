from docarray import BaseDoc
from docarray.typing import NdArray
from datetime import datetime

class MemoryMessage(BaseDoc):
    text: str = ''
    insertionOrdinal: int
    embedding: NdArray[1536]