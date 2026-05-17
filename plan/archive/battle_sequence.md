battle menu layout:

top 45% of the screen is for enemies ("enemy" part). bottom 55% of the screen is for menus. ("menu" part)

at beggining of battle:
- character box: draw a menu box in the left 2/5 of the "menu" part of the screen. this box will contain the 4 party members. show the down-facing image of the character, with hp_current / hp_max displayed next to the character image.
- enemy name box: draw a menu box in the right 3/5 of the "menu" part of the screen, but make it stack behind the "character box". in this box, list the enemies by name, followed by a count of how many there are. example: if there is a single goblin, it should say "Goblin 1". if there are a pair of goblins and a slime, it should say "Goblin 2" and under that "Slime 1".
- action box. this should overlap both the "character box" and the "enemy box". the left border should be about a borders' width overlapping the "character box". in this menu, the choices are Fight and Run, with the up/down arrows moving between them.

if run is chosen:
- new menu is drawn over the full "menu" part. this is a text box, and it will describe the outcome of the choice to run. if the party gets away, it will say "Run away!!!" if they can't run it will say something like "The enemy blocks the way!!" and then the enemy gets a turn without the heroes getting a turn.

if fight is chosen:
- in the left 2/5 of the "menu" part, draw the character box again, but this time only for the character in question. 
- in the right 3/5 of the "menu" part, draw a box for the choices for this character. Fight, Magic, Item. 
- if "fight" is chosen, overlay another menu in the left 3/5 of the screen that lists out the enemies to be chosen from.
- if "magic" is chosen, replace the options with a list of spells to choose from, then overlay another menu in the left 3/5 fo the screen that lists out the enemies to be chosen from OR if it's a spell that targets the party, the list of heroes to choose from.
- if "item" is chosen, replace the options with a list of items to choose from, then the appropriate target choices

once the fight begins, overlay a new menu over the entire "menu" part that describes what happens one action at a time. note that when the enemy gets a turn, their actions will also be described here.

example of the description:
hero A attacks enemy B with weapon. 15 damage! 
enemy B attacks hero A with weapon. 5 damage!
hero C use Fire against enemy B. 30 damage!
enemy B defeated.
Right on!
Received 72 GP.
Received 12 EXP.
Received Cure!
