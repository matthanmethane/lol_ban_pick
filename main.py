from typing import List, Optional

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import json

ban_phase_list = [
    'blueBan1',
    'redBan1',
    'blueBan2',
    'redBan2',
    'blueBan3',
    'redBan3',
    'bluePick1',
    'redPick1',
    'redPick2',
    'bluePick2',
    'bluePick3',
    'redPick3',
    'redBan4',
    'blueBan4',
    'blueBan5',
    'redBan5',
    'redPick4',
    'bluePick4',
    'bluePick5',
    'redPick5'
]

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        for connection in self.active_connections:
            await connection.send_text(json.dumps({'side': '', 'champ': '', 'phase': ban_phase_list[0], 'phase_id': 0}))

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()


@app.get("/{side}", response_class=HTMLResponse)
async def get(request: Request, side: Optional[str] = None):
    with open('champion_list.json', 'r', encoding='utf-8') as f:
        champion_list = json.load(f)
    # print(type(champion_list))
    if side == 'red':
        return templates.TemplateResponse("home.html", {'request': request, 'side': side, 'champions': champion_list, })
    if side == 'blue':
        return templates.TemplateResponse("home.html", {'request': request, 'side': side, 'champions': champion_list, })
    return templates.TemplateResponse("home.html", {'request': request, 'side': 'watch', 'champions': champion_list, })


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            json_data = json.loads(data)
            json_data['prev_phase'] = ban_phase_list[json_data['phase_id']-1]
            json_data['phase'] = ban_phase_list[json_data['phase_id']
                                                ] if json_data['phase_id'] < len(ban_phase_list) else ''
            # await manager.send_personal_message(f"You wrote: {data}", websocket)
            print(json_data)
            await manager.broadcast(json.dumps(json_data))
            # await manager.broadcast(f"{client_id.capitalize()} ban/picks: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client #{client_id} left the chat")
