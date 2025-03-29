import turtle
import tkinter as tk
import os
from PIL import Image
import sys

background_image = sys.argv[1]
name = background_image.split(".")[0]
polygons = [[(0, 0)]]

try:
    os.mkdir(name)
except:
    pass

os.system(f"convert {background_image} {name}/{background_image}.gif")

os.chdir(name)

def resize_image(image_path, scale_factor=2):
    img = Image.open(image_path)
    new_size = (int(img.width * scale_factor), int(img.height * scale_factor))
    img_resized = img.resize(new_size, Image.LANCZOS)
    new_image_path = "resized_" + image_path
    img_resized.save(new_image_path)
    return new_image_path

background_image = resize_image(f"{background_image}.gif")
turtle.addshape(background_image)
image_visible = True

def draw_axes(x_max, y_max):
    turtle.speed(0)
    turtle.penup()
    
    turtle.goto(-x_max, 0)
    turtle.pendown()
    turtle.goto(x_max, 0)
    turtle.penup()
    
    turtle.goto(0, -y_max)
    turtle.pendown()
    turtle.goto(0, y_max)
    turtle.penup()

def draw_grid(x_max, y_max, step=500):
    turtle.speed(0)
    turtle.color("gray")
    
    for x in range(-x_max, x_max + step, step):
        if x == 0:
            continue
        turtle.penup()
        turtle.goto(x, -y_max)
        turtle.pendown()
        turtle.goto(x, y_max)
    
    for y in range(-y_max, y_max + step, step):
        if y == 0:
            continue
        turtle.penup()
        turtle.goto(-x_max, y)
        turtle.pendown()
        turtle.goto(x_max, y)
    
    turtle.penup()
    turtle.color("black")
    
def draw_labels(x_max, y_max, step=500):
    turtle.speed(0)
    turtle.color("black")
    turtle.penup()
    
    for x in range(-x_max, x_max + step, step):
        turtle.goto(x, -20)
        turtle.write(str(x), align="center", font=("Arial", 12, "normal"))
    
    for y in range(-y_max, y_max + step, step):
        if y != 0:
            turtle.goto(-30, y - 5)
            turtle.write(str(y), align="right", font=("Arial", 12, "normal"))

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
draw_grid(x_max, y_max)
draw_axes(x_max, y_max)
turtle.update()

draw_labels(2000, 2000, 500)


def save_polygons():
    actual_code = """#include <Stepper.h>
#include <math.h>

#define STEPS_PER_REV 2048
#define rayon 800 
#define step_dyal_angle 1 
#define steps_kolhom (360 / step_dyal_angle) 
#define max_step 4500
#define half_max = 2250

int motor1[] = {13, 12, 11, 10};
int motor2[] = {9, 8, 7, 6};
int motor3[] = {5, 4, 3, 2};

Stepper stepper1(STEPS_PER_REV, motor1[0], motor1[2], motor1[1], motor1[3]); 
Stepper stepper2(STEPS_PER_REV, motor2[0], motor2[2], motor2[1], motor2[3]); 
Stepper stepper3(STEPS_PER_REV, motor3[0], motor3[2], motor3[1], motor3[3]); 

void moveSteppers(Stepper& stepperX, Stepper& stepperY, int dx, int dy) {
    int steps = fmax(abs(dx), abs(dy));
    float x_step = (float)dx / steps;
    float y_step = (float)dy / steps;
    
    float x_acc = 0, y_acc = 0;
    
    for (int i = 0; i < steps; i++) {
        x_acc += x_step;
        y_acc += y_step;
        
        if (round(x_acc) != 0) {
            stepperX.step(round(x_acc));
            x_acc -= round(x_acc);
        }
        if (round(y_acc) != 0) {
            stepperY.step(round(y_acc));
            y_acc -= round(y_acc);
        }
    }
}

class Plan {
  private:
    Stepper& penuse;
    Stepper& stepperX;
    Stepper& stepperY;
    float o_x, o_y;

  public:
    Plan(Stepper& penuse, Stepper& stepperX, Stepper& stepperY, float xx = 0, float yy = 0) : penuse(penuse), stepperX(stepperX), stepperY(stepperY), o_x(xx), o_y(yy) {}

    void move(float x, float y) {
        int dx = round(x - o_x);
        int dy = round(y - o_y);
        o_x = x;
        o_y = y;
        moveSteppers(stepperX, stepperY, dx, dy);
    }

    void penup() {
        penuse.step(150);
    }

    void pendown() {
        penuse.step(-150);
    }
};

void setup() {
    stepper1.setSpeed(10);
    stepper2.setSpeed(10);
    stepper3.setSpeed(10);

    Plan cursor(stepper1, stepper2, stepper3); 

    Serial.begin(115200);

    cursor.penup();

    stepper2.step(2000);
    stepper3.step(2000);
"""
    
    for polygon in polygons:
        actual_code += f"cursor.move({polygon[0][0]}, {polygon[0][1]})"
        actual_code += "\ncursor.pendown()\n"
        for x, y in polygon[1:]:
            actual_code += f"cursor.move({x}, {y})\n"
        actual_code += "cursor.penup()\n"
        
    actual_code += "cursor.move(-2000, -2000);\n"
            

    with open(f"{name}.ino", "w") as file:
        file.write(actual_code)
    
    print(f"Polygons saved to {name}.ino")

def on_close():
    save_polygons()
    sys.exit(0)

turtle.getcanvas().winfo_toplevel().protocol("WM_DELETE_WINDOW", on_close)

turtle.done()
