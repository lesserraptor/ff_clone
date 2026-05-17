# menu 

## party list
menu box that takes up right 2/3 of the screen. should show the down-facing frame of the character animation. to the right of that, the character's name. to the right of that the HP and MP stats.

## main menu
menu box that takes up left 1/3 of the screen. this menu should layer on top of the "party list" menu. choices include: 
- Items
- Equip
- Status
- Save

## gold menu
menu box that takes up bottom 1/8 of the screen (and about 1/2 of the width). this is just a running count of how much gold the party has. it should say something like "123GP"

## item menu
if you select "item", it should clear the screen and draw a new menu box with all the items the party has. this box shoudl be full height of the screen, and 2/3 of the width. it will also list the quantity of each -- for example "Cure 4" or "Axe 3".

## equip menu
if you select "equip", the cursor should jump over to the "party list" and allow you to select one of the heros. then, when you select one of them, we clear the screen and draw the equip menu.

the equip menu has several parts layered back to front:
- character stats. menu box that takes up left 1/2 of the screen, bottom 3/4 of the screen. this should show strength, defense, agility, magic. each has a score. when the user chooses equipment for the character, these numbers should change to show what effect the equipment had on the character's stats.
- character identifier. menu box that takes up left 1/3 of the screen, top 1/4 of the screen. shows the down-facing frame of the character animation, to the right of that, the character's name, and below that the characters current hp / max hp.
- equipment list. menu box that takes up full height, right 2/3 of the screen. lists out all the equipment type items.
- currently equipped items. this is a list of the items that the character has currently equipped. this menu box hovers over all the other menus. it obscures the equipment list, but doesn't obscure the character stats. it covers the bottom 3/4 of the screen. there should probably be a slot for armor, helmet, arm1, arm2 (arms can have shields, weapons, double-handed weapons, etc), accessories

## save menu
if you select "save", the screen should clear and display the save menu. there are 3 save slots visible. each is a menu box that takes up 1/3 of height of the screen, and the full width.
