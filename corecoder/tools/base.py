"""所以工具的基础类"""

from abc import ABC, abstractmethod


class Tool(ABC):
    name: str  # 工具名称
    description: str  # 工具描述
    parameters: dict  # 工具参数

    # 抽象方法，子类必须实现
    @abstractmethod
    def execute(self, **kwargs) -> str:
        ...

    # OpenAI的函数调用模式的schema
    def schema(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }
