import numpy as np

from typing import List
from docarray.index.backends.hnswlib import HnswDocumentIndex
from docarray import DocList
from vectordb.data_schema import MemoryMessage
from params import ASYNCOPENAI as client
from params import similarity_threshold

# workspace path
similarityIndex = HnswDocumentIndex[MemoryMessage](work_dir='./vectordb/workspace_path')

async def insertToMemory(text: str | None, origin_messages: str):
    if text is None:
        return

    embedding = await getTextEmbedding(origin_messages)
    embedding = np.array(embedding, dtype=float)
    similarityIndex.index(DocList[MemoryMessage]([MemoryMessage(text=text, insertionOrdinal=similarityIndex.num_docs(), embedding=embedding, origin_messages=origin_messages)]))

async def retrieveMemoriesWithContext(message: str, memoriesToRetrieve: int, contextSize: int):
    memories = await queryMemory(message, memoriesToRetrieve)
    memoriesWithContext = []
    for memory in memories:
        memoriesWithContext.append(getMemoryContext(memory.insertionOrdinal, contextSize))

    return memoriesWithContext

# returns a list of memories that are similar to the query
async def queryMemory(toSearch: str, limit: int) -> list:
    embedding = await getTextEmbedding(toSearch)
    embedding = np.array(embedding, dtype=float)
    # everything is ignored except the embedding field
    query = MemoryMessage(text='', insertionOrdinal=0, embedding=embedding, origin_messages='')
    results, scores = similarityIndex.find(query, limit=limit, search_field='embedding')

    # reject results below the similarity threshold based on the scores returned by the search
    results = [result for result, score in zip(results, scores) if score > similarity_threshold]

    return results

# retrieves a 'context' around the memory at the given ordinal, including the memory at the given ordinal
def getMemoryContext(memoryOrdinal: int, maxDistance: int):
    query = {
        '$and': [{'insertionOrdinal': {'$lte': memoryOrdinal+maxDistance}}, {'insertionOrdinal': {'$gte': memoryOrdinal-maxDistance}}]
    }

    results = similarityIndex.filter(query, limit=maxDistance*2+1)

    # sort results by insertionOrdinal
    results.sort(key=lambda x: x.insertionOrdinal)

    return results

async def getTextEmbedding(text: str) -> List[float]:
    return (await client.embeddings.create(input=text, model="text-embedding-ada-002")).data[0].embedding