from EventTopics import Topics
from EventBus import EventBus
import re

class MessageRouter():
    event_bus: EventBus

    def __init__(self, event_bus):
        self.event_bus = event_bus
        self.activeOutputs = set()
        self.errorFeedbackReceivers = []
        self.event_bus.subscribe(self.onOutputStateChanged, Topics.System.OUTPUT_STATE)

    async def onMessage(self, message: str):

        # Split the message by tag, capturing the tag still
        parts = re.split(r'(\[.*?\])', message)

        # Find the index of the first valid tag
        first_tag_index = next((i for i, part in enumerate(parts) if re.match(r'\[.*?\]', part)), None)

        # If there is no valid tag, send an error
        if first_tag_index is None:
            await self.sendErrorFeedback(self.invalidInputFeedback())
            return

        # Remove elements before the first valid tag
        parts = parts[first_tag_index:]

        # here, we assume that parts takes the form [tag, message, tag, message, ...]
        for i in range(0, len(parts) - 1, 2):
            # Get the tag and the message
            tag = parts[i].strip()[1:-1].lower()
            message = parts[i + 1].strip()

            if message == "":
                continue

            await self.send(message, tag)

    async def onOutputStateChanged(self, event: Topics.OutputStateUpdate):
        if event.output_active:
            self.activeOutputs.add(event.tag)
        else:
            self.activeOutputs.remove(event.tag)

    async def send(self, text: str, tag: str):
        if not tag in self.activeOutputs:
            await self.sendErrorFeedback(self.nonexistentTagFeedback(tag))
            return

        topic = getattr(Topics.Router, tag.upper(), None)
        if topic is None:
            await self.sendErrorFeedback(self.invalidInputFeedback())
            return

        print("ROUTING MESSAGE: '" + text + "' to TOPIC: " + topic)

        await self.event_bus.publish(topic, text)
    
    async def sendErrorFeedback(self, message):
        await self.event_bus.publish(Topics.Router.ERROR, message)

    def getOutputTags(self):
        return [tag for tag in self.activeOutputs]

    def invalidInputFeedback(self):
        return "[system] Invalid output tag. Tags look like [tag] and must be at the beginning of your message. Available outputs: [" + "], [".join(self.getOutputTags()) + "]"
    
    def nonexistentTagFeedback(self, tag: str):
        return "[system] The tag '" + tag + "' does not exist. Available outputs: [" + "], [".join(self.getOutputTags()) + "]"