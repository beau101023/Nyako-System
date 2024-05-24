from abc import ABC

class Pipe(ABC):
    """
    Marker interface for classes which take input and give output as part of a pipeline using EventBus.
    """
    pass

class OutputPipe(Pipe):
    """
    Marker interface for a pipe which outputs using system functionality.
    """

class InputPipe(Pipe):
    """
    Marker interface for a pipe which takes input directly from system functionality.
    """