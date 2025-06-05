import asyncio

from event_system.EventBus import EventBus
from event_system.events.System import CommandEvent, CommandType


def test_eventbus_filtering():
    bus = EventBus()
    calls: list[CommandEvent] = []

    def handler(event: CommandEvent):
        calls.append(event)

    # Subscribe to only STOP commands
    bus.subscribe(CommandEvent(CommandType.STOP), handler)

    # Publish non-matching events
    asyncio.run(bus.publish(CommandEvent(CommandType.LISTEN)))
    asyncio.run(bus.publish(CommandEvent(CommandType.SLEEP)))

    assert calls == []

    # Publish matching event
    asyncio.run(bus.publish(CommandEvent(CommandType.STOP)))

    assert len(calls) == 1
    assert calls[0].command is CommandType.STOP
