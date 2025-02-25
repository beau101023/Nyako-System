# Nyako-System Technical Overview

## General Architecture

Nyako-System is built around two key design patterns:

### Pipe System

The pipe system is a design pattern that allows data to flow through a series of processing stages, or "pipes." Each pipe is responsible for a specific task, such as input handling, message processing, or output generation. By chaining together multiple pipes, developers can create complex data processing pipelines.

In Nyako-System, pipes are implemented as classes that inherit from the [Pipe abstract base class](/pipesys/Pipe.py). Each pipe can subscribe to other pipes to process the data they output. The processed data is then passed along to the next pipe in the pipeline.

### Event Bus

The event bus is a design pattern that facilitates communication between different components in a system. It acts as a central hub where events are published and subscribed to by various modules. When an event is published, all modules that have subscribed to that event are notified and can take appropriate action.

In Nyako-System, the event bus is implemented using the [EventBusSingleton class](/event_system/EventBusSingleton.py). Modules can subscribe to specific events by registering callback functions with the event bus. When an event is published, the event bus invokes the registered callback functions, allowing modules to respond to the event.

#### Event Bus Usage

The Event Bus system enables decoupled communication between components. Here's how to use it:

**Subscribing to Events**

You can subscribe to events in two ways:

1. Subscribe to a specific event type with exact field values:

```python
# Subscribe to a VolumeUpdatedEvent for Discord input
EventBusSingleton.subscribe(
    VolumeUpdatedEvent(None, AudioType.DISCORD, AudioDirection.INPUT),
    instance.on_input_volume_update
)
```

2. Subscribe to all events of a certain type:

```python
# Subscribe to all BotReadyEvent instances
EventBusSingleton.subscribe(BotReadyEvent, instance.on_bot_ready)
```

**How Event Filtering Works**

The Event Bus uses a sophisticated filtering system:
- If a field value in the event filter is `None`, it doesn't filter on that field
- If a field value is a type, the corresponding event's field must be an instance of that type
- Otherwise, the event's field must match the filter value exactly

**Publishing Events**

To publish an event that subscribers can react to:

```python
# Create and publish an event
volume_event = VolumeUpdatedEvent(0.75, AudioType.DISCORD, AudioDirection.OUTPUT)
await EventBusSingleton.publish(volume_event)
```

**Creating Custom Events**

Define your own events by extending the base Event class:

```python
class CustomEvent(Event):
    def __init__(self, message: str, priority: int):
        self.message = message
        self.priority = priority
```

## Additional Features

These files contain utility functions and helpers which serve as the building blocks of the various modules.

- **Speech Recognition**: Utilizes advanced [transcription capabilities](/Transcribers.py) for converting speech to text.
- **Text-to-Speech**: Provides [TTS functionality](/TTS.py) for generating natural-sounding speech from text.
- **Voice Activity Detection**: Implements [VAD utilities](/VAD_utils.py) to detect when users are speaking.
- **LLM Integration**: Connects with language models through the [nyako_llm module](/LLM/nyako_llm.py).
- **Vector Database**: Supports [RAG capabilities](/vectordb/RAG_utils.py) for enhanced conversational context.