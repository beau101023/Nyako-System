from dataclasses import dataclass

class Topics:

    class Pipeline:
        SPEECH_TO_TEXT_IN = 'speech_to_text'
        CONSOLE_IN = 'console_input'
        CHUNKER = 'message_chunker'
        CONVERSATION_SESSION_REPLY = 'conversation_session_processor'

    @dataclass
    class SpeakingStateUpdate:
        starting: bool = False
        ending: bool = False

    class TTS:
        SPEAKING_STATE = 'TTS_speaking_state'

    class Router:
        VOICE = 'message_router[voice]'
        CONSOLE = 'message_router[console]'
        ERROR = 'message_router_error'

    @dataclass
    class OutputStateUpdate:
        tag: str
        output_active: bool

    class System:
        OUTPUT_STATE = 'output_state'
        TASK_CREATED = 'task_created'
        PRE_LINKING = 'system_pre_link'
        STOP = 'system_stop'