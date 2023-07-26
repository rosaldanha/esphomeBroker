#!/usr/bin/env python
import asyncio
#import websockets
from websockets import connect, serve
import re, yaml, json
from urllib.parse import urlparse



def getWsUrl(commonUrl:str) -> str:
    urlParsed = urlparse(commonUrl)
    if urlParsed.scheme == 'https':
        RETURN_PROTOCOL = 'wss'
    else:
        RETURN_PROTOCOL = 'ws'
    RETURN_PATH = '/run'
    if urlParsed.port != None:
        RETURN_PORT = f":{urlParsed.port}"
    else:
        RETURN_PORT = ''
    return f"{RETURN_PROTOCOL}://{urlParsed.hostname}{RETURN_PORT}{RETURN_PATH}"

def loadConfig() :
    with open('config.yml', 'r') as file:
        prime_service = yaml.safe_load(file)
    return prime_service
def getEvtDone(type:str, device:str ):
    return json.dumps({
        "type":type,
        "device":device,
        "status":"done"
    })
def getEvtRunning(type:str, device:str):
    return json.dumps({
        "type":type,
        "device":device,
        "status":"running"
    })
def getEvtPercent(device:str, value:int):
    return json.dumps({
        "type": "percent",
        "device":device,
        "status": value
    })       
async def handler(websocket):
    while True:
        message = await websocket.recv()
        currentDevice = ''
        messageObject =json.loads(message)  
        if messageObject["type"] == "quit":
            print('quiting')
            break
        if messageObject["type"] == "spawn":
            currentDevice = messageObject["configuration"].split('.')[0]
        print('vou conectar o esphome aqui')
        await asyncio.sleep(0)
        WS_URL = getWsUrl(CONFIG["server"]["url"])
        async with connect(WS_URL) as websocketClient:
            print('Conectado no esphome')
            await websocketClient.send(message)
            while True:
                message = await websocketClient.recv()   
                messageObject =json.loads(message)  
                print(message)
                if messageObject["event"] == 'line':
                    dataStr = messageObject["data"]
                if messageObject["event"]=='exit':
                    dataStr = "ERROR"
                if dataStr.find("Reading configuration") > -1:                    
                    await websocket.send(getEvtRunning("config",currentDevice)) # reading config
                if dataStr.find("Compiling") > -1:
                    evt = {
                        "type":"config",
                        "device": currentDevice,
                        "status": "done"
                    }
                    await websocket.send(getEvtDone("config",currentDevice)) # reading config
                    await asyncio.sleep(0.1)
                    await websocket.send(getEvtRunning("compile",currentDevice)) # reading config
                if dataStr.find("ERROR") > -1:
                    await websocket.send('ERROR')
                    await asyncio.sleep(0.1)                
                    await websocketClient.close()  
                    break                 
                if dataStr.startswith("Uploading"):
                    numero = re.findall(r"\d+(?=%)",dataStr)[0] if re.findall(r"\d+(?=%)", dataStr) else None
                    if numero:
                        if numero == '0':
                            await websocket.send(getEvtDone("compile",currentDevice)) # reading config
                            await asyncio.sleep(0.1)
                            await websocket.send(getEvtRunning("ota",currentDevice))
                        else:
                            await websocket.send(getEvtPercent(currentDevice,numero))  
                if dataStr.find("OTA successful") > -1:
                    await websocket.send(getEvtDone("ota",currentDevice))
                    await asyncio.sleep(0.1)
                    await websocketClient.close()
                    break
                await asyncio.sleep(0)
            print('exited')           
            


async def main():
    async with serve(handler, "", 8001,open_timeout=None,close_timeout=None):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    CONFIG = loadConfig()
    asyncio.run(main())