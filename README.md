# Porygon3

Porygon3 is a Discord bot designed for the Springfield Battle League, a VGC Pokémon Draft League. It includes various Pokémon-related features both specific to the draft league and related to Pokémon in general. If you are looking to use this for your own draft league, there are many specific features associated with our document set-up and record keeping that would be hard to carry over. However, features like the replay analysis and integration with Pokemon Showdown could be generally applied.

## Features

Porygon3's functionality is organized into modular cogs, each providing specialized features for the Springfield Battle League and general Pokémon Discord activities:

- **General Cog**: Offers basic bot commands, help messages, and utility functions for users.
- **Trade Cog**: Facilitates Pokémon trades between league members, including trade requests, confirmations, and trade history tracking.
- **Betting Cog**: Enables users to place bets on league matches, manage virtual currency, and view betting leaderboards.
- **Season Cog**: Manages league seasons, including scheduling matches, reporting results, and tracking team standings.
- **Showdown Cog**: Integrates with Pokémon Showdown to fetch and analyze battle replays, extract stats, and update player records.
- **SBL Cog**: Provides Springfield Battle League-specific features such as draft management, coach rosters, and league announcements.
- **Misc Cog**: Contains additional fun or utility commands, such as tracking the number of times "Tuesday" is mentioned.


### Stat Tracking

- Automatically parses Pokémon Showdown replays to record statistics like kills, deaths, and other performance metrics for league analysis.
- Supports leaderboard generation and historical performance tracking for coaches and teams.

## Project Structure

```
Porygon3/
├── cogs/                     # Contains modular command files for the bot
├── resources/                # Data files and resources used by the bot
├── main.py                   # Entry point for the Discord bot
├── utils.py                  # Utility functions and constants
├── requirements.txt          # Python dependencies
├── .gitignore                # Git ignore rules
```

## Setup

1. Clone the repository:
   ```sh
   git clone https://github.com/your-repo/porygon3.git
   cd porygon3
   ```

2. Create a virtual environment and activate it:
   ```sh
   python -m venv venv
   venv\Scripts\activate  # On Windows
   ```

3. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```

4. Add your Discord bot token:
   - Place your bot token in `resources/discord_secret.txt`.

5. Run the bot:
   ```sh
   python main.py
   ```

## Usage

- Use the `!` prefix to interact with the bot.
- Example commands:
  - `!tuesday`: Tracks the number of times "Tuesday" is mentioned.
  - `!bet <amount>`: Place a bet on a match.

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
