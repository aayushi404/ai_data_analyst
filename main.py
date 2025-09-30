from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from google import genai
from google.genai import types
from dotenv import load_dotenv
import os
import json
import subprocess

load_dotenv()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

def task_breakdown(task:str):
    '''
    client = genai.Client()
    task_breakdown_prompt_filepath = os.path.join("prompts", "task_breakdown.txt")
    with open(task_breakdown_prompt_filepath, 'r') as f:
        prompt = f.read()
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt, task],
        )
        print(response.text)
        with open('answer.txt', 'w') as f:
            f.write(response.text)
        print("answer generated")
    except Exception as e:
       raise Exception(str(e))
       '''
    with open('mainPrompt.txt', 'r') as f:
        prompt = f.read()

    return prompt
    

@app.get("/")
def root():
    client = genai.Client()
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="Explain how AI works in a few words",
    )
    return {"message":response.text}

def send_llm(sysInst:str="", contents:list[str]=None):
    try:
        client = genai.Client()
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(
                system_instruction=sysInst),
            contents=contents
        )
        return response.text
    except Exception as e:
        raise Exception(str(e))

def loop(contents=list[str]):
    loop_propmt = os.path.join("prompts", "loop_propmt.txt")
    with open(loop_propmt, 'r') as f:
        loopPrompt = f.read()
    
    msg = contents
    for i in range(2):
        print(f"generating {i+1}th call")
        response = send_llm(sysInst=loopPrompt, contents=msg)
        write_log(f'llm_response_{i+1}:{response}')

        json_response = json.load(response)
        if json_response.final_answer:
            return json_response.final_answer
        
        print(f"execution the {i + 1}th code")
        output = execute_code(json_response.code)
        write_log(f'output_for_{i+1}_code: {output}')
        msg.append(output)
    return json_response.code

def gen_code(instructions):
    sysPropmt = '''
        you are an experianced data analyst. 
        ***awailable resources: ***
        1. questions to solve
        2. step by step instructions to solve those questions 

        ***Goal: ***
        generate complete executable python code.
    '''
    code = send_llm(sysInst=sysPropmt, contents=[instructions])
    return code

def execute_code(code:str):
    with open('executable_code.py', 'w') as f:
        f.write(code)
    result = subprocess.run(['python3', 'executable_code.py'], capture_output=True, text=True)
    output = {"code":code, "output": result.stdout, "error":result.stderr}
    return json.dump(output)

def write_log(content:str):
    with open("outputs.txt", 'a') as f:
        f.write(content)
        f.write('\n')

@app.post("/uploadFile/")
async def uploadFile(file:UploadFile=File(...)):
    try:
        content = await file.read()
        text = content.decode('utf-8')

        print("generating instructions")
        instructions = task_breakdown(text)
        log = f'instructions: {instructions}'
        write_log(log)

        print("generating first code")
        first_prompt = {"question":content, "instuctions":instructions}
        first_prompt = json.dump(first_prompt)
        code = gen_code(first_prompt)
        write_log(f'code:{code}')

        print("execution the first code")
        output = execute_code(code)
        write_log(f'output:{output}')
   
        contents = [first_prompt] + [output]
        print("debugging the first code")
        final_answer = loop(contents=contents)
        return {"content":final_answer}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error":str(e)})

if __name__ == "__main__":
    import uvicorn as uv
    uv.run(app, host='127.0.0.1', port=3030)