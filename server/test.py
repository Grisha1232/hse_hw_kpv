# main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from typing import List, Dict
from pydantic import BaseModel
from enum import Enum
from uuid import uuid4
import asyncio
import time

app = FastAPI()

origins = [
    "http://localhost:8000",
    "http://localhost",
    "http://localhost:8080",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
class BoardState(str, Enum):
	EMPTY = " "
	X = "X"
	O = "O"


class GameSession:
	def __init__(self, player1: WebSocket, player2: WebSocket):
		self.id = str(uuid4())
		self.player1 = player1
		self.player2 = player2
		self.last_time_action_1 = time.time();
		self.last_time_action_2 = time.time();
		self.board = [[BoardState.EMPTY]*3 for _ in range(3)]
		self.current_turn = BoardState.X
		self.player1_wins = 0;
		self.player2_wins = 0;
		self.draws = 0;

# Словарь для хранения активных игровых сессий
active_sessions: Dict[str, GameSession] = {}

html = """
<!-- index.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tic Tac Toe</title>
</head>
<body>
    <div id="game">
    	<div id="player"></div>
        <div id="board"></div>
        <div id="status">Waiting for opponent...</div>
        <div id="counter">
        	<div id="player1"></div>
        	<div id="player2"></div>
        	<div id="draw"></div>
        </div>
    </div>
    <script>// script.js
            var socket = new WebSocket("ws://localhost:8000/connect");
            socket.onopen = function(event) {
                console.log("WebSocket connected");
                const msg = {
				    status: "join"
				  };
                socket.send(JSON.stringify(msg))
            };

            socket.onmessage = function(event) {
                const data = JSON.parse(event.data);
                console.log(data)
                if (data.status == "waiting" || data.status == "ready") {
                	player_num = data.player;
                	session_id = data.session_id;
                	console.log(data.player);
                	console.log(player_num);
                } else if (data.status == "start") {
                	startBoard();
                } else if (data.status === "update") {
                    updateBoard(data.board, data.turn);
                } else if (data.status === "game_over") {
                    handleGameOver(data.result, data.count);
                } else if (data.status == "error") {
                	let status = document.getElementById("status");
                	status.textContent = data.message;
                	if (clicked != null) {
	                	clicked.textContent = "";
	                	clicked = null;
                	}
                } else if (data.status == "opponentDisconnect") {
                	let status = document.getElementById("status")
                	status.textContent = "Opponent Disconnected. Diconnecting you. If you wanna play again, please refresh the page"
                }
            };

            function startBoard() {
            	let boardDiv = document.getElementById("board");
            	for (let i = 0; i < 3; i++) {
            		let row = document.createElement("div");
            		row.setAttribute("class", "row");
            		boardDiv.appendChild(row);
            		for (let j = 0; j < 3; j++) {
            			let button = document.createElement("button");
            			button.setAttribute("class", "btn")
            			button.setAttribute("type", "button")
            			button.id = i + "_" + j;
            			z = document.createAttribute("readonly")
            			button.setAttributeNode(z)
            			button.onclick = function(event) {
            				clickedCellButton(event);
            			}
            			row.appendChild(button);

            		}
            	}

            	let status = document.getElementById("status");
            	status.textContent = "move: Player 1";

            	let player = document.getElementById("player");
            	player.textContent = player_num;

            	let button = document.createElement("button");
            	button.setAttribute("type", "button");
            	button.textContent = "Make move";
            	button.onclick = function(event) {
            		handleMove(event);
            	}
            	document.getElementById("game").appendChild(button);
            };

            function handleMove(event) {
            	const msg = {
            		status: "move",
            		i: selected_i,
            		j: selected_j,
            		"session_id": session_id
            	}
            	socket.send(JSON.stringify(msg));
            };

            function clickedCellButton(event) {
            	if (clicked != null) {
            		clicked.textContent = "";
            	}
            	let cell = event.srcElement;
            	if (cell.textContent != "") {
            		selected_i = -1;
            		selected_j = -1;
            		clicked = null;
            		return;
            	}
            	clicked = cell;
            	console.log(cell.id);
            	selected_i = Number(event.srcElement.id[0]);
            	selected_j = Number(event.srcElement.id[2]);
            	if (cell.textContent != "") {
            		cell = null
            		return;
            	}
            	if (player_num == "Player1") {
            		cell.textContent = "X";
            	} else {
            		cell.textContent = "O";
            	}
            };

            function updateBoard(board, turn) {
            	console.log(turn);
            	let cell = document.getElementById(turn.i + "_" + turn.j);
            	console.log(cell);
            	if (clicked != null) {
            		clicked.textContent = "";
            		clicked = null;
            	}
            	cell.textContent = turn.player;

            	let status = document.getElementById("status");
            	if (turn.player == "X") {
            		status.textContent = "move: Player 2"
            	} else {
            		status.textContent = "move: Player 1"
            	}
            };

            function handleGameOver(result, counter) {
                let message;
                if (result === "win") {
                    message = "You win!";
                } else if (result === "lose") {
                    message = "You lose!";
                } else {
                    message = "It's a draw!";
                }
                document.getElementById("status").textContent = message;

                clicked = null;
                document.getElementById("player1").textContent = "player 1: " + counter.player1;
                document.getElementById("player2").textContent = "player 2: " + counter.player2;
                document.getElementById("draw").textContent = "draw: " + counter.draw;

                let cells = document.getElementsByClassName("btn");
                for (let i = 0; i < 9; i++) {
                	cells.item(i).textContent = "";
                }
            }

            var clicked = null;
            var player_num = "";
            var selected_i = -1;
            var selceted_j = -1;
            var session_id = "";
    </script>
    <style type="text/css">/* style.css */
#game {
    width: 350px;
    margin: 0 auto;
}

#board {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  margin: 35px;
}

.row {
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn {
  border: 1px solid black;
  border-radius: 5px;
  height: 75px;
  margin: 2px;
  width: 75px;
  text-align: center;
  font-size: 50px;
  font-weight: 500;
}
</style>
</body>
</html>
"""

@app.get("/")
async def start():
	print("ok")
	return HTMLResponse(html)

@app.websocket("/test")
async def test(websocket: WebSocket):
	print("not ok")
	await websocket.accept();
	return {"hello"}

@app.websocket("/connect")
async def read_root(websocket: WebSocket):
	await websocket.accept()
	try:
		while True:
			# Получаем сообщение от клиента
			message = await websocket.receive_json()
			if message["status"] == "join":
				await handle_join(websocket)
			elif message["status"] == "move":
				await handle_move(websocket, message)
			else:
				continue
	except WebSocketDisconnect:
		print("lol")
		pass
	

async def handle_join(websocket: WebSocket):
	if len(active_sessions) == 0 or active_sessions[list(active_sessions.keys())[-1]].player2 is not None:
		# Создаем новую игровую сессию, если нет активных сессий или в текущей сессии уже есть два игрока
		game_session = GameSession(player1=websocket, player2=None)
		active_sessions[game_session.id] = game_session
		await websocket.send_json({"status": "waiting", "session_id": game_session.id, "player": "Player1"})
		asyncio.create_task(check_online_players(game_session))
	else:
		# Присоединяемся к существующей игровой сессии
		session_id = list(active_sessions.keys())[-1]
		active_sessions[session_id].player2 = websocket
		await websocket.send_json({"status": "ready", "session_id": session_id, "player": "Player2"})
		await websocket.send_json({"status": "start", "session_id": session_id})
		await active_sessions[session_id].player1.send_json({"status": "start", "session_id": session_id})
		# Запуск asyncio.Task для проверки онлайн статуса игроков




async def handle_move(websocket: WebSocket, message: dict):
	session_id = message.get("session_id")
	row = message.get("i")
	col = message.get("j")
	game_session = active_sessions.get(session_id)
	if game_session is None or game_session.player1 != websocket and game_session.player2 != websocket:
		await websocket.send_json({"status": "error", "message": "Invalid session"})
		return
	if game_session.current_turn == BoardState.X and websocket != game_session.player1:
		await websocket.send_json({"status": "error", "message": "It's not your turn"})
		return
	if game_session.current_turn == BoardState.O and websocket != game_session.player2:
		await websocket.send_json({"status": "error", "message": "It's not your turn"})
		return
	if not (0 <= row <= 2 and 0 <= col <= 2):
		await websocket.send_json({"status": "error", "message": "Invalid move"})
		return
	if game_session.board[row][col] != BoardState.EMPTY:
		await websocket.send_json({"status": "error", "message": "Cell already occupied"})
		return

	if (game_session.player1 == websocket):
		game_session.last_time_action_1 = time.time();
	else:
		game_session.last_time_action_2 = time.time();

	# Обновляем состояние игровой доски
	game_session.board[row][col] = game_session.current_turn
	# Проверяем наличие победителя или ничьи
	winner = check_winner(game_session.board)
	if winner:
		if (winner == BoardState.X):
			game_session.player1_wins += 1
		else:
			game_session.player2_wins += 1
		await game_session.player1.send_json({"status": "game_over", "result": "win" if winner == BoardState.X else "lose", 
        	"count": {"player1": game_session.player1_wins, "player2": game_session.player2_wins, "draw": game_session.draws}})
		await game_session.player2.send_json({"status": "game_over", "result": "win" if winner == BoardState.O else "lose",
        	"count": {"player1": game_session.player1_wins, "player2": game_session.player2_wins, "draw": game_session.draws}})
		await restart_game(game_session)
	elif all(cell != BoardState.EMPTY for row in game_session.board for cell in row):
		game_session.draws += 1
		await game_session.player1.send_json({"status": "game_over", "result": "draw", "count": {"player1": game_session.player1_wins, "player2": game_session.player2_wins, "draw": game_session.draws}})
		await game_session.player2.send_json({"status": "game_over", "result": "draw", "count": {"player1": game_session.player1_wins, "player2": game_session.player2_wins, "draw": game_session.draws}})
		await restart_game(game_session)
	else:
		# Переключаем ход
		# Отправляем обновленное состояние доски игрокам
		await game_session.player1.send_json({"status": "update", "board": game_session.board, "turn": {"i": row, "j": col, "player": game_session.current_turn}})
		await game_session.player2.send_json({"status": "update", "board": game_session.board, "turn": {"i": row, "j": col, "player": game_session.current_turn}})
		game_session.current_turn = BoardState.X if game_session.current_turn == BoardState.O else BoardState.O

# Метод для проверки наличия победителя
def check_winner(board: List[List[BoardState]]) -> BoardState:
    # Проверка строк
    for row in board:
        if row[0] == row[1] == row[2] and row[0] != BoardState.EMPTY:
            return row[0]
    # Проверка столбцов
    for col in range(3):
        if board[0][col] == board[1][col] == board[2][col] and board[0][col] != BoardState.EMPTY:
            return board[0][col]
    # Проверка диагоналей
    if board[0][0] == board[1][1] == board[2][2] and board[0][0] != BoardState.EMPTY:
        return board[0][0]
    if board[0][2] == board[1][1] == board[2][0] and board[0][2] != BoardState.EMPTY:
        return board[0][2]
    return None

async def restart_game(game_session):
    game_session.board = [[BoardState.EMPTY]*3 for _ in range(3)]

# Метод для сброса игровой сессии
async def reset_game(session_id: str):
    active_sessions.pop(session_id)

# asyncio.Task для проверки онлайн статуса игроков
async def check_online_players(game_session):
    while True:
        await asyncio.sleep(30)
        if (game_session.player2 is None):
        	continue
        if (time.time() - game_session.last_time_action_1 > 30):
        	await game_session.player1.send_json({"status": "opponentDisconnect"})
        	await game_session.player1.close()
        	await game_session.player2.send_json({"status": "opponentDisconnect"})
        	await game_session.player2.close()
        	active_sessions.pop(game_session.id)
        elif (time.time() - game_session.last_time_action_2 > 30):
        	await game_session.player2.send_json({"status": "opponentDisconnect"})
        	await game_session.player2.close()
        	await game_session.player1.send_json({"status": "opponentDisconnect"})
        	await game_session.player1.close()
        	active_sessions.pop(game_session.id)


