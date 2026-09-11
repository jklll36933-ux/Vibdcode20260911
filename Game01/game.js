const boardCanvas = document.querySelector('#gameBoard');
const boardContext = boardCanvas.getContext('2d');
const nextCanvas = document.querySelector('#nextPiece');
const nextContext = nextCanvas.getContext('2d');
const overlay = document.querySelector('#overlay');
const overlayTitle = document.querySelector('#overlayTitle');
const overlayMessage = document.querySelector('#overlayMessage');
const overlayButton = document.querySelector('#overlayButton');
const pauseButton = document.querySelector('#pauseButton');
const statusText = document.querySelector('#statusText');
const scoreElement = document.querySelector('#score');
const levelElement = document.querySelector('#level');
const linesElement = document.querySelector('#lines');

const columns = 10;
const rows = 20;
const cellSize = 30;
const colors = ['#000000', '#ff5f56', '#ffbd2e', '#27c93f', '#5ab0ff', '#c77dff', '#ff8a3d', '#56e0c1'];
const pieces = [
  [[1, 1, 1, 1]],
  [[2, 2], [2, 2]],
  [[0, 3, 0], [3, 3, 3]],
  [[4, 0, 0], [4, 4, 4]],
  [[0, 0, 5], [5, 5, 5]],
  [[6, 6, 0], [0, 6, 6]],
  [[0, 7, 7], [7, 7, 0]]
];

let board;
let currentPiece;
let nextPiece;
let score = 0;
let totalLines = 0;
let level = 1;
let dropTimer = null;
let dropInterval = 800;
let gameState = 'ready';

function createBoard() { return Array.from({ length: rows }, () => Array(columns).fill(0)); }

function randomPiece() {
  const shape = pieces[Math.floor(Math.random() * pieces.length)].map(row => [...row]);
  return { shape, x: Math.floor(columns / 2) - Math.ceil(shape[0].length / 2), y: 0 };
}

function drawCell(context, x, y, color, size) {
  context.fillStyle = colors[color];
  context.fillRect(x * size + 1, y * size + 1, size - 2, size - 2);
  context.fillStyle = 'rgba(255,255,255,.25)';
  context.fillRect(x * size + 3, y * size + 3, size - 8, 3);
  context.fillStyle = 'rgba(0,0,0,.22)';
  context.fillRect(x * size + 3, y * size + size - 6, size - 6, 3);
}

function drawBoard() {
  boardContext.fillStyle = '#121416';
  boardContext.fillRect(0, 0, boardCanvas.width, boardCanvas.height);
  boardContext.strokeStyle = 'rgba(255,255,255,.045)';
  boardContext.lineWidth = 1;
  for (let y = 0; y <= rows; y++) { boardContext.beginPath(); boardContext.moveTo(0, y * cellSize + .5); boardContext.lineTo(300, y * cellSize + .5); boardContext.stroke(); }
  for (let x = 0; x <= columns; x++) { boardContext.beginPath(); boardContext.moveTo(x * cellSize + .5, 0); boardContext.lineTo(x * cellSize + .5, 600); boardContext.stroke(); }
  board.forEach((row, y) => row.forEach((value, x) => value && drawCell(boardContext, x, y, value, cellSize)));
  if (currentPiece) currentPiece.shape.forEach((row, y) => row.forEach((value, x) => value && drawCell(boardContext, currentPiece.x + x, currentPiece.y + y, value, cellSize)));
}

function drawNext() {
  nextContext.fillStyle = '#16191d';
  nextContext.fillRect(0, 0, nextCanvas.width, nextCanvas.height);
  if (!nextPiece) return;
  const size = 25;
  const offsetX = (nextCanvas.width - nextPiece.shape[0].length * size) / 2;
  const offsetY = (nextCanvas.height - nextPiece.shape.length * size) / 2;
  nextPiece.shape.forEach((row, y) => row.forEach((value, x) => {
    if (!value) return;
    nextContext.fillStyle = colors[value];
    nextContext.fillRect(offsetX + x * size + 1, offsetY + y * size + 1, size - 2, size - 2);
    nextContext.fillStyle = 'rgba(255,255,255,.25)';
    nextContext.fillRect(offsetX + x * size + 3, offsetY + y * size + 3, size - 8, 3);
  }));
}

