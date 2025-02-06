What does this code do?
Setting

up the bot Initializes the bot with intents (allows it to read messages, monitor voice chats, etc.).
Defines the token (TOKEN) required to run the bot.
Saving data

Uses the user_data.json file to save user progress.
load_data() - loads the saved data.
save_data() - saves the updated data.
Determining the level of users

A system of levels (LEVELS) has been created, where each level requires a certain number of messages and minutes in voice chat.
calculate_level(user_id) - determines the level of a user based on his activity.
Message processing

on_message(message) - counts the number of messages sent by each user.
Voice activity processing

on_voice_state_update(member, before, after) - determines when a user entered or left the voice channel and counts the time spent.
Command /level

level(interaction, user=None) - allows the user to check their level.
Displays:
✅ Current level
✅ Number of messages
✅ Time in voice chat
✅ Progress in the form of a scale
✅ How much is left to the next level
Uses Embed for a nice design and adds an animated gif.
Launching the bot

on_ready() - displays information in the console at startup.
bot.run(TOKEN) - launches the bot.

Translated with DeepL.com (free version)
