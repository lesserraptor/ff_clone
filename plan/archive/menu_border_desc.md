w = light color
b = dark color
g = in-between color
t = transparent pixel

top left corner:
ttttbb
ttbbgg
tbgwww
tbwwgg
bgwggb
bgwgbb
top border
b
g
w
g
b
t
bottom border
t
b
g
w
g
b
left border
bgwgbt
right border
tbgwgb
top right corner:
bbtttt
ggbbtt
wwwgbt
ggwwbt
bggwgb
bbgwgb
bottom left corner:
bgwgbb
bgwggb
tbwwgg
tbgwww
ttbbgg
ttttbb
bottom right corner:
bbgwgb
bggwgb
ggwwbt
wwwgbt
ggbbtt
bbtttt

example (18x18 menu box):
ttttbbbbbbbbbbtttt
ttbbggggggggggbbtt
tbgwwwwwwwwwwwwgbt
tbwwggggggggggwwbt
bgwggbbbbbbbbggwgb
bgwgbbttttttbbgwgb
bgwgbwtttttttbgwgb
bgwgbwtttttttbgwgb
bgwgbwtttttttbgwgb
bgwgbwtttttttbgwgb
bgwgbwtttttttbgwgb
bgwgbwtttttttbgwgb
bgwgbbttttttbbgwgb
bgwggbbbbbbbbggwgb
tbwwggggggggggwwbt
tbgwwwwwwwwwwwwgbt
ttbbggggggggggbbtt
ttttbbbbbbbbbbtttt

---

## Implementation

Think of the border as a 3x3 grid of 6x6 pixel blocks:

```
+-------+-------------------+-------+
| TL    | repeat top edge   | TR    |
| 6x6   | (w-12) wide       | 6x6   |
+-------+-------------------+-------+
| repeat|                   | repeat|
| left  |  transparent      | right |
| edge  |  (w-12 x h-12)    | edge  |
| 1px   |                   | 1px   |
+-------+-------------------+-------+
| BL    | repeat bot edge   | BR    |
| 6x6   | (w-12) wide       | 6x6   |
+-------+-------------------+-------+
```

Key points:
- **Top/bottom edges** are 6 pixels tall. Each row is filled entirely with one color (b, g, w, w, g, b from top to bottom). The corner patterns attach to each end.
- **Left/right edges** are 1 pixel tall, 6 pixels wide. Each vertical slice uses the edge pattern (bgwgbt / tbgwgb). The corner patterns attach to top and bottom.
- **Middle** is transparent.
- **Corners** are 6x6 pixel patterns that connect the edge patterns together.

For a box of width W and height H at scale S:
- Border thickness = 6 * S pixels on each side
- Left edge: x to x+6*S, y+6*S to y+H-6*S
- Right edge: x+W-6*S to x+W, y+6*S to y+H-6*S
- Top border: y to y+6*S, x+6*S to x+W-6*S
- Bottom border: y+H-6*S to y+H, x+6*S to x+W-6*S
