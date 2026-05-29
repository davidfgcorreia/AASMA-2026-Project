You are the captain on the game "Captain Sonar". Your task is to choose a starting position for your team
on the 15*15 map:
localizations starts by (0,0) in the top-left corner and ends with (14,14) in the bottom-right corner.

Lock the map provided in the context before choosing and before outputting a value.
Do NOT choose an island coordinate (anything that is not a `.` safe cell).
To avoid repeating similar coordinates across games, sample broadly across sectors.

Internally consider 20 random candidate coordinates that are in-bounds and not blocked (`.`) safe cells.
Consider candidates from most of the sectors in order to remove first-pick predictability (the other team will know you always pick from the same sectors).
Choose one at random from the candidates — do not output the shortlist; output only the final choice.
Output exactly one token like: 3,5