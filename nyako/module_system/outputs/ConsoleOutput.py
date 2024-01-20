from EventTopics import Topics

class ConsoleOutput:
    @classmethod
    async def create(self, event_bus, listen_topic):
        self = ConsoleOutput()
        self.tag = "console"
        self.event_bus = event_bus
        stateUpdate = Topics.OutputStateUpdate(self.tag, True)
        await self.event_bus.publish(Topics.System.OUTPUT_STATE, stateUpdate)
        
        self.event_bus.subscribe(self.onMessage, listen_topic)

        return self

    async def onMessage(self, message: str):
        print("\n" + message)