import re

from event_system import EventBusSingleton
from pipesys import Pipe

from params import debug_mode

from event_system.events.Pipeline import MessageEvent, OutputAvailabilityEvent, SystemOutputType, OutputRoutingEvent
from event_system.events.System import CommandEvent, CommandAvailabilityEvent, CommandType
from event_system.events.LLMOutput import InvalidTagEvent, InactiveOutputEvent, InactiveCommandEvent, NoTagsEvent

class MessageRouter(Pipe):
    def __init__(self, listen_to: Pipe):
        self.active_outputs: set[SystemOutputType] = set()
        self.active_commands: set[CommandType] = set()
        EventBusSingleton.subscribe(OutputAvailabilityEvent, self.onOutputStateChanged)
        EventBusSingleton.subscribe(CommandAvailabilityEvent, self.onCommandStateChanged)
        EventBusSingleton.subscribe(MessageEvent(sender=listen_to), self.onMessage)

    async def onMessage(self, event: MessageEvent):
        """
        The MessageRouter class expects a message consisting of n parts of the format [output_type] message.\
        """

        message = event.message

        # discard if message is none, empty, or only whitespace
        if message == None or message.strip() == "":
            return

        # Split the message by tag.
        parts = self.splitByTag(message)

        # Find the index of the first valid tag
        first_tag_index = self.get_first_tag_in_list(parts)

        # If there is no valid tag, send an error
        if first_tag_index is None:
            await EventBusSingleton.publish(NoTagsEvent())
            return

        # Remove elements before the first valid tag
        parts = parts[first_tag_index:]

        # Parse out all tags and messages and handle them
        await self.handle_tagged_list(parts)

    async def handle_tagged_list(self, parts):
        i: int = 0
        while i < len(parts):
            # If i doesn't point to a tag, continue
            if not self.is_tag(parts[i]):
                i += 1
                continue

            tag = parts[i].strip()[1:-1].lower()

            # If `i` is a command, handle it
            if CommandType.fromString(tag):
                await self.handle_command_tag(tag)
                i += 1
                continue

            # If we're at the end of parts and there's a non-command tag, ignore it
            if i == len(parts) - 1:
                i += 1
                continue

            # If `i` is a valid output tag but it's followed by another tag, ignore it
            if SystemOutputType.fromString(tag) and self.is_tag(parts[i + 1]):
                i += 1
                continue

            # If `i` is a valid output tag and it's followed by a non-tag part, handle it
            if SystemOutputType.fromString(tag):
                message = parts[i+1]
                await self.handle_output_tag(tag, message)
                i += 2
                continue

            # If `i` is an invalid but well-formed tag, raise invalidtagevent
            await EventBusSingleton.publish(InvalidTagEvent(tag))

    async def handle_command_tag(self, tag: str) -> None:
        command = CommandType.fromString(tag)
        if command == None:
            await EventBusSingleton.publish(InvalidTagEvent(tag))
        elif command in self.active_commands:
            await EventBusSingleton.publish(CommandEvent(command))
        else:
            await EventBusSingleton.publish(InactiveCommandEvent(command))

    async def handle_output_tag(self, tag: str, message: str) -> None:
        """
        Handles a message with a valid output tag.

        Parameters:
        tag (str): the tag to handle
        message (str): the message to handle
        """
        output_types: list[SystemOutputType]|None = SystemOutputType.fromString(tag)
        if output_types == None:
            await EventBusSingleton.publish(InvalidTagEvent(tag))
            return
        
        for output_type in output_types:
            if output_type in self.active_outputs:
                if debug_mode:
                    await EventBusSingleton.publish(OutputRoutingEvent(message, self, SystemOutputType.ALL))
                else:
                    await EventBusSingleton.publish(OutputRoutingEvent(message, self, output_type))
            else:
                await EventBusSingleton.publish(InactiveOutputEvent(message, output_type))

    def get_first_tag_in_list(self, list: list[str]) -> int|None:
        """
        Returns the index of the first valid tag in a list of strings.

        Parameters:
        list (list[str]): the list to search
        """
        for i, part in enumerate(list):
            if self.is_tag(part):
                return i
        return None
    
    def is_tag(self, candidate: str) -> bool:
        """
        Returns whether a string is a tag.

        Parameters:
        candidate (str): the string to check
        """
        return not re.match(r'\[.*?\]', candidate) == None

    def splitByTag(self, message: str) -> list[str]:
        """
        Splits a message into a list[str] of the format [tag, message, tag, message, ...]
            when the initial message is of the form `[tag] message [tag] message`.
        
        Parameters:
        message (str): the message to split
        """
        return re.split(r'(\[.*?\])', message)

    async def onOutputStateChanged(self, event: OutputAvailabilityEvent):
        if event.output_available:
            self.active_outputs.add(event.output_type)
        else:
            self.active_outputs.remove(event.output_type)

    async def onCommandStateChanged(self, event: CommandAvailabilityEvent):
        if event.command_available:
            self.active_commands.add(event.command_type)
        else:
            self.active_commands.remove(event.command_type)