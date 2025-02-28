# Nyako-System 🐱

Nyako-System is a Python framework for creating AI chat systems. It provides a modular architecture of pipeline components and an object-oriented event bus, allowing developers to connect components to build a customized AI system.

## Capabilities

Using Nyako-System, developers can create AI applications that handle voice and text inputs, process them using language models, and output responses in voice and text.

Nyako-System supports
- 💬 Voice output with [MeloTTS](https://github.com/myshell-ai/MeloTTS)
- 👂 Voice input with [Whisper](https://github.com/openai/whisper) and [Faster Whisper](https://github.com/SYSTRAN/faster-whisper)
- 👂💬 Discord voice and text chat via extensions to [Pycord](https://github.com/Pycord-Development/pycord)


- 👂 [Real-time input segmentation](/pipesys/processors/RealtimeMessageChunker.py) for natural multi-user conversations
- 💻 Text chat via the console

## Demos

(Coming soon!)

## Example Usage

See **[the usage template](usage_template.py)** for an example configuration of a full voice-based AI assistant that communicates via Discord.

## Further Reading

If you're a developer, read **[the docs](docs)**. For an introductory guide on using Nyako-System, see **[the configuration guide](docs/CONFIGURING.md)**