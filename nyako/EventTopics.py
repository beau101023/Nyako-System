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

    @dataclass
    class VolumeUpdate:
        volume: float

    class TTS:
        SPEAKING_STATE = 'TTS_speaking_state'

    class SpeechToText:
        USER_SPEAKING_STATE = 'speech_to_text_speaking_state'

    class Router:
        SHUTDOWN = 'message_router[stop]'
        LISTEN = 'message_router[listen]'
        SLEEP = 'message_router[sleep]'
        VOICE = 'message_router[voice]'
        CONSOLE = 'message_router[console]'
        DISCORD = 'message_router[discord]'
        ERROR = 'message_router_error'

        class Outputs:
            CONSOLE = 'message_router[console]'
            DISCORD = 'message_router[discord]'
            VOICE = 'message_router[voice]'

    @dataclass
    class OutputStateUpdate:
        tag: str
        output_active: bool

    class Discord:
        LISTENING_CHANNEL_SET = 'discord_listening_channel_set'

    class Audio:
        INPUT_VOLUME_UPDATE = 'audio_input_volume_update'
        OUTPUT_VOLUME_UPDATE = 'audio_output_volume_update'

    class System:
        OUTPUT_STATE = 'output_state'
        TASK_CREATED = 'task_created'
        WARMUP = 'system_pre_link'
        STOP = 'system_stop'
        SLEEP = 'system_sleep'
        WAKE = 'system_wake'
