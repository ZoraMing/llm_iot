import json
import asyncio
from openai import AsyncOpenAI

from llm_task_prompts import system_prompt_parser, system_prompt_dispatcher, system_prompt_validator
from llm_task_tools import devices_info

aclient = AsyncOpenAI(
    api_key="sk-8e1eb5aaeb824c02a3a561f3c0c33c47",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

used_model = "qwen-plus"
# used_model = "qwen-turbo"


async def process_instruction(user_input):
    # 第一阶段：异步指令解析
    stage1 = await aclient.chat.completions.create(
        model=used_model,    
        messages=[{
            "role": "system", 
            "content": system_prompt_parser.replace("{devices_info}", json.dumps(devices_info))
        },{
            "role": "user",
            "content": f"{user_input}（请返回JSON格式）"
        }],
        temperature=0.1,
        response_format={"type": "json_object"}
    )
    
    # 解析第一阶段结果
    stage1_content = json.loads(stage1.choices[0].message.content)
    tasks = stage1_content.get('tool_calls', [])
    print(tasks,"======1")

    # 第二阶段：并行处理所有任务
    stage2_coros = []
    for task in tasks:
        stage2_coros.append(
            aclient.chat.completions.create(
                model=used_model,
                messages=[{
                    "role": "system",
                    "content": system_prompt_dispatcher
                },{
                    "role": "user",
                    "content": json.dumps(task)
                }],
                temperature=0.0,
                response_format={"type": "json_object"}
            )
        )
    
    # 并行执行所有任务生成
    stage2_results = await asyncio.gather(*stage2_coros)
    for result in stage2_results:
        print(result.choices[0].message.content,"======2\n")

    # 第三阶段：并行格式校验
    stage3_coros = []
    for result in stage2_results:
        if result.choices[0].message.content:
            stage3_coros.append(
                aclient.chat.completions.create(
                    model=used_model,
                    messages=[{
                        "role": "system",
                        "content": system_prompt_validator
                    },{
                        "role": "user",
                        "content": result.choices[0].message.content
                    }],
                    temperature=0.0,
                    response_format={"type": "json_object"}
                )
            )
    
    # 获取所有校验结果
    stage3_results = await asyncio.gather(*stage3_coros)
    for result in stage3_results:
        print(result.choices[0].message.content,"======3\n")
    
    # 构建最终输出
    return [json.loads(r.choices[0].message.content) for r in stage3_results if r.choices]

if __name__ == "__main__":
    # 异步执行测试
    async def main():
        result = await process_instruction("帮我开灯")
        llm_res = json.dumps(result, indent=2, ensure_ascii=False)
        print(llm_res)

    
    asyncio.run(main())