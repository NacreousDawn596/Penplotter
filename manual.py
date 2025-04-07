import turtle
import tkinter as tk
import os
import sys
import penplotter.interface as interface
import penplotter.imageUtils as imageUtils

background_image = sys.argv[1]
name = background_image.split(".")[0]
polygons = [[(0, 0)]]

try:
    os.mkdir(name)
except:
    pass

os.system(f"convert {background_image} {name}/{background_image}.gif")

os.chdir(name)

background_image = imageUtils.resize_image(f"{background_image}.gif")
turtle.addshape(background_image)
image_visible = True

def on_mouse_click(x, y):
    print(f"Left click at: ({x}, {y})")
    turtle.color("red")
    turtle.goto(x, y)
    polygons[-1].append((x, y))
    turtle.update()

def on_right_click(x, y):
    print(f"Right click at: ({x}, {y})")
    turtle.penup()
    turtle.goto(x, y)
    turtle.pendown()
    turtle.dot(5, "blue") 
    polygons.append([(x, y)])
    turtle.update()
    
def toggle_background(x, y):
    global image_visible
    if image_visible:
        turtle.bgpic("") 
    else:
        turtle.bgpic(background_image) 
    image_visible = not image_visible

root = tk.Tk()
screen_size = min(root.winfo_screenwidth(), root.winfo_screenheight())
root.destroy()

x_max, y_max = 2250, 2250 

turtle.setup(width=screen_size, height=screen_size)
turtle.onscreenclick(on_mouse_click, 1)
turtle.onscreenclick(on_right_click, 3) 
turtle.onscreenclick(toggle_background, 2) 
turtle.setworldcoordinates(-x_max, -y_max, x_max, y_max)
turtle.hideturtle()
turtle.tracer(0, 0)
interface.draw_grid(x_max, y_max)
interface.draw_axes(x_max, y_max)
turtle.update()

interface.draw_labels(2000, 2000, 500)

def on_close():
    interface.save_polygons(name, polygons)
    sys.exit(0)

turtle.getcanvas().winfo_toplevel().protocol("WM_DELETE_WINDOW", on_close)

turtle.done()
