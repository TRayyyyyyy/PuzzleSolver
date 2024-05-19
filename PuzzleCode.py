import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import random
from simpleai.search import astar, SearchProblem
import tkinter.messagebox as messagebox

# Class containing methods to solve the puzzle
class PuzzleSolver(SearchProblem):
    # Action method to get the list of the possible numbers that can be moved into the empty space 
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

class PuzzleApp:
    def __init__(self, root):
        self.root = root
        self.root.title("8-Puzzle Solver")
        self.root.geometry("600x650")
        self.image_loaded = False 
        self.mixed = False  # Flag to track if the puzzle has been mixed
        self.tiles = {}
        self.tile_images = {}
        self.create_widgets()

        self.move_count = 0
        self.move_label = tk.Label(self.root, text="Moves: 0", font=("Helvetica", 15))
        self.move_label.grid(row=4, column=0, columnspan=3, pady=(10, 0))

        self.message_label = tk.Label(self.root, text="", font=("Helvetica", 12))
        self.message_label.grid(row=5, column=0, columnspan=3, pady=(10, 0))

    def create_widgets(self):
        title = tk.Label(self.root, text="8-Puzzle Solver", font=("Helvetica", 20, "bold"))
        title.grid(row=0, column=0, columnspan=3, pady=10)

        self.canvas = tk.Canvas(self.root, width=400, height=400, borderwidth=2, relief="solid")
        self.canvas.grid(row=1, column=0, rowspan=2, columnspan=3, padx=10, pady=10)

        self.mix_button = tk.Button(self.root, text="Mix puzzle", command=self.mix_puzzle, width=15)
        self.mix_button.grid(row=3, column=0, padx=10, pady=10)

        self.upload_button = tk.Button(self.root, text="Upload", command=self.load_new_image, width=15)
        self.upload_button.grid(row=3, column=1, padx=10, pady=10)

        self.solve_button = tk.Button(self.root, text="Solve", command=self.solve, width=15)
        self.solve_button.grid(row=3, column=2, padx=10, pady=10)

    def load_new_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg;*.jpeg;*.png")])
        if file_path:
            img = Image.open(file_path)
            img = img.resize((400, 400))  # Resize the image to fit the canvas
            pieces = [img.crop((j * 133, i * 133, (j + 1) * 133, (i + 1) * 133)) for i in range(3) for j in range(3)]
            pieces[-1] = Image.new('RGB', (133, 133), color='white')  # The last piece is empty
            for i, piece in enumerate(pieces):
                self.tile_images[str(i + 1) if i < 8 else 'e'] = ImageTk.PhotoImage(piece)
            self.update_puzzle(GOAL)  # Update to initial goal state with one empty tile
            self.image_loaded = True
            self.mixed = False  # Reset mix flag

    def update_puzzle(self, state):
        rows = string_to_list(state)
        self.canvas.delete("all")
        
        for i, row in enumerate(rows):
            for j, tile in enumerate(row):
                x0 = j * 133
                y0 = i * 133
                self.canvas.create_image(x0, y0, anchor=tk.NW, image=self.tile_images[tile])
                # Add thicker lines between image cells
                self.canvas.create_rectangle(x0, y0, x0 + 133, y0 + 133, outline="black", width=2)
                self.tiles[(i, j)] = tile

    def mix_puzzle(self):
        if not self.image_loaded:  # Check if an image has been loaded
            messagebox.showinfo("Error", "Please upload an image before mixing.")
            return
        self.move_label.config(text="Moves: 0")

        goal_state = GOAL
        current_state = self.mix_state(goal_state)
        self.mixed = True  # Set the flag to True after mixing
        self.update_puzzle(current_state)
        self.message_label.config(text="")

    def mix_state(self, state):
        current_state = state
        for _ in range(100):
            possible_actions = PuzzleSolver().actions(current_state)
            action = random.choice(possible_actions)
            current_state = PuzzleSolver().result(current_state, action)
        return current_state
    
    

    def solve(self):
        if not self.image_loaded:  # Check if an image has been loaded
            messagebox.showinfo("Error", "Please upload an image before solving.")
            return
        current_state = list_to_string([[self.tiles[(i, j)] for j in range(3)] for i in range(3)])
        if current_state == GOAL:
            messagebox.showinfo("Info", "The puzzle is already solved. Please mix the puzzle before solving.")
            return
        if not self.mixed:  # Check if the puzzle has been mixed
            messagebox.showinfo("Error", "Please mix the puzzle before solving.")
            return
        
        self.mix_button.config(state=tk.DISABLED)
        self.upload_button.config(state=tk.DISABLED)
        self.solve_button.config(state=tk.DISABLED)

        self.message_label.config(text="Please wait a moment while thinking to solve puzzle...", font=("Helvetica", 12, "italic"))
        self.root.update_idletasks()

        result = astar(PuzzleSolver(current_state))
        self.reset_move_count()
        if not result.path():
            print("No solution found.")
            return

        def animate_solution(steps):
            self.message_label.config(text="")  # Clear the message label
            if not steps:
                print("Puzzle solved in", self.move_count, "moves.")
                self.move_label.config(text="Puzzle solved!", font=("Helvetica", 14, "bold"))
                self.mixed = False  # Reset mix flag after solving
                self.mix_button.config(state=tk.NORMAL)
                self.upload_button.config(state=tk.NORMAL)
                self.solve_button.config(state=tk.NORMAL)
                return
            action, state = steps[0]
            self.update_puzzle(state)
            self.move_count += 1
            self.move_label.config(text="Moves: " + str(self.move_count))
            self.root.after(500, lambda: animate_solution(steps[1:]))

        animate_solution(result.path())

    def reset_move_count(self):
        self.move_count = 0
        self.move_label.config(text="Moves: 0")
        self.move_label.update_idletasks()

root = tk.Tk()
app = PuzzleApp(root)
root.mainloop()
