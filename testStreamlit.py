import streamlit as st
from PIL import Image
import random
from simpleai.search import astar, SearchProblem
import time

# Class containing methods to solve the puzzle
class PuzzleSolver(SearchProblem):
    # Action method to get the list of the possible numbers that can be moved o the empty space 
    def actions(self, cur_state):
        rows = string_to_list(cur_state)
        row_empty, col_empty = get_location(rows, 'e')

        actions = []
        if row_empty > 0:
            actions.append(rows[row_empty - 1][col_empty])
        if row_empty < 2:
            actions.append(rows[row_empty + 1][col_empty])
        if col_empty > 0:
            actions.append(rows[row_empty][col_empty - 1])
        if col_empty < 2:
            actions.append(rows[row_empty][col_empty + 1])

        return actions

    # Return the resulting state after moving a piece to the empty space
    def result(self, state, action):
        rows = string_to_list(state)
        row_empty, col_empty = get_location(rows, 'e')
        row_new, col_new = get_location(rows, action)

        rows[row_empty][col_empty], rows[row_new][col_new] = \
                rows[row_new][col_new], rows[row_empty][col_empty]

        return list_to_string(rows)

    # Returns true if a state is the goal state
    def is_goal(self, state):
        return state == GOAL

    # Returns an estimate of the distance from a state to the goal using the Manhattan distance
    def heuristic(self, state):
        rows = string_to_list(state)

        distance = 0

        for number in '12345678e':
            row_new, col_new = get_location(rows, number)
            row_new_goal, col_new_goal = goal_positions[number]

            distance += abs(row_new - row_new_goal) + abs(col_new - col_new_goal)

        return distance

# Convert list to string
def list_to_string(input_list):
    return '\n'.join([' '.join(x) for x in input_list])

# Convert string to list
def string_to_list(input_string):
    return [x.split() for x in input_string.split('\n')]

# Find the 2D location of the input element 
def get_location(rows, input_element):
    for i, row in enumerate(rows):
        for j, item in enumerate(row):
            if item == input_element:
                return i, j  

# Final result that we want to achieve
GOAL = '''1 2 3
4 5 6
7 8 e'''

goal_positions = {}
rows_goal = string_to_list(GOAL)
for number in '12345678e':
    goal_positions[number] = get_location(rows_goal, number)

def main():
    st.title("8-Puzzle Solver")

    # Load image
    uploaded_file = st.file_uploader("Choose an image", type=["jpg", "jpeg", "png"])
    if uploaded_file is not None:
        img = Image.open(uploaded_file)
        img = img.resize((400, 400))  # Resize the image to fit the canvas
        pieces = [img.crop((j * 133, i * 133, (j + 1) * 133, (i + 1) * 133)) for i in range(3) for j in range(3)]
        pieces[-1] = Image.new('RGB', (133, 133), color='white')  # The last piece is empty
        tile_images = {}
        for i, piece in enumerate(pieces):
            tile_images[str(i + 1) if i < 8 else 'e'] = piece

        # Initialize session state for tiles and scramble flag
        if 'tiles' not in st.session_state:
            st.session_state.tiles = { (i, j): str(i * 3 + j + 1) if i * 3 + j < 8 else 'e' for i in range(3) for j in range(3) }
        if 'scrambled' not in st.session_state:
            st.session_state.scrambled = False
        if 'solving' not in st.session_state:
            st.session_state.solving = False

        # Display puzzle
        st.header("Puzzle")
        puzzle_cols = st.columns(3)
        tiles = st.session_state.tiles
        for i in range(3):
            for j in range(3):
                puzzle_cols[j].image(tile_images[tiles[(i, j)]], use_column_width=True)

        # Scramble button
        if st.button("Scramble"):
            goal_state = GOAL
            current_state = scramble_state(goal_state)
            st.session_state.tiles = update_puzzle(current_state, tiles, puzzle_cols, tile_images)
            st.session_state.scrambled = True
            st.session_state.solving = False

        # Solve button
        if st.button("Solve"):
            current_state = list_to_string([[tiles[(i, j)] for j in range(3)] for i in range(3)])
            if current_state == GOAL:
                st.warning("The puzzle is already solved.")
            elif not st.session_state.scrambled:
                st.warning("Please scramble the puzzle before solving.")
            else:
                result = astar(PuzzleSolver(current_state))
                if not result.path():
                    st.error("No solution found.")
                else:
                    st.session_state.solving = True
                    st.session_state.solution_path = result.path()
                    st.session_state.solution_step = 0
                    st.experimental_rerun()

        # Animate solution steps
        if st.session_state.solving and st.session_state.solution_step < len(st.session_state.solution_path):
            action, state = st.session_state.solution_path[st.session_state.solution_step]
            st.session_state.tiles = update_puzzle(state, st.session_state.tiles, puzzle_cols, tile_images)
            st.session_state.solution_step += 1
            time.sleep(0.5)
            st.experimental_rerun()

def scramble_state(state):
    current_state = state
    num_steps = random.randint(500, 1000)  # Scramble in 500-1000 steps
    for _ in range(num_steps):
        possible_actions = PuzzleSolver(current_state).actions(current_state)
        action = random.choice(possible_actions)
        current_state = PuzzleSolver(current_state).result(current_state, action)

    # Ensure the scrambled state is different from the goal
    if current_state == GOAL:
        for _ in range(100):
            possible_actions = PuzzleSolver(current_state).actions(current_state)
            action = random.choice(possible_actions)
            current_state = PuzzleSolver(current_state).result(current_state, action)

    return current_state

def update_puzzle(state, tiles, puzzle_cols, tile_images):
    rows = string_to_list(state)
    for i, row in enumerate(rows):
        for j, tile in enumerate(row):
            tiles[(i, j)] = tile
            puzzle_cols[j].image(tile_images[tile], use_column_width=True)
    return tiles

if __name__ == "__main__":
    main()
