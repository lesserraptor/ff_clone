## Context
- architecture is described in plan/ARCHITECTURE.md
- currently, a custom JSON format is used to draw the maps
- we are using python arcade library, and we want to make sure that sprites generated with this library work in the map

## Goal
Ensure that we can use Tiled to edit maps, and that they load properly in the game in a Tiled format.

## Constraints
- Don't change anything about how sprites are working -- if there is no other way, discuss it before making any decisions
- The game must still work using Tiled-based maps after this change

## Acceptance Criteria
- [ ] Current map is saved into a Tiled format
- [ ] Newly saved map format is editable in Tiled (human check)
- [ ] Sprites still work properly with the new map format
- [ ] New tests to cover map load
- [ ] Game loads new map without any issues

## Implementation notes
- None
