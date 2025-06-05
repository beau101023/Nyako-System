# Nyako-System Technical Overview

## General Architecture

There are two core architectural ideas that form the backbone of the system.

### 1. Pipe System

The pipe system allows developers to connect different modules (Pipes) together. Each pipe is responsible for a single task, such as input handling, text processing, or output production.

In Nyako-System, pipes are implemented as classes that inherit from the [Pipe](/pipesys/Pipe.py) abstract base class. Each pipe can subscribe to other pipes to process the data they output. The processed data is then passed along to the next pipe in the pipeline.

#### Pipe System Usage

See [the user guide](/docs/CONFIGURING.md) for examples of connecting and configuring pipeline modules.

### 2. Event Bus

The event bus is a design pattern that facilitates communication between different components in a system. It acts as a central hub where events are published and subscribed to by various modules. When an event is published, all modules that have subscribed to that event are notified and can take appropriate action.

In Nyako-System, the event bus is implemented using the [EventBusSingleton class](/event_system/EventBusSingleton.py). Modules can subscribe to specific events by registering callback functions with the event bus. When an event is published, the event bus invokes the registered callback functions, allowing modules to respond to the event.

#### Event Bus Usage

**Subscribing to Events**

To subscribe to an event with the EventBusSingleton, pass an event instance or an event class to the subscribe method.

Examples of subscribing to events:

1. Subscribe to all events of a type by passing the class to the subscribe method.

```python
# Subscribe to all BotReadyEvents.
EventBusSingleton.subscribe(BotReadyEvent, self.on_bot_ready)
```

2. Subscribe to all events with specific attribute values by passing an instance of the event with those values to the subscribe method.

```python
# Subscribe to all CommandEvent with a CommandType of STOP
EventBusSingleton.subscribe(CommandEvent(CommandType.STOP), self.stop)
```

3. When subscribing, ignore an attribute by setting its value to `EventParameterFlag.NOT_SPECIFIED`. You will then receive events regardless of the value of the ignored attribute.

```python
# Subscribe to all VolumeUpdatedEvent with an AudioType of DISCORD, an AudioDirection of INPUT, and indicate we don't care about the value of the first parameter.
EventBusSingleton.subscribe(
    VolumeUpdatedEvent(EventParameterFlag.NOT_SPECIFIED, AudioType.DISCORD, AudioDirection.INPUT),
    self.on_input_volume_update
)
```

4. Event parameters are equal to EventParameterFlag.NOT_SPECIFIED by default, so event subscriptions can simply omit parameters they have no interest in filtering on as well.

```python
# This event subscription is equivalent to the previous one.
EventBusSingleton.subscribe(
    VolumeUpdatedEvent(audio_type = AudioType.DISCORD, audio_direction = AudioDirection.INPUT),
    self.on_input_volume_update
)
```

**Publishing Events**

To publish an event, pass an event instance to the publish method. For example:

```python
volume_event = VolumeUpdatedEvent(0.75, AudioType.DISCORD, AudioDirection.OUTPUT)
await EventBusSingleton.publish(volume_event)
```

**Creating Custom Events**

You can define your own events by extending the Event base class. The Event class itself provides no functionality, it only serves as a marker that an object is an event.

```python
class CustomEvent(Event):
    def __init__(self, message: str, priority: int):
        self.message = message
        self.priority = priority
```

## Additional Features

These files contain utility functions and helpers which serve as the building blocks of various modules.

- [**Speech Recognition**](/Transcribers.py): Provides `Transcriber` objects for converting speech to text.
- [**Text-to-Speech**](/TTS.py): Provides `TextToSpeech` objects for voice synthesis.
- [**Voice Activity Detection**](/VAD_utils.py): Provides a `detectVoiceActivity` function.
- [**LLM Integration**](/LLM/nyako_llm.py): Provides a standardized API and context management for language models.
- [**Vector Database**](/vectordb/RAG_utils.py): Supports RAG capabilities.
