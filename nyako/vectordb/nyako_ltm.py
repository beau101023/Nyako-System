from docarray.index import HnswDocumentIndex
from docarray import DocList
from vectordb.data_schema import MemoryMessage
from openai import Embedding
from params import API_KEY
from params import similarity_threshold

# workspace path
similarityIndex = HnswDocumentIndex[MemoryMessage](work_dir='./vectordb/workspace_path')

def insertToMemory(summary: str, origin_messages: str):
    embedding = Embedding.create(api_key=API_KEY, input=origin_messages, model="text-embedding-ada-002")['data'][0]['embedding']
    similarityIndex.index(DocList[MemoryMessage]([MemoryMessage(text=summary, insertionOrdinal=similarityIndex.num_docs(), embedding=embedding, origin_messages=origin_messages)]))

def retrieveMemoriesWithContext(message: str, memoriesToRetrieve: int, contextSize: int):
    memories = queryMemory(message, memoriesToRetrieve)
    memoriesWithContext = []
    for memory in memories:
        memoriesWithContext.append(getMemoryContext(memory.insertionOrdinal, contextSize))

    return memoriesWithContext

# returns a list of memories that are similar to the query
def queryMemory(toSearch: str, limit: int):
    embedding = Embedding.create(api_key=API_KEY, input=toSearch, model="text-embedding-ada-002")['data'][0]['embedding']
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