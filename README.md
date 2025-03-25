# Nyako-System 🐱

Nyako-System is a Python framework for creating AI chatbots. It provides a modular library of pipeline components for connecting inputs and outputs to an LLM. It also provides several components for intermediate processing stages.

## Capabilities

Using Nyako-System, developers can create AI applications that handle voice and text inputs, process them using language models, and output responses in voice and text.

Nyako-System supports
- 💬 Voice output with [MeloTTS](https://github.com/myshell-ai/MeloTTS)
- 👂 Voice input with [Whisper](https://github.com/openai/whisper) and [Faster Whisper](https://github.com/SYSTRAN/faster-whisper)
- 👂💬 Discord voice and text chat via extensions to [Pycord](https://github.com/Pycord-Development/pycord)


- 💬💬 [Real-time input segmentation](/pipesys/processors/RealtimeMessageChunker.py) for natural multi-user conversations
- 💻 Text chat via the console

## Demos

(Coming soon!)

## Example Usage

See **[the usage template](usage_template.py)** for an example configuration of a chatbot that speaks over Discord.

## Further Reading

If you're a developer, read **[the docs](docs)**. For an introductory guide on using Nyako-System, see **[the configuration guide](docs/CONFIGURING.md)**