function collides(piece, offsetX = 0, offsetY = 0, shape = piece.shape) {
  return shape.some((row, y) => row.some((value, x) => value && (piece.x + x + offsetX < 0 || piece.x + x + offsetX >= columns || piece.y + y + offsetY >= rows || board[piece.y + y + offsetY]?.[piece.x + x + offsetX])));
}

function rotate(shape) { return shape[0].map((_, index) => shape.map(row => row[index]).reverse()); }

function move(direction) {
  if (gameState !== 'playing' || collides(currentPiece, direction)) return;
  currentPiece.x += direction;
  drawBoard();
}

function rotatePiece() {
  if (gameState !== 'playing') return;
  const rotated = rotate(currentPiece.shape);
  if (!collides(currentPiece, 0, 0, rotated)) currentPiece.shape = rotated;
  drawBoard();
}

function lockPiece() {
  currentPiece.shape.forEach((row, y) => row.forEach((value, x) => { if (value) board[currentPiece.y + y][currentPiece.x + x] = value; }));
  clearLines();
  currentPiece = nextPiece;
  nextPiece = randomPiece();
  drawNext();
  if (collides(currentPiece)) endGame();
}

function clearLines() {
  let cleared = 0;
  board = board.filter(row => { if (row.every(Boolean)) { cleared++; return false; } return true; });
  while (board.length < rows) board.unshift(Array(columns).fill(0));
  if (!cleared) return;
  const points = [0, 100, 300, 500, 800][cleared] * level;
  score += points;
  totalLines += cleared;
  level = Math.floor(totalLines / 10) + 1;
  dropInterval = Math.max(100, 800 - (level - 1) * 65);
  updateStats();
  resetTimer();
}

function drop() {
  if (gameState !== 'playing') return;
  if (!collides(currentPiece, 0, 1)) currentPiece.y++;
  else lockPiece();
  drawBoard();
}

function hardDrop() {
  if (gameState !== 'playing') return;
  while (!collides(currentPiece, 0, 1)) { currentPiece.y++; score += 2; }
  lockPiece();
  updateStats();
  drawBoard();
}

function resetTimer() { clearInterval(dropTimer); dropTimer = setInterval(drop, dropInterval); }

function updateStats() {
  scoreElement.textContent = String(score).padStart(6, '0');
  levelElement.textContent = String(level).padStart(2, '0');
  linesElement.textContent = String(totalLines).padStart(3, '0');
}

function startGame() {
  board = createBoard(); score = 0; totalLines = 0; level = 1; dropInterval = 800;
  currentPiece = randomPiece(); nextPiece = randomPiece(); gameState = 'playing';
  overlay.classList.add('hidden'); pauseButton.disabled = false; statusText.textContent = 'PLAYING';
  updateStats(); drawNext(); drawBoard(); resetTimer();
}

function togglePause() {
  if (gameState === 'playing') { gameState = 'paused'; clearInterval(dropTimer); statusText.textContent = 'PAUSED'; pauseButton.innerHTML = '<span>▶</span> RESUME'; overlayTitle.textContent = 'PAUSED'; overlayMessage.textContent = '계속하려면 RESUME을 눌러주세요'; overlayButton.textContent = 'RESUME'; overlay.classList.remove('hidden'); }
  else if (gameState === 'paused') { gameState = 'playing'; overlay.classList.add('hidden'); pauseButton.innerHTML = '<span>Ⅱ</span> PAUSE'; statusText.textContent = 'PLAYING'; resetTimer(); }
}

function endGame() {
  gameState = 'over'; clearInterval(dropTimer); pauseButton.disabled = true; statusText.textContent = 'GAME OVER';
  overlayTitle.textContent = 'GAME OVER'; overlayMessage.textContent = `FINAL SCORE ${String(score).padStart(6, '0')}`; overlayButton.textContent = 'PLAY AGAIN'; overlay.classList.remove('hidden');
}

document.addEventListener('keydown', event => {
  if (event.key === 'ArrowLeft') { event.preventDefault(); move(-1); }
  if (event.key === 'ArrowRight') { event.preventDefault(); move(1); }
  if (event.key === 'ArrowDown') { event.preventDefault(); drop(); }
  if (event.key === 'ArrowUp') { event.preventDefault(); rotatePiece(); }
  if (event.code === 'Space') { event.preventDefault(); hardDrop(); }
  if (event.key.toLowerCase() === 'p') togglePause();
});
overlayButton.addEventListener('click', () => gameState === 'paused' ? togglePause() : startGame());
pauseButton.addEventListener('click', togglePause);
board = createBoard();
drawBoard();