from EventTopics import Topics
from EventBus import EventBus
import re

from params import debug_mode

class MessageRouter():
    event_bus: EventBus

    def __init__(self, event_bus, listen_topic=Topics.Pipeline.CONVERSATION_SESSION_REPLY):
        self.event_bus = event_bus
        self.activeOutputs = set()
        self.errorFeedbackReceivers = []
        self.event_bus.subscribe(self.onOutputStateChanged, Topics.System.OUTPUT_STATE)
        self.event_bus.subscribe(self.onMessage, listen_topic)

    async def onMessage(self, message: str):

        # Split the message by tag, capturing the tag still
        parts = re.split(r'(\[.*?\])', message)

        # Find the index of the first valid tag
        first_tag_index = next((i for i, part in enumerate(parts) if re.match(r'\[.*?\]', part)), None)

        # If there is no valid tag, send an error
        if first_tag_index is None:
            await self.all_outputs_send(message)
            return

        # Remove elements before the first valid tag
        parts = parts[first_tag_index:]

        # here, we assume that parts takes the form [tag, message, tag, message, ...]
        for i in range(0, len(parts) - 1, 2):
            # Get the tag and the message
            tag = parts[i].strip()[1:-1].lower()
            message = parts[i + 1].strip()

            # sends to all outputs except tagged. Sends before the main send to avoid getting interrupted if the shutdown command is sent
            if debug_mode:
                await self.all_outputs_except(message, tag)

            await self.send(message, tag)

    async def onOutputStateChanged(self, event: Topics.OutputStateUpdate):
        if not event.tag in self.activeOutputs and not event.output_active:
            return
        
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
            await self.sendErrorFeedback(self.nonexistentTagFeedback(tag))
            return

        if debug_mode:
            print("ROUTING MESSAGE: '" + text + "' to TOPIC: " + topic)

        await self.event_bus.publish(topic, text)

    async def all_outputs_except(self, text: str, tag: str):
        # send to every topic in router.outputs except the one specified in the tag
        for output in [output for output in dir(Topics.Router.Outputs) if not output.startswith('__') and output != tag.upper()]:
            await self.event_bus.publish(getattr(Topics.Router.Outputs, output), "[" + tag + "] " + text)

    async def all_outputs_send(self, text: str):
        # send to every topic in router.outputs except the one specified in the tag
        for output in [output for output in dir(Topics.Router.Outputs) if not output.startswith('__')]:
            await self.event_bus.publish(getattr(Topics.Router.Outputs, output), "[untagged] " + text)

    async def sendErrorFeedback(self, message):
        try:
            raise Exception(message)
        except Exception as error:
            await self.event_bus.publish(Topics.Router.ERROR, str(error))

    def getOutputTags(self):
        return [tag for tag in self.activeOutputs]

    def invalidInputFeedback(self):
        return "[system] You need to tag your messages like \"["+self.getOutputTags()[0]+"] hi, I'm nyako!\" if you want the user to see them! Available tags: [" + "], [".join(self.getOutputTags()) + "]"
    
    def nonexistentTagFeedback(self, tag: str):
        return "[system] The tag '" + tag + "' is disabled! Available tags: [" + "], [".join(self.getOutputTags()) + "]"