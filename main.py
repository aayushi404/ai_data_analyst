from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from google import genai
from google.genai import types
from dotenv import load_dotenv
import os

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

def loop(sysInst:str, contents=list[str]):
    return

def gen_code(instructions):
    sysPropmt = '''
        you are an experianced data analyst. 
        ***awailable resources: ***
        1. questions to solve
        2. step by step instructions to solve those questions 

        ***Goal: ***
        generate complete python code that can be executable. also include libraries to install in the code 
    '''
    code = send_llm(sysInst=sysPropmt, contents=[instructions])
    return code

@app.post("/uploadFile/")
async def uploadFile(file:UploadFile=File(...)):
    try:
        content = await file.read()
        if file.content_type == "text/plain":
            text = content.decode('utf-8')
            instructions = task_breakdown(text)
            get_code(instructions)
            return {"content":text}
        else:
            return JSONResponse(status_code=200, content={"message":"please provide you detailed question in a txt file"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error":str(e)})

if __name__ == "__main__":
    import uvicorn as uv
    uv.run(app, host='127.0.0.1', port=3030)