from EventTopics import Topics

class ConsoleOutput:
    """
    Outputs messages to the console.
    """

    @classmethod
    async def create(self, event_bus, listen_topic):
        """
        Creates an instance of the ConsoleOutput module.

        Parameters:
        event_bus (EventBus): the event bus to use
        listen_topic (str): the topic to listen for messages on
        """

        self = ConsoleOutput()
        self.tag = "console"
        self.event_bus = event_bus
        stateUpdate = Topics.OutputStateUpdate(self.tag, True)
        await self.event_bus.publish(Topics.System.OUTPUT_STATE, stateUpdate)
        
        self.event_bus.subscribe(self.onMessage, listen_topic)

        return self

    async def onMessage(self, message: str):
        """
        Outputs a message to the console asynchonously.
        
        Parameters:
        message (str): the message to output
        """

        print("\n" + message)