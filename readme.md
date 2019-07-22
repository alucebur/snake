# Snake

This is a Python implementation of the classic game "Snake".

- [How to play](#how-to-play)
- [Screenshot](#screenshot)
- [Libraries used](#libraries-used)
- [Requirements](#requirements)
- [Installation](#installation)
- [License](#license)

---

### How to play
- Use arrow keys to move up, down, left and right.
- Feed the snake with apples without crashing into itself.
- If the snake leaves the screen, it will appear at the opposite edge.
- Press 'Escape' to exit.
- Press 'P' to pause the game. Press 'P' again to unpause.
- Press 'G' to show a grid.

---

### Screenshot
![Game screenshot](https://i.imgur.com/fMgL2xd.png)

---

### Libraries used
- os
- json
- queue
- random
- pygame

---

### Requirements
Requires Python 3.6+ (with pip).

---

### Installation
Clone the repository or download and extract the zip or tarball file in an empty folder on your computer.

Install dependencies:

- Pipenv:

        pipenv install

- Pip:

        pip install -r requirements.txt

Run the game:

- Pipenv:

        pipenv run snake.py

- Other:

        python snake.py

Enjoy.

---

### License
This project code is Unlicensed, feel free to use it as you want. Audios, fonts and background are from public domain.

Snake and apple sprites were modified from the original, and are under the following GPLv3 license:

Copyright (c) 2015 Rembound.com

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see http://www.gnu.org/licenses/.
