import asyncio
from analyzer.services.chess_api import ChessAPIClient

async def test():
    client = ChessAPIClient()
    # Попробуй свой никнейм на Chess.com
    print("Fetching Chess.com games...")
    games = await client.get_games("neilside", "chess.com", limit=5)
    for g in games:
        print(f"Game: {g['opponent_name']} | Result: {g['user_result']} | Opening: {g['opening']}")

asyncio.run(test())