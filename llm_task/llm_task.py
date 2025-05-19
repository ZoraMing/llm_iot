# task_processor.py 主处理模块
import json
import asyncio
import requests
from openai import AsyncOpenAI
from llm_task_prompts import system_prompt_parser, system_prompt_dispatcher, system_prompt_validator
from llm_task_tools import devices_info

class HomeAutomationProcessor:
    def __init__(self):
        self.aclient = AsyncOpenAI(
            api_key="sk-8e1eb5aaeb824c02a3a561f3c0c33c47",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        self.used_model = "qwen-plus"
        self.api_endpoint = "http://localhost:5000/api/control"

    async def parse_instruction(self, user_input: str) -> dict:
        """第一阶段：指令解析"""
        response = await self.aclient.chat.completions.create(
            model=self.used_model,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt_parser.replace(
                        "{devices_info}", json.dumps(devices_info))
                },
                {"role": "user", "content": user_input}
            ],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)

    async def dispatch_task(self, task: dict) -> dict:
        """第二阶段：任务分发"""
        response = await self.aclient.chat.completions.create(
            model=self.used_model,
            messages=[
                {"role": "system", "content": system_prompt_dispatcher},
                {"role": "user", "content": json.dumps(task)}
            ],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)

    async def validate_command(self, command: dict) -> dict:
        """第三阶段：指令校验"""
        response = await self.aclient.chat.completions.create(
            model=self.used_model,
            messages=[
                {"role": "system", "content": system_prompt_validator},
                {"role": "user", "content": json.dumps(command)}
            ],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)

    async def execute_commands(self, commands: list) -> list:
        """执行设备控制"""
        results = []
        for cmd in commands:
            try:
                response = requests.post(
                    self.api_endpoint,
                    json=cmd,
                    timeout=5
                )
                results.append({
                    "status": response.status_code,
                    "response": response.json()
                })
            except Exception as e:
                results.append({"error": str(e)})
        return results

    async def full_process(self, user_input: str) -> dict:
        """完整处理流程"""
        # 第一阶段解析
        parsed = await self.parse_instruction(user_input)
        recall_msg = parsed.get('recall_msg', '')
        print("recall_msg: ",recall_msg)
        
        # 第二阶段并行处理
        tasks = parsed.get('task_list', [])
        dispatch_coros = [self.dispatch_task(task) for task in tasks]
        dispatched = await asyncio.gather(*dispatch_coros)

        # 第三阶段校验
        validate_coros = [self.validate_command(cmd) for cmd in dispatched]
        validated = await asyncio.gather(*validate_coros)

        # 提取有效指令
        final_commands = [
            v.get('corrected', v) if not v['valid'] else v 
            for v in validated
        ]

        # 执行控制
        execution_results = await self.execute_commands(final_commands)

        return {
            "recall_msg": recall_msg,
            "commands": final_commands,
            "execution_results": execution_results
        }

# 使用示例
async def main():
    use_input = "好暗啊,帮我打开客厅灯"
    use_input = input("请输入指令: ")

    processor = HomeAutomationProcessor()
    result = await processor.full_process(use_input)
    
    print("最终回复:", result['recall_msg'])
    print("执行结果:", json.dumps(result['execution_results'], indent=2))

if __name__ == "__main__":
    asyncio.run(main())