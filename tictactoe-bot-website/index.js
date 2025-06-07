const http = require('http');
const server = http.createServer((req, res) => {
  res.statusCode = 200;
  res.setHeader('Content-Type', 'text/html');
  res.end('<h1>Hello from Tic-Tac-Toe with AI!</h1>');
});
const port = process.env.PORT || 3000;
server.listen(port, '0.0.0.0', () => console.log(`Server running on port ${port}`));