# WRO 2026 Future Engineers - Obstacle Challenge Generator

A Python tool for generating random **WRO 2026 Future Engineers Obstacle Challenge** layouts.

The program follows the randomisation procedure from the official WRO 2026 rulebook and generates a visual representation of the resulting field.

## What It Does

The generator randomly determines:

- Driving direction
- The section containing the single traffic sign
- The colour of the single traffic sign
- Traffic-sign positions in the other sections
- The section containing the parking lot
- The starting position

The generated layout is displayed using the WRO field image, with the traffic signs, parking lot, and starting position placed on top.

---

## How the Randomisation Works

The generator follows the WRO 2026 Obstacle Challenge randomisation procedure.

### 1. Driving Direction

The program randomly selects either:

- `CW` - Clockwise
- `CCW` - Counter-clockwise

### 2. Single-Sign Section

Two coin tosses are used to select the section containing the single traffic sign.

| Tosses | Section |
|---|---|
| Heads + Heads | North |
| Tails + Heads | West |
| Heads + Tails | East |
| Tails + Tails | South |

### 3. Single-Sign Colour

A third coin toss determines the colour of the single traffic sign.

```text
Heads -> Green
Tails -> Red
```

### 4. Traffic-Sign Cards

The program uses the 36 traffic-sign cards shown in the WRO 2026 rulebook.

Cards `9` and `10` are the single-sign cards. Depending on the colour selected above, the corresponding card is removed from the deck.

The remaining 35 cards are shuffled and three cards are drawn without replacement.

These cards determine the traffic-sign layouts in the other three straightforward sections.

Because cards are drawn without replacement, the same card cannot be selected twice during the same field setup.

The card data in the program is based directly on the layouts shown in the official rulebook.

---

## Traffic-Sign Positions

Each straightforward section contains a grid of possible traffic-sign positions.

The card system represents a position using three values:

```python
(len_idx, wid_idx, colour)
```

For example:

```python
(2, 1, 'green')
```

represents a green sign at a specific position within the section.

The program then converts these position values into the appropriate pixel coordinates for the section.

The position data is stored separately for each section:

```python
SEAT_PIXELS_RAW
```

This allows the same card definitions to be used regardless of which section the card is assigned to.

---

## Parking Lot

The parking lot is always placed in the starting section.

Another two coin tosses are used to determine which section contains the parking lot.

The parking lot dimensions are based on the robot length.

The program uses:

```python
park_length = 1.5 * robot_length
```

For example, with a 250 mm robot:

```text
250 mm x 1.5 = 375 mm
```

The parking lot is then drawn onto the field in the selected section.

The two parking-lot boundaries are also displayed.

---

## Starting Position

The starting position is placed in the same section as the parking lot.

The program marks the starting location on the generated field so it is easy to see where the robot can begin.

The generator also keeps track of the selected starting section in the generated configuration.

---

## Moving Signs in the Starting Section

After the parking lot is placed, the traffic signs in that section are moved closer to the inner wall.

The program handles this by changing the position of the signs in the starting section before rendering the final field.

This is done after the normal traffic-sign layout has been generated.

---

## Field Rendering

The program uses a reference image of the WRO field instead of drawing the entire field from scratch.

```python
PLAYFIELD_IMAGE = HERE / "playfield.png"
```

The generated objects are drawn over this image.

These include:

- Green traffic signs
- Red traffic signs
- Parking-lot boundaries
- Starting position
- Other field information

The result is exported as an HTML file that can be opened in a browser.

---

## Coordinate System

The program uses both millimetres and pixels.

### Millimetres

Millimetres are used for physical dimensions such as:

- Robot length
- Parking-lot dimensions
- Field measurements

### Pixels

Pixels are used when placing objects onto the field image.

The program converts between the two systems when necessary.

The conversion is handled by:

```python
mm_to_raw_px()
```

This allows the generated objects to be positioned correctly on the field image.

---

## Random Seeds

The generator supports random seeds.

For example:

```bash
python wro_fe_obstacle_generator.py --seed 42
```

Using the same seed will produce the same randomised configuration.

This is useful for:

- Recreating a previous practice field
- Testing the robot
- Debugging
- Comparing different navigation algorithms
- Recording specific challenge layouts

If no seed is provided, the program generates a new random configuration.

---

## Robot Length

The robot length can be changed using the command line.

For example:

```bash
python wro_fe_obstacle_generator.py --robot-length 300
```

This sets the robot length to:

```text
300 mm
```

and the parking-lot length becomes:

```text
300 x 1.5 = 450 mm
```

The default robot length is:

```text
250 mm
```

---

## Command Line Options

| Option | Description | Default |
|---|---|---|
| `--seed` | Sets the random seed | Random |
| `--robot-length` | Robot length in mm | `250` |
| `--output` | Output HTML filename | `obstacle_challenge_field.html` |
| `--size` | Display size in pixels | `560` |
| `--no-open` | Prevents the browser from opening automatically | Off |

### Example

```bash
python wro_fe_obstacle_generator.py --seed 42 --robot-length 250 --output round1.html --size 700
```

---

## Output

The generator creates an HTML file containing the generated field.

The output includes:

- The WRO field
- Traffic-sign locations
- Traffic-sign colours
- Parking lot
- Starting position
- Driving direction
- Randomisation information

The HTML file can be opened in any modern web browser.

---

## Project Structure

The project should contain:

```text
project/
|
+-- wro_fe_obstacle_generator.py
|
+-- playfield.png
|
+-- obstacle_challenge_field.html
```

`playfield.png` is the reference field image used by the generator.

The generated HTML file contains the field image directly, so the image does not need to be manually added to the HTML afterward.

---

## Main Parts of the Code

### `generate_round()`

This is the main function responsible for creating a new field configuration.

It handles the randomisation of the field and returns the resulting configuration.

### `DECK`

Contains the 36 traffic-sign card configurations.

The cards correspond to the layouts shown in the WRO 2026 rulebook.

### `SECTION_FROM_TOSS`

Converts the two coin tosses into the corresponding field section.

### `next_sections_clockwise()`

Determines which three straightforward sections come after the single-sign section when moving clockwise.

### `SEAT_PIXELS_RAW`

Contains the pixel locations of the possible traffic-sign positions for each section.

### `section_bbox_mm()`

Provides the approximate millimetre boundaries of each straightforward section.

### `render_popup_html()`

Creates the visual representation of the generated field and places the generated objects on top of the field image.

### `main()`

Handles the command-line arguments, generates the field, saves the output, and opens the generated HTML file.

---

## Installation

Python 3 is required.

Install the required package with:

```bash
pip install pillow
```

The rest of the program uses Python's standard libraries.

---

## Running the Generator

The basic command is:

```bash
python wro_fe_obstacle_generator.py
```

The program will:

1. Generate a random field
2. Print the generated configuration
3. Create the HTML file
4. Open the field in a browser

A specific configuration can be recreated later by using the same seed.

---

## Purpose

The goal of this project is to make WRO practice rounds easier to set up and more random.

Instead of manually creating a new obstacle layout every time, the generator can quickly produce a new field that follows the WRO randomisation system.

This makes it useful for:

- Robot testing
- Navigation development
- Practice rounds
- Debugging
- Team training
- Simulating competition conditions

---

## Example Random Combination Output Image

<img width="705" height="812" alt="Screenshot 2026-08-09 194108" src="https://github.com/user-attachments/assets/b17a0984-04db-48a8-bcd2-1d104a82665e" />
