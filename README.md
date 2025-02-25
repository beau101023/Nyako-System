# Nyako-System
Nyako-System is a programming framework designed for developers to create their own AI conversation systems. It is built using a modular architecture, allowing developers to link together various components to build a customized AI system. The framework leverages design patterns such as the pipe system and event bus to facilitate communication and data flow between different modules.

## Purpose
The primary purpose of Nyako-System is to provide a flexible and extensible platform for building AI-driven conversation systems. By using Nyako-System, developers can create sophisticated AI applications that can handle voice and text inputs, process them using natural language processing (NLP) models, and generate appropriate responses. The modular design ensures that developers can easily add, remove, or modify components to suit their specific needs.

## General Architecture
Nyako-System is built around two key design patterns: the pipe system and the event bus. These patterns enable efficient communication and data flow between different modules in the system.

## Pipe System
The pipe system is a design pattern that allows data to flow through a series of processing stages, or "pipes." Each pipe is responsible for a specific task, such as input handling, message processing, or output generation. By chaining together multiple pipes, developers can create complex data processing pipelines.

In Nyako-System, pipes are implemented as classes that inherit from the Pipe abstract base class. Each pipe can subscribe to specific events and process the data associated with those events. The processed data is then passed along to the next pipe in the pipeline.

## Event Bus
The event bus is a design pattern that facilitates communication between different components in a system. It acts as a central hub where events are published and subscribed to by various modules. When an event is published, all modules that have subscribed to that event are notified and can take appropriate action.

In Nyako-System, the event bus is implemented using the EventBusSingleton class. Modules can subscribe to specific events by registering callback functions with the event bus. When an event is published, the event bus invokes the registered callback functions, allowing modules to respond to the event.

## Modules
Nyako-System is composed of various modules that can be linked together to create a customized AI conversation system. These modules are categorized into core modules, input modules, processing modules, and output modules.

## Core Modules
Core modules are essential components that manage the overall operation of the system. Examples include:

TaskManager: Manages and runs all asynchronous tasks in the system.
DiscordClientRunner: Handles the Discord client for communication with Discord servers.
AdminPanel: Provides a graphical user interface for managing the system.

## Input Modules
Input modules handle different types of input data, such as voice or text. Examples include:

DiscordVoiceInput: Captures voice data from a Discord voice channel and processes it using a speech-to-text transcriber.
PipelineMonitor: Monitors and logs input events for debugging and analysis.

## Processing Modules
Processing modules perform various tasks on the input data, such as chunking messages, querying NLP models, and routing messages to appropriate outputs. Examples include:

RealtimeMessageChunker: Accumulates messages over a time period and sends them as a batch to the next processor.
ConversationSessionProcessor: Queries the NLP model and processes the conversation context.
MessageRouter: Routes messages to output modules based on tagging.

## Output Modules
Output modules generate responses and deliver them to the appropriate destinations. Examples include:

DiscordVoiceOutput: Converts text to speech and plays it in a Discord voice channel.
FileLogger: Logs messages to a file for record-keeping and analysis.
PipelineMonitor: Monitors and logs output events for debugging and analysis.

## Example Usage
The following example demonstrates how to create a simple AI conversation system using Nyako-System:

In this example, various modules are created and linked together to form a complete AI conversation system. The TaskManager runs all asynchronous tasks, while the DiscordClientRunner handles the Discord client. Input modules capture voice data from Discord, processing modules handle message chunking and conversation processing, and output modules generate and deliver responses.

By using Nyako-System, developers can easily build and customize their own AI conversation systems to suit their specific needs.