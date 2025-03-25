# Nyako-System User Guide

## Pipe System

Nyako-System's [pipe system](/pipesys/) is a collection of modules that can be linked together to create an AI conversation system.

### Connecting Modules

To connect modules to data sources, use the `listen_to` parameter of the module's `create` method.

In this example, we give the `RealtimeMessageChunker` instance a class name- `UserInputEvent` to tell it to receive all messages of type `UserInputEvent`.

```python
message_chunker = await RealtimeMessageChunker.create(
    listen_to=UserInputEvent, processor_delay=0.2
)
```

In this example, we give the `ConversationSessionProcessor` instance the `message_chunker` instance we just created to tell it to receive all messages that the `message_chunker` instance sends.

```python
conversation_session_processor = await ConversationSessionProcessor.create(
    listen_to=message_chunker
)
```

## Module List

### [Input Modules](/pipesys/inputs/)

Input modules are the 'entrance points' in a system of pipes. They take input and deliver it to pipes they connect to.

- **[DiscordVoiceInput](/pipesys/inputs/discord_voice_input/DiscordVoiceInput.py)**: Captures and transcribes audio from a Discord voice channel.
- **[DiscordInput](/pipesys/inputs/DiscordInput.py)**: Handles text input from Discord channels.
- **[ConsoleInput](/pipesys/inputs/ConsoleInput.py)**: Allows input directly through the console.
- **[SpeechToTextInput](/pipesys/inputs/SpeechToTextInput.py)**: Captures and transcribes audio from the system's microphone.

### [Processing Modules](/pipesys/processors/)

Processing modules perform intermediate processing steps on, such as segmenting groups of messages and querying LLMs.

- **[RealtimeMessageChunker](/pipesys/processors/RealtimeMessageChunker.py)**: Accumulates messages over a time period and sends them as a batch to the next processor.
- **[ConversationSessionProcessor](/pipesys/processors/ConversationSessionProcessor.py)**: Queries the LLM and manages its conversation history.
- **[MessageRouter](/pipesys/processors/MessageRouter.py)** (Deprecated): Routes messages to output modules based on tagging.

### [Output Modules](/pipesys/outputs/)

Output modules are the 'exit points' in a system of pipes. They take messages from the pipes they listen to and produce some user-facing output.

- **[DiscordVoiceOutput](/pipesys/outputs/DiscordVoiceOutput.py)**: Converts `MessageEvent`s to speech and plays that speech in a Discord voice channel.
- **[FileLogger](/pipesys/outputs/FileLogger.py)**: Logs `MessageEvent`s to a file named with the current date and time.
- **[PipelineMonitor](/pipesys/outputs/PipelineMonitor.py)**: Prints messages for debugging, without 
- **[ConsoleOutput](/pipesys/outputs/ConsoleOutput.py)**: Outputs messages to the console.
- **[DiscordOutput](/pipesys/outputs/DiscordOutput.py)**: Sends messages to a Discord text channel.
- **[TextToSpeechOutput](/pipesys/outputs/TextToSpeechOutput.py)**: Converts text to speech and plays it through the system's speakers.
- **[VisualOutput](/pipesys/outputs/VisualOutput.py)**: A window that displays 'emotion images' based on sentiment analysis of the input text.

### [Core Modules](/pipesys/core/)

Core modules coordinate multiple other modules in the system, usually directly via the [Event Bus](/event_system/EventBusSingleton.py) rather than via the pipe system.

- **[DiscordClientRunner](/pipesys/core/DiscordClientRunner.py)**: Handles the Discord client for communication with Discord servers.
- **[AdminPanel](/pipesys/core/AdminPanel.py)**: A GUI for managing the system at runtime.
- **[SleepManager](/pipesys/core/SleepManager.py)**: Allows the system to enter an inactive state. The system can be awakened afterwards by user input.