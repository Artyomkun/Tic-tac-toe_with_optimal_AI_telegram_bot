// __tests__/game.test.js
const { initializeBoard } = require('../game.js');

test('initial board is empty', () => {
  const board = initializeBoard();
  expect(board).toEqual([['', '', ''], ['', '', ''], ['', '', '']]);
});
