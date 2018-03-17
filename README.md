# Theorycrafter
This is designed to generate ship fittings for the game Eve Online based off records of destroyed ships (killmails).

The two csvs contain static data about modules and ships in Eve, and the json file is a sample batch of killmails.

ToDo:
Improve training time by simplifying inputs slightly
Write generative network and test, including a "itemID" to English function
Test the predictive network on an independent test set (a second batch of killmails) 
Write batch importing of killmails (multiple JSON files)
...
