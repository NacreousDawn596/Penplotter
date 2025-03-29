import cv2
import numpy as np
import turtle
import os
from img2sketch import *
import sys
import argparse

def draw(contours, scale=1, offset_x=0, offset_y=0, container=2000, output_file="file.ino"):
    screen = turtle.Screen()
    screen.tracer(0, 0)
    screen.setup(800, 800)
    screen.bgcolor("white")
    screen.setworldcoordinates(-container, -container, container, container)
    
    t = turtle.Turtle()
    def draw_axes(x_max, y_max):
        t.speed(0)
        t.penup()
        t.goto(-x_max, 0)
        t.pendown()
        t.goto(x_max, 0)
        t.penup()
        t.goto(0, -y_max)
        t.pendown()
        t.goto(0, y_max)
        t.penup()

    def draw_grid(x_max, y_max, step=1000):
        t.speed(0)
        t.color("gray")
        for x in range(-x_max, x_max + step, step):
            if x == 0:
                continue
            t.penup()
            t.goto(x, -y_max)
            t.pendown()
            t.goto(x, y_max)
        for y in range(-y_max, y_max + step, step):
            if y == 0:
                continue
            t.penup()
            t.goto(-x_max, y)
            t.pendown()
            t.goto(x_max, y)
        t.penup()
        t.color("black")
        
    def draw_labels(x_max, y_max, step=500):
        t.speed(0)
        t.color("black")
        t.penup()
        for x in range(-x_max, x_max + step, step):
            t.goto(x, -20)
            t.write(str(x), align="center", font=("Arial", 12, "normal"))
        for y in range(-y_max, y_max + step, step):
            if y != 0:
                t.goto(-30, y - 5)
                t.write(str(y), align="right", font=("Arial", 12, "normal"))
    
    t.speed(0)
    # draw_grid(container, container)
    draw_axes(container, container)
    turtle.update()
    draw_labels(container, container, 500)
    t.penup()
    
    with open(f"{output_file}.ino", 'w') as f:
        f.write('''#include <Stepper.h>
#include <math.h>

#define STEPS_PER_REV 2048
#define rayon 800 
#define step_dyal_angle 1 
#define steps_kolhom (360 / step_dyal_angle) 
#define max_step 4500
#define half_max 2250

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

class Cursor {
  private:
    Stepper& penuse;
    Stepper& stepperX;
    Stepper& stepperY;
    float o_x, o_y;

  public:
    Cursor(Stepper& penuse, Stepper& stepperX, Stepper& stepperY, float xx = 0, float yy = 0) : penuse(penuse), stepperX(stepperX), stepperY(stepperY), o_x(xx), o_y(yy) {}

    void move(float x, float y) {
        int dx = round(x - o_x);
        int dy = round(y - o_y);
        o_x = x;
        o_y = y;
        moveSteppers(stepperX, stepperY, dx, -1* dy);
    }

    void penup() {
        penuse.step(150);
    }

    void pendown() {
        penuse.step(-150);
    }
};

void setup() {
    stepper2.setSpeed(10);
    stepper3.setSpeed(10);
    stepper1.setSpeed(10);
    
    Cursor cursor(stepper1, stepper2, stepper3); 
    
    Serial.begin(115200);
    cursor.penup();
    
    // Homing
    stepper2.step(2000);
    stepper3.step(2000);
    
    // Drawing
''')

        for i, contour in enumerate(contours):
            if len(contour) < 2:
                continue
            x, y = contour[0]
            f.write(f'    // Contour {i+1}\n')
            f.write(f'    cursor.move({x * scale + offset_x}, {y * scale + offset_y});\n')
            f.write('    cursor.pendown();\n')
            t.goto(x * scale + offset_x, y * scale + offset_y)
            t.pendown()
            for x, y in contour[1:]:
                f.write(f'    cursor.move({x * scale + offset_x}, {y * scale + offset_y});\n')
                t.goto(x * scale + offset_x, y * scale + offset_y)
            t.penup()
            f.write('    cursor.penup();\n\n')
        
        f.write('''
    // Retour à l'origine
    cursor.move(0, 0);
    stepper2.step(-2000);
    stepper3.step(-2000);
}

void loop() {
}''')
        
    screen.update()
    screen.mainloop()

def image_to_arduino_contours(img, output_file, n=10, canny_threshold1=50, canny_threshold2=150, pen_diameter=2, max_widthh=2000, multiplier=4.5):
    try:
        os.mkdir(output_file)
    except:
        pass
    os.chdir(output_file)

    if img is None:
        print("ta finahiya had tswira??")
        return
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, canny_threshold1, canny_threshold2)
    
    kernel_size = int(pen_diameter * 2)
    kernel = np.ones((kernel_size, kernel_size), np.uint8)
    edges = cv2.dilate(edges, kernel, iterations=1)
    
    contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    height, width = img.shape[:2]
    scale =  multiplier*max_widthh / max(width, height)
    simplified_contours = []

    for contour in contours:
        if cv2.contourArea(contour) < 10:
            continue
        
        epsilon = n * cv2.arcLength(contour, True) / 100
        approx = cv2.approxPolyDP(contour, epsilon, True)
        approx = approx.squeeze()
        if approx.ndim == 1: 
            approx = np.expand_dims(approx, axis=0)

        scaled = [(int(x * scale), multiplier*max_widthh - int(y * scale)) for (x, y) in approx]
        simplified_contours.append(scaled)

    all_points = [pt for contour in simplified_contours for pt in contour]
    if all_points:
        xs = [p[0] for p in all_points]
        ys = [p[1] for p in all_points]
        center_x = (min(xs) + max(xs)) // 2
        center_y = (min(ys) + max(ys)) // 2

        centered_contours = []
        for contour in simplified_contours:
            centered_contours.append([(x - center_x, y - center_y) for (x, y) in contour])
        simplified_contours = centered_contours

    draw(simplified_contours, scale=0.4, offset_x=0, offset_y=0, container=max_widthh, output_file=output_file)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate Arduino contours from an image.')
    parser.add_argument('input', help='Input image file path')
    parser.add_argument('output', help='Output file path')
    parser.add_argument('--n', type=int, default=0, help='n parameter (default: 0)')
    parser.add_argument('--canny_threshold1', type=int, default=125, 
                       help='First threshold for Canny edge detector (default: 125)')
    parser.add_argument('--canny_threshold2', type=int, default=130,
                       help='Second threshold for Canny edge detector (default: 130)')
    parser.add_argument('--pen_diameter', type=float, default=1.5,
                       help='Pen diameter for drawing (default: 1.5)')
    parser.add_argument('--max_widthh', type=int, default=2200,
                       help='Maximum width parameter (default: 2200)')
    parser.add_argument('--multiplier', type=int, default=6,
                       help='Multiplier factor (default: 6)')
    args = parser.parse_args()

    frame = cv2.imread(args.input)
    i2s = PencilSketch()


    image_to_arduino_contours(
        img=i2s(frame),
        output_file=args.output,
        n=args.n,
        canny_threshold1=args.canny_threshold1,
        canny_threshold2=args.canny_threshold2,
        pen_diameter=args.pen_diameter,
        max_widthh=args.max_widthh,
        multiplier=args.multiplier
    )