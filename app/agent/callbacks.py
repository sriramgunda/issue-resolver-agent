from langchain_core.callbacks import BaseCallbackHandler


class ToolTrackingCallback(BaseCallbackHandler):
    def __init__(self):
        self.steps = []

    def on_tool_start(self, serialized, input_str, **kwargs):
        self.steps.append({
            "step": serialized.get("name"),
            "status": "started",
            "details": input_str
        })

    def on_tool_end(self, output, **kwargs):
        self.steps[-1]["status"] = "completed"
        self.steps[-1]["details"] = str(output)