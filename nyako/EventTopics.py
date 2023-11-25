from dataclasses import dataclass

class Topics:

    class Pipeline:
        USER_INPUT = 'user_input'
        PRIORITY_INPUT = 'priority_input'
        CHUNKER = 'message_chunker'
        CONVERSATION_SESSION_REPLY = 'conversation_session_processor'

    @dataclass
    class SpeakingStateUpdate:
        starting: bool = False
        ending: bool = False

    class TTS:
        SPEAKING_STATE = 'TTS_speaking_state'

    class Router:
        STOP = 'message_router[stop]'
        LISTENING = 'message_router[listening]'
        SLEEP = 'message_router[sleep]'
        VOICE = 'message_router[voice]'
        CONSOLE = 'message_router[console]'
        DISCORD = 'message_router[discord]'
        ERROR = 'message_router_error'

    @dataclass
    class OutputStateUpdate:
        tag: str
        output_active: bool

    class Discord:
        LISTENING_CHANNEL_SET = 'discord_listening_channel_set'

    class System:
        OUTPUT_STATE = 'output_state'
        TASK_CREATED = 'task_created'
        WARMUP = 'system_pre_link'
        STOP = 'system_stop'
        SLEEP = 'system_sleep'
        WAKE = 'system_wake'