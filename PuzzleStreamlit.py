import streamlit as st
from PIL import Image, ImageDraw
import random
from simpleai.search import astar, SearchProblem
import time

class PuzzleSolver(SearchProblem):
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

    def result(self, state, action):
        rows = string_to_list(state)
        row_empty, col_empty = get_location(rows, 'e')
        row_new, col_new = get_location(rows, action)
        rows[row_empty][col_empty], rows[row_new][col_new] = rows[row_new][col_new], rows[row_empty][col_empty]
        return list_to_string(rows)

    def is_goal(self, state):
        return state == GOAL

    def heuristic(self, state):
        rows = string_to_list(state)
        distance = 0

        for number in '12345678e':
            row_new, col_new = get_location(rows, number)
            row_new_goal, col_new_goal = goal_positions[number]
            distance += abs(row_new - row_new_goal) + abs(col_new - col_new_goal)

        return distance

def list_to_string(input_list):
    return '\n'.join([' '.join(x) for x in input_list])

def string_to_list(input_string):
    return [x.split() for x in input_string.split('\n')]

def get_location(rows, input_element):
    for i, row in enumerate(rows):
        for j, item in enumerate(row):
            if item == input_element:
                return i, j
    return None, None

GOAL = '''1 2 3
4 5 6
7 8 e'''

goal_positions = {}
rows_goal = string_to_list(GOAL)
for number in '12345678e':
    goal_positions[number] = get_location(rows_goal, number)

empty_piece = Image.new('RGB', (133, 133), color='white')

def main():
    st.title("8-Puzzle Solver")

    st.markdown(
        """
        <style>
        .button {
            display: flex;
            justify-content: center;
            align-items: center;
            width: 100%;
            height: 50px;
            font-size: 24px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader("Choose an image", type=["jpg", "jpeg", "png"])
    if uploaded_file is not None:
        img = Image.open(uploaded_file)
        img = img.resize((400, 400))
        pieces = [img.crop((j * 133, i * 133, (j + 1) * 133, (i + 1) * 133)) for i in range(3) for j in range(3)]
        tile_images = pieces.copy()

        init_session_state()

        display_image_frame(st.session_state.tiles, tile_images)

        col1, col3 = st.columns([1.5, 1.5])

        with col1:
            if st.button("Mix puzzle", key="mix_puzzle", use_container_width=True):
                current_state = list_to_string([[st.session_state.tiles[(i, j)] for j in range(3)] for i in range(3)])
                st.session_state.initial_state = current_state
                current_state = mix_puzzle_state(current_state)
                st.session_state.mixed_state = current_state
                update_puzzle(current_state, st.session_state.tiles)
                st.session_state.mixed = True
                st.session_state.solving = False
                st.session_state.waiting_message = False
                st.session_state.move_count = 0 
                st.experimental_rerun()

        with col3:
            if st.button("Solve", key="solve", use_container_width=True):
                if not st.session_state.mixed:
                    st.warning("Please mix the puzzle before solving.")
                else:
                    st.session_state.solving = True
                    st.session_state.waiting_message = True
                    st.experimental_rerun()

        if st.session_state.waiting_message:
            st.info("Solving the puzzle, please wait...")

        if 'move_count' in st.session_state and not st.session_state.waiting_message:
            st.write(f"Moves: {st.session_state.move_count}")

        if st.session_state.solving and st.session_state.waiting_message:
            current_state = list_to_string([[st.session_state.tiles[(i, j)] for j in range(3)] for i in range(3)])
            result = astar(PuzzleSolver(current_state))
            if not result.path():
                st.error("No solution found.")
                st.session_state.solving = False
                st.session_state.waiting_message = False
            else:
                st.session_state.solution_path = result.path()
                st.session_state.solution_step = 0
                st.session_state.waiting_message = False
                st.experimental_rerun()

        if st.session_state.solving and not st.session_state.waiting_message:
            if st.session_state.solution_step < len(st.session_state.solution_path):
                action, state = st.session_state.solution_path[st.session_state.solution_step]
                update_puzzle(state, st.session_state.tiles)
                st.session_state.solution_step += 1
                st.session_state.move_count += 1 
                time.sleep(0.5) 
                st.experimental_rerun()
            else:
                st.session_state.solving = False
                st.success("Puzzle solved!")

def mix_puzzle_state(state):
    current_state = state
    num_steps = random.randint(10, 30)
    last_action = None

    for step in range(num_steps):
        possible_actions = PuzzleSolver(current_state).actions(current_state)
        if last_action:
            possible_actions = [action for action in possible_actions if action != last_action]
        action = random.choice(possible_actions)
        current_state = PuzzleSolver(current_state).result(current_state, action)
        last_action = action

    if current_state == GOAL:
        possible_actions = PuzzleSolver(current_state).actions(current_state)
        action = random.choice(possible_actions)
        current_state = PuzzleSolver(current_state).result(current_state, action)

    return current_state

def update_puzzle(state, tiles):
    rows = string_to_list(state)
    for i, row in enumerate(rows):
        for j, tile in enumerate(row):
            tiles[(i, j)] = tile

def display_image_frame(tiles, tile_images):
    grid_image = Image.new('RGB', (400, 400), color='white')
    draw = ImageDraw.Draw(grid_image)
    
    for i in range(1, 3):
        draw.line((i * 133, 0, i * 133, 400), fill='black', width=2)
        draw.line((0, i * 133, 400, i * 133), fill='black', width=2)

    for i in range(3):
        for j in range(3):
            tile_index = tiles[(i, j)]
            if tile_index != 'e':
                tile_image = tile_images[int(tile_index) - 1]
                bordered_tile = Image.new('RGB', (135, 135), 'black')
                bordered_tile.paste(tile_image, (1, 1))
                grid_image.paste(bordered_tile, (j * 133, i * 133))

    st.image(grid_image, use_column_width=True)

def init_session_state():
    if 'tiles' not in st.session_state:
        st.session_state.tiles = { (i, j): str(i * 3 + j + 1) if i * 3 + j < 8 else 'e' for i in range(3) for j in range(3) }
    if 'mixed' not in st.session_state:
        st.session_state.mixed = False
    if 'solving' not in st.session_state:
        st.session_state.solving = False
    if 'waiting_message' not in st.session_state:
        st.session_state.waiting_message = False
    if 'initial_state' not in st.session_state:
        st.session_state.initial_state = None
    if 'mixed_state' not in st.session_state:
        st.session_state.mixed_state = None
    if 'move_count' not in st.session_state:
        st.session_state.move_count = 0

if __name__ == "__main__":
    main()
