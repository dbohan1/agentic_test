"""
Interactive example demonstrating gameplay for The Mind.
"""

from the_mind import TheMind, GameState


def play_example_game():
    """
    Play through an example game scenario.
    """
    print("="*60)
    print("The Mind - Interactive Example")
    print("="*60)
    print()
    
    # Create a 2-player game
    game = TheMind(num_players=2)
    print(f"🎮 Starting a {game.num_players}-player game!")
    print(f"❤️  Lives: {game.lives}")
    print(f"⭐ Throwing Stars: {game.throwing_stars}")
    print()
    
    # --- Level 1 ---
    print("-" * 60)
    print("📊 LEVEL 1")
    print("-" * 60)
    game.setup_level()
    
    print(f"Player 0 hand: {game.get_player_hand(0)}")
    print(f"Player 1 hand: {game.get_player_hand(1)}")
    print()
    
    # Get the cards for ordered play
    all_cards = []
    for player_id in range(game.num_players):
        for card in game.get_player_hand(player_id):
            all_cards.append((card, player_id))
    all_cards.sort()
    
    # Play all cards in correct order
    for card, player_id in all_cards:
        success, msg = game.play_card(player_id, card)
        print(f"Player {player_id} plays {card}: {msg}")
    
    print(f"\n✅ Level 1 completed! Current level: {game.current_level}")
    print(f"Played pile: {game.played_pile}")
    print()
    
    # --- Level 2 ---
    print("-" * 60)
    print("📊 LEVEL 2")
    print("-" * 60)
    game.setup_level()
    
    print(f"Player 0 hand: {game.get_player_hand(0)}")
    print(f"Player 1 hand: {game.get_player_hand(1)}")
    print()
    
    # Demonstrate using a throwing star
    print("💭 Team decides to use a throwing star!")
    success, discarded = game.use_throwing_star()
    if success:
        for player_id, card in discarded.items():
            print(f"   Player {player_id} discards their lowest card: {card}")
        print(f"   ⭐ Throwing stars remaining: {game.throwing_stars}")
    print()
    
    print(f"After throwing star:")
    print(f"Player 0 hand: {game.get_player_hand(0)}")
    print(f"Player 1 hand: {game.get_player_hand(1)}")
    print()
    
    # Play remaining cards
    all_cards = []
    for player_id in range(game.num_players):
        for card in game.get_player_hand(player_id):
            all_cards.append((card, player_id))
    all_cards.sort()
    
    for card, player_id in all_cards:
        success, msg = game.play_card(player_id, card)
        print(f"Player {player_id} plays {card}: {msg}")
    
    print()
    
    # --- Demonstrate an error scenario ---
    print("-" * 60)
    print("📊 LEVEL 3 - Demonstrating a mistake")
    print("-" * 60)
    game.setup_level()
    
    print(f"Player 0 hand: {game.get_player_hand(0)}")
    print(f"Player 1 hand: {game.get_player_hand(1)}")
    print()
    
    # Manually create a scenario where a mistake happens
    # Let's say player 1 plays a higher card first
    player_0_cards = game.get_player_hand(0)
    player_1_cards = game.get_player_hand(1)
    
    if player_1_cards:
        # Play a card from player 1
        card_to_play = player_1_cards[0]
        success, msg = game.play_card(1, card_to_play)
        print(f"Player 1 plays {card_to_play}: {msg}")
        
        # Try to play a lower card from player 0 (if available)
        lower_cards = [c for c in player_0_cards if c < card_to_play]
        if lower_cards:
            card_to_play = lower_cards[0]
            success, msg = game.play_card(0, card_to_play)
            print(f"Player 0 plays {card_to_play}: {msg}")
            print(f"   ❌ ❤️  Lives remaining: {game.lives}/{game.max_lives}")
        else:
            # If no lower card, continue playing in order
            for card in player_0_cards:
                if card > game.played_pile[-1]:
                    success, msg = game.play_card(0, card)
                    print(f"Player 0 plays {card}: {msg}")
                    break
    
    print()
    
    # Final game status
    print("="*60)
    print("📈 GAME STATUS")
    print("="*60)
    info = game.get_game_info()
    print(f"Current Level: {info['current_level']}")
    print(f"Lives: {info['lives']}/{info['max_lives']}")
    print(f"Throwing Stars: {info['throwing_stars']}/{info['max_throwing_stars']}")
    print(f"Game State: {info['state']}")
    print()
    
    if game.state == GameState.GAME_WON:
        print("🎉 Congratulations! You won The Mind!")
    elif game.state == GameState.GAME_LOST:
        print("💔 Game Over! Better luck next time!")
    else:
        print("🎮 Game in progress...")
    
    print("="*60)


if __name__ == "__main__":
    play_example_game()
