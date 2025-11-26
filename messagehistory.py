class MessageHistory:
    def __init__(self):
        self.messages = []

    def push_system_message(self, message):
        self.messages.append({"role": "system", "content": message})

    def push_user_message(self, message):
        self.messages.append({"role": "user", "content": message})

    def push_assistant_message(self, message):
        self.messages.append({"role": "assistant", "content": message})

    def pop(self, times=1):
        for i in range(times):
            self.messages.pop()
