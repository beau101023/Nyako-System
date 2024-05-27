import asyncio
from asyncqt import QEventLoop
from PyQt5.QtWidgets import QApplication

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QSlider, QCheckBox, QPushButton, QWidget, QLabel, QFrame
from PyQt5.QtCore import Qt

from event_system.events.Audio import AudioDirection, AudioType, VolumeUpdatedEvent
from event_system.events.System import CommandEvent, CommandType, CommandAvailabilityEvent

from event_system import EventBusSingleton

class AdminPanel(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Admin Panel")

        widget = QWidget(self)
        self.setCentralWidget(widget)

        layout = QVBoxLayout()
        widget.setLayout(layout)

        self.create_volume_sliders(layout)

        # horizontal line
        hline = QFrame()
        hline.setFrameShape(QFrame.HLine)
        hline.setFrameShadow(QFrame.Sunken)
        layout.addWidget(hline)

        self.create_command_checkboxes(layout)
        self.create_command_buttons(layout)

    def create_volume_sliders(self, layout: QVBoxLayout):
        for audio_type in AudioType:
            for audio_dir in AudioDirection:
                # Create a label for the slider
                label = QLabel(f"{audio_type.name} {audio_dir.name}")
                layout.addWidget(label)

                # Create the slider
                slider = QSlider(Qt.Orientation.Horizontal)
                slider.setMinimum(0)
                slider.setMaximum(100)
                slider.setValue(20)
                slider.valueChanged.connect(lambda value, audio_type=audio_type, audio_dir=audio_dir: self.volume_updated(value, audio_type, audio_dir))
                layout.addWidget(slider)

                mute_checkbox = QCheckBox("Mute")
                mute_checkbox.stateChanged.connect(lambda state, slider=slider: self.mute_volume(state, slider))
                layout.addWidget(mute_checkbox)

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

    def create_command_checkboxes(self, layout: QVBoxLayout):
        for command_type in CommandType:
            checkbox = QCheckBox(f"{command_type.name} enabled")
            checkbox.stateChanged.connect(lambda state, command_type=command_type: self.toggle_command_access(state, command_type))
            layout.addWidget(checkbox)

    def create_command_buttons(self, layout: QVBoxLayout):
        for command_type in CommandType:
            button = QPushButton(command_type.name)
            button.clicked.connect(lambda _, command_type=command_type: self.trigger_command(command_type))
            layout.addWidget(button)

    def volume_updated(self, value, audio_type, audio_dir):
        # Handle volume update here
        asyncio.create_task(EventBusSingleton.publish(VolumeUpdatedEvent(float(value)/100, audio_type, audio_dir)))

    def toggle_command_access(self, state, command_type):
        # Handle command access toggle here
        asyncio.create_task(EventBusSingleton.publish(CommandAvailabilityEvent(command_type, state == Qt.CheckState.Checked)))

    def trigger_command(self, command_type):
        # Handle command trigger here
        asyncio.create_task(EventBusSingleton.publish(CommandEvent(command_type)))

if __name__ == "__main__":
    app = QApplication([])
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    with loop:
        admin_panel = AdminPanel()
        admin_panel.show()
        loop.run_forever()