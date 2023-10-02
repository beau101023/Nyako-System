from docarray.index import HnswDocumentIndex
from data_schema import MemoryMessage
from openai import Embedding
from nyako_params import API_KEY

openai.api_key = API_KEY

# workspace path
similarityIndex = HnswDocumentIndex[MemoryMessage](work_dir='./nyako/vectordb/workspace_path')

def insertToMemory(message: str):
    embedding = Embedding.create(message, model="text-embedding-ada-002")['data'][0]['embedding']
    similarityIndex.index(DocList[MemoryMessage]([MemoryMessage(text=message, insertionOrdinal=similarityIndex.num_docs(), embedding=embedding)]))

def retrieveMemoriesWithContext(message: str, memoriesToRetrieve: int, contextSize: int):
    memories = queryMemory(message, memoriesToRetrieve)
    memoriesWithContext = []
    for memory in memories:
        memoriesWithContext.append(getMemoryContext(memory.insertionOrdinal, contextSize))

# returns a list of memories that are similar to the query
def queryMemory(toSearch: str, limit: int):
    embedding = Embedding.create(toSearch, model="text-embedding-ada-002")['data'][0]['embedding']
    # insertionOrdinal is ignored here
    query = MemoryMessage(text=toSearch, insertionOrdinal=0, embedding=embedding)
    results, scores = similarityIndex.find(query, limit=limit, search_field='embedding')
    return results

# retrieves a 'context' around the memory at the given ordinal, including the memory at the given ordinal
def getMemoryContext(memoryOrdinal: int, maxDistance: int):
    query = {
        '$and': [{'sID': {'$lte': memoryOrdinal+maxDistance}}, {'sID': {'$gte': memoryOrdinal-maxDistance}}]
    }

    results = similarityIndex.filter(query, limit=maxDistance*2)

    # sort results by insertionOrdinal
    results.sort(key=lambda x: x.insertionOrdinal)

    return results