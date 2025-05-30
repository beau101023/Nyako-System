import asyncio

from discord import Client, TextChannel, VoiceChannel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from event_system import EventBusSingleton
from event_system.events.Audio import AudioDirection, AudioType, VolumeUpdatedEvent
from event_system.events.Discord import (
    BotReadyEvent,
    TextChannelConnectedEvent,
    VoiceChannelConnectedEvent,
)
from event_system.events.Pipeline import MessageEvent
from event_system.events.System import (
    CommandAvailabilityEvent,
    CommandEvent,
    CommandType,
    StartupEvent,
    StartupStage,
    TaskCreatedEvent,
)
from pipesys import MessageSource, Pipe


class AdminPanel(Pipe):
    def __init__(self, listen_to: MessageSource):
        super().__init__()

        self.default_volume = 20

        self.window = QMainWindow()

        self.window.setWindowTitle("Admin Panel")

        main_panel = QWidget(self.window)
        self.window.setCentralWidget(main_panel)

        layout = QHBoxLayout()
        main_panel.setLayout(layout)

        layout.addWidget(self.create_left_panel())
        layout.addWidget(self.create_right_panel())

        self.create_text_display()

        self.subscribe_to_message_sources(listen_to, self.on_message)

    @classmethod
    async def create(cls, listen_to: MessageSource) -> "AdminPanel":
        self = AdminPanel(listen_to)

        task = asyncio.create_task(self.run_admin_panel())
        await EventBusSingleton.publish(TaskCreatedEvent(task, "Admin Panel"))

        EventBusSingleton.subscribe(CommandEvent(CommandType.STOP), self.on_stop)
        EventBusSingleton.subscribe(BotReadyEvent, self.update_discord_control_panel)
        EventBusSingleton.subscribe(StartupEvent(StartupStage.WARMUP), self.publish_volume_defaults)

        return self

    def create_right_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout()
        panel.setLayout(layout)

        self.right_layout = layout

        return panel

    def create_left_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout()
        panel.setLayout(layout)
        self.create_command_enablers(layout)
        self.create_command_buttons(layout)
        self.create_volume_sliders(layout)

        return panel

    def update_discord_control_panel(self, event: BotReadyEvent):
        if(not isinstance(event.client, Client)):
            return
        
        channels = event.client.get_all_channels()

        channels = [
            channel for channel in channels if isinstance(channel, (TextChannel, VoiceChannel))
        ]

        for channel in channels:
            if isinstance(channel, VoiceChannel):
                chl_type_str = "Voice: "
            elif isinstance(channel, TextChannel):
                chl_type_str = "Text: "
            else:
                continue

            # Create a label for the channel
            label = QLabel(chl_type_str + channel.name)

            # Create a button for the channel
            button = QPushButton("Connect")
            button.clicked.connect(lambda checked=False, ch=channel: self.connect_to_channel(ch))

            # Add the label and button to the layout
            self.right_layout.addWidget(label)
            self.right_layout.addWidget(button)

    def connect_to_channel(self, channel: TextChannel | VoiceChannel):
        asyncio.create_task(self._connect_and_publish(channel))

    async def _connect_and_publish(self, channel: TextChannel | VoiceChannel):
        if isinstance(channel, VoiceChannel):
            # connect to channel
            client = await channel.connect()
            await EventBusSingleton.publish(VoiceChannelConnectedEvent(client))

        if isinstance(channel, TextChannel):
            await EventBusSingleton.publish(TextChannelConnectedEvent(channel))

    def create_text_display(self):
        self.text_display_window = QMainWindow()
        self.text_display_window.setBaseSize(800, 600)
        self.text_display_window.setWindowTitle("Text Display")

        self.text_display = QLabel(self.text_display_window)
        self.text_display.setWordWrap(True)
        self.text_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text_display.setFont(QFont("Arial", 16))

        self.text_display_window.setCentralWidget(self.text_display)

    def update_text_display(self, text: str):
        self.text_display.setText(text)

        # Resize the label to fit the text
        self.text_display.adjustSize()

        # Resize the window to fit the label
        self.text_display_window.adjustSize()

    def create_volume_sliders(self, layout: QVBoxLayout):
        self.sliders: list[QSlider] = []

        for audio_type in AudioType:
            for audio_dir in AudioDirection:
                # Create a label for the slider
                label = QLabel(f"{audio_type.name} {audio_dir.name}")
                layout.addWidget(label)

                # Create the slider
                slider = QSlider(Qt.Orientation.Horizontal)
                self.sliders.append(slider)
                slider.setMinimum(0)
                slider.setMaximum(100)
                slider.setValue(self.default_volume)
                # make sure to update the system with the default values
                slider.valueChanged.connect(
                    lambda value, audio_type=audio_type, audio_dir=audio_dir: self.volume_updated(
                        value, audio_type, audio_dir
                    )
                )
                layout.addWidget(slider)

                mute_checkbox = QCheckBox("Mute")
                mute_checkbox.stateChanged.connect(
                    lambda state, slider=slider: self.mute_volume(state, slider)
                )
                layout.addWidget(mute_checkbox)

    def publish_volume_defaults(self, event: StartupEvent):
        for audio_type in AudioType:
            for audio_dir in AudioDirection:
                self.volume_updated(self.default_volume, audio_type, audio_dir)

    def mute_volume(self, state, slider: QSlider):
        if state == Qt.CheckState.Checked:
            # Store the current value and set the slider to 0
            slider.stored_value = slider.value()
            slider.setValue(0)
            slider.setEnabled(False)
        else:
            # Restore the slider's value
            slider.setValue(slider.stored_value)
            slider.setEnabled(True)

    def create_command_enablers(self, layout: QVBoxLayout):
        for command_type in CommandType:
            checkbox = QCheckBox(f"{command_type.name} enabled")
            checkbox.stateChanged.connect(
                lambda state, command_type=command_type: self.toggle_command_access(
                    state, command_type
                )
            )
            layout.addWidget(checkbox)

    def create_command_buttons(self, layout: QVBoxLayout):
        for command_type in CommandType:
            button = QPushButton(command_type.name)
            button.clicked.connect(
                lambda _, command_type=command_type: self.trigger_command(command_type)
            )
            layout.addWidget(button)

    def volume_updated(self, value, audio_type, audio_dir):
        # Handle volume update here
        asyncio.create_task(
            EventBusSingleton.publish(VolumeUpdatedEvent(float(value) / 100, audio_type, audio_dir))
        )

    def toggle_command_access(self, state, command_type):
        # Handle command access toggle here
        asyncio.create_task(
            EventBusSingleton.publish(
                CommandAvailabilityEvent(command_type, state == Qt.CheckState.Checked)
            )
        )

    def trigger_command(self, command_type):
        # Handle command trigger here
        asyncio.create_task(EventBusSingleton.publish(CommandEvent(command_type)))

    def on_message(self, event: MessageEvent):
        if(not isinstance(event.message, str)):
            return
        
        self.update_text_display(event.message)

    async def run_admin_panel(self):
        self.window.show()
        self.text_display_window.show()

    async def on_stop(self, event: CommandEvent):
        self.window.close()
        self.text_display_window.close()


if __name__ == "__main__":
    import sys

    import qasync
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    loop = qasync.QEventLoop(app)

    asyncio.set_event_loop(loop)

    panel = AdminPanel(listen_to=MessageEvent)
    panel.window.show()
    panel.text_display_window.show()

    panel.update_text_display(
        "HIHIHIHIHIHIHIHIHIHIHIHIHIHIHIHIHIHIHIHIHIHIHIHIHIHIHIHIHIHIHIHIHIHIHIHIHIHIHIHI"
    )

    loop.run_forever()
