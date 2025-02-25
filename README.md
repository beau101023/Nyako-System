# Nyako-System

Nyako-System is a programming framework designed for developers to create their own AI conversation systems. It is built using a modular architecture, allowing developers to link together various components to build a customized AI system. The framework leverages design patterns such as the pipe system and event bus to facilitate communication and data flow between different modules.

## Purpose

The primary purpose of Nyako-System is to provide a flexible and extensible platform for building AI-driven conversation systems. By using Nyako-System, developers can create sophisticated AI applications that can handle voice and text inputs, process them using natural language processing (NLP) models, and generate appropriate responses. The modular design ensures that developers can easily add, remove, or modify components to suit their specific needs.

## Modules

Nyako-System is composed of various modules that can be linked together to create a customized AI conversation system. These modules are categorized into:

### Core Modules

Core modules are essential components that manage the overall operation of the system. Examples include:

- **[TaskManager](TaskManager.py)**: Manages and runs all asynchronous tasks in the system.
- **[DiscordClientRunner](pipesys/core/DiscordClientRunner.py)**: Handles the Discord client for communication with Discord servers.
- **[AdminPanel](pipesys/core/AdminPanel.py)**: Provides a graphical user interface for managing the system.

### Input Modules

Input modules handle different types of input data, such as voice or text. Examples include:

- **[DiscordVoiceInput](pipesys/inputs/discord_voice_input/DiscordVoiceInput.py)**: Captures voice data from a Discord voice channel and processes it using a speech-to-text transcriber.
- **[DiscordInput](pipesys/inputs/DiscordInput.py)**: Handles text input from Discord channels.
- **[ConsoleInput](pipesys/inputs/ConsoleInput.py)**: Allows input directly through the console.

### Processing Modules

Processing modules perform various tasks on the input data, such as chunking messages, querying LLMs, and routing messages to appropriate outputs. Examples include:

- **[RealtimeMessageChunker](pipesys/processors/RealtimeMessageChunker.py)**: Accumulates messages over a time period and sends them as a batch to the next processor.
- **[ConversationSessionProcessor](pipesys/processors/ConversationSessionProcessor.py)**: Queries the LLM and manages its conversation history.
- **[MessageRouter](pipesys/processors/MessageRouter.py)** (Deprecated): Routes messages to output modules based on tagging.

### Output Modules

Output modules generate responses and deliver them to the appropriate destinations. Examples include:

- **[DiscordVoiceOutput](pipesys/outputs/DiscordVoiceOutput.py)**: Converts text to speech and plays it in a Discord voice channel.
- **[FileLogger](pipesys/outputs/FileLogger.py)**: Logs messages to a file.
- **[PipelineMonitor](pipesys/outputs/PipelineMonitor.py)**: Monitors and logs events to the console.

## Example Usage

See **[the usage template](usage_template.py)** for an example configuration of a full voice-based AI assistant that communicates via Discord.

By using Nyako-System, developers can easily build and customize their own AI conversation systems to suit their specific needs.

## Further Reading

If you're a developer or a power user, read **[the docs](docs)**.