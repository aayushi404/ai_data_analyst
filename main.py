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
    
    

@app.get("/")
def root():
    client = genai.Client()
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="Explain how AI works in a few words",
    )
    return {"message":response.text}

def send_llm(sysInst:str, contents:list[str]):
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
    loop_prompt = os.path.join("prompts", "loop_prompt.txt")
    with open(loop_prompt, 'r') as f:
        prompt = f.read()
    
    msg = contents
    for i in range(3):
        print(f"generating {i+1}th call")
        response = send_llm(sysInst=prompt, contents=msg)
        write_log(f'llm_response_{i+1}:{response}')

        json_response = json.loads(response)
        for i in json_response.keys():
            if i == "answer":
                return json_response["answer"]
            if i == "code":
                print(f"executing {i + 1}th code")
                output = execute_code(json_response["code"])
                write_log(f'output_for_{i+1}_code: {output}')
                msg.append(output)
            else:
                return
    return json_response["code"]

def gen_code(instructions):
    sysPropmt = '''
        you are an experianced data analyst. 
        ***awailable resources: ***
        1. questions that requires getting the data, cleaning the data and analysing the data to get answers.
        2. step by step instructions to solve those questions 

        ***Goal: ***
        - generate complete executable python code. return a python script which can be directly saved to a file to execute.
        - don't write in markdown format
    '''
    code = send_llm(sysInst=sysPropmt, contents=[instructions])
    return code

def execute_code(code:str):
    with open('executable.py', 'w') as f:
        f.write(code)
    result = subprocess.run(['python3', 'executable.py'], capture_output=True, text=True)
    output = {"code":code, "output": result.stdout, "error":result.stderr}
    return json.dumps(output)

def write_log(content:str):
    with open("output.txt", 'a') as f:
        f.write(content)
        f.write('\n\n')

@app.post("/uploadFile/")
async def uploadFile(file:UploadFile=File(...)):
    try:
        content = await file.read()
        question = content.decode('utf-8')

        print("generating instructions")
        instructions = task_breakdown(question)
        log = f'instructions: {instructions}'
        write_log(log)

        print("generating first code")
        first_prompt = {"question":question, "instuctions":instructions}
        first_prompt = json.dumps(first_prompt)
        code = gen_code(first_prompt)

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