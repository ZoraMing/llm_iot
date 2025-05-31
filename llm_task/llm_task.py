import json
import asyncio
import aiohttp
from openai import AsyncOpenAI
from llm_task_prompts import system_prompt_parser, system_prompt_dispatcher, system_prompt_validator
from llm_task_tools import devices_info

API_KEY = "sk-8e1eb5aaeb824c02a3a561f3c0c33c47"
ollama_url = "http://localhost:11434/v1"
ollama_model = "qwen2.5:1.5b"

class HomeAutomationProcessor:
    def __init__(self):
        self.used_model = "qwen-plus"
        # self.used_model = ollama_model
        self.api_endpoint = "http://localhost:5000/api/control"
        self.http_session = None
        self.openai_client = None
    
    # 使用with自动关闭资源
    async def __aenter__(self):
        """进入异步上下文时初始化资源"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc, tb):
        """退出异步上下文时关闭资源"""
        await self.close()
    
    async def initialize(self):
        """异步初始化资源"""
        self.http_session = aiohttp.ClientSession()
        self.openai_client = AsyncOpenAI(
            api_key=API_KEY,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            # 本地ollama运行
            # base_url=ollama_url,
        )
    
    async def close(self):
        """安全关闭所有资源"""
        if self.http_session:
            try:
                await self.http_session.close()
            except Exception as e:
                # 忽略关闭错误，因为它们在程序结束时无害
                # 太坏了windows异步垃圾回收
                pass
            self.http_session = None

    async def parse_instruction(self, user_input: str) -> dict:
        """第一阶段：指令解析"""
        try:
            response = await self.openai_client.chat.completions.create(
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
        except Exception as e:
            print(f"解析指令时出错: {e}")
            return {
                "task_list": [],
                "recall_msg": "抱歉，我无法理解您的指令"
            }

    async def dispatch_task(self, task: dict) -> dict:
        """第二阶段：任务分发"""
        try:
            response = await self.openai_client.chat.completions.create(
                model=self.used_model,
                messages=[
                    {"role": "system", "content": system_prompt_dispatcher},
                    {"role": "user", "content": json.dumps(task)}
                ],
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"任务分发时出错: {e}")
            return {}

    async def validate_command(self, command: dict) -> dict:
        """第三阶段：指令校验"""
        try:
            response = await self.openai_client.chat.completions.create(
                model=self.used_model,
                messages=[
                    {"role": "system", "content": system_prompt_validator},
                    {"role": "user", "content": json.dumps(command)}
                ],
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"指令校验时出错: {e}")
            return {"valid": False, "errors": ["验证失败"], "corrected": command}

    async def execute_command(self, command: dict) -> dict:
        """执行单个设备控制命令"""
        if not self.http_session:
            return {"error": "HTTP session not initialized"}
        
        try:
            async with self.http_session.post(
                self.api_endpoint,
                json=command,
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                if response.status == 200:
                    return {
                        "status": response.status,
                        "response": await response.json()
                    }
                else:
                    return {
                        "status": response.status,
                        "error": await response.text()
                    }
        except Exception as e:
            return {"error": str(e)}

    async def full_process(self, user_input: str) -> dict:
        """完整处理流程"""
        # 第一阶段解析
        parsed = await self.parse_instruction(user_input)
        # print("解析结果:", json.dumps(parsed, indent=2, ensure_ascii=False))
        
        recall_msg = parsed.get('recall_msg', '抱歉，操作未完成')
        tasks = parsed.get('task_list', [])
        
        if not tasks:
            return {
                "recall_msg": recall_msg,
                "commands": [],
                "execution_results": []
            }
        
        # 第二阶段并行处理
        dispatch_coros = [self.dispatch_task(task) for task in tasks]
        dispatched = await asyncio.gather(*dispatch_coros)
        # print("任务分发结果:", json.dumps(dispatched, indent=2, ensure_ascii=False))
        
        # 第三阶段校验
        validate_coros = [self.validate_command(cmd) for cmd in dispatched]
        validated = await asyncio.gather(*validate_coros)
        # print("验证结果:", json.dumps(validated, indent=2, ensure_ascii=False))
        
        # 提取有效指令
        final_commands = []
        for v in validated:
            if v.get('valid', False):
                final_commands.append(v)
            elif 'corrected' in v:
                final_commands.append(v['corrected'])
            else:
                final_commands.append({
                    "device_id": "unknown_device",
                    "device_type": "switch",
                    "command": "toggle",
                    "params": ["on"]
                })
        
        # 并行执行控制
        execute_coros = [self.execute_command(cmd) for cmd in final_commands]
        execution_results = await asyncio.gather(*execute_coros)
        # print("执行结果:", json.dumps(execution_results, indent=2, ensure_ascii=False))
        
        # 检查执行结果，更新回复消息
        success_count = sum(1 for r in execution_results if r.get('status', 0) == 200)
        if success_count < len(tasks):
            recall_msg = f"部分操作未完成（成功 {success_count}/{len(tasks)}）"
        
        return {
            "recall_msg": recall_msg,
            "commands": final_commands,
            "execution_results": execution_results
        }

# 使用示例
async def main():
    user_input = input("请输入指令: ")
    
    # 使用异步上下文管理器确保资源正确释放
    async with HomeAutomationProcessor() as processor:
        result = await processor.full_process(user_input)
        print("\n最终回复:", result['recall_msg'])
        
        # 打印详细执行结果
        print("\n执行详情:")
        for i, res in enumerate(result['execution_results'], 1):
            # 获取设备ID，优先从修正后的命令中获取
            command = result['commands'][i-1]
            device_id = command.get('device_id', 
                                    command.get('corrected', {}).get('device_id', '未知设备'))
            
            if 'status' in res and res['status'] == 200:
                print(f"  - {device_id}: 操作成功")
            else:
                error = res.get('error', '未知错误')
                print(f"  - {device_id}: 操作失败 - {error}")

if __name__ == "__main__":
    # 在Windows上设置事件循环策略
    if hasattr(asyncio, 'WindowsSelectorEventLoopPolicy') and isinstance(
        asyncio.get_event_loop_policy(), asyncio.WindowsProactorEventLoopPolicy):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"程序运行出错: {e}")