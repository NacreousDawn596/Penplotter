import cv2
import numpy as np
import turtle
import os

def t(contours, scale=1, offset_x=0, offset_y=0):
    """Dessine les contours avec t."""
    screen = turtle.Screen()
    screen.setup(800, 800)
    screen.bgcolor("white")
    
    t = turtle.turtle()
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

    def draw_grid(x_max, y_max, step=20):
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
    t.penup()

    for contour in contours:
        if len(contour) < 2:
            continue
        
        # Déplacer vers le premier point
        x, y = contour[0]
        t.goto(x * scale + offset_x, y * scale + offset_y)
        t.pendown()

        # Tracer le reste du contour
        for x, y in contour[1:]:
            t.goto(x * scale + offset_x, y * scale + offset_y)

        t.penup()  # Lever le stylo à la fin du contour

    screen.mainloop()

def image_to_arduino_contours(image_path, output_file, canny_threshold1=50, canny_threshold2=150):
    """Convertit une image en instructions pour un traceur basé sur Arduino."""
    img = cv2.imread(image_path)
    try:
        os.mkdir(output_file)
    except:
        pass
    os.chdir(output_file)

    if img is None:
        print("Erreur : Impossible de charger l'image.")
        return
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, canny_threshold1, canny_threshold2)
    contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    height, width = img.shape[:2]
    scale = 2000 / max(width, height)
    scaled_contours = []

    for contour in contours:
        if cv2.contourArea(contour) < 10:
            continue
        scaled = [(int(x * scale), 2000 - int(y * scale)) for (x,y) in contour.squeeze()]
        scaled_contours.append(scaled)

    # Afficher avec t
    t(scaled_contours, scale=0.4, offset_x=-400, offset_y=-400)

    # Sauvegarder le fichier Arduino
    with open(f"{output_file}.ino", 'w') as f:
        f.write('''#include <Stepper.h>

#define STEPS_PER_REV 2048

int motor1[] = {13, 12, 11, 10};
int motor2[] = {9, 8, 7, 6};
int motor3[] = {5, 4, 3, 2};

Stepper stepperX(STEPS_PER_REV, motor1[0], motor1[2], motor1[1], motor1[3]); 
Stepper stepperY(STEPS_PER_REV, motor2[0], motor2[2], motor2[1], motor2[3]); 
Stepper stepper1(STEPS_PER_REV, motor3[0], motor3[2], motor3[1], motor3[3]); 

void moveSteppers(int dx, int dy) {
    stepperX.step(dx);
    stepperY.step(dy);
}

void penUp() {
    stepper1.step(150);
}

void penDown() {
    stepper1.step(-150);
}

void setup() {
    stepperX.setSpeed(10);
    stepperY.setSpeed(10);
    stepper1.setSpeed(10);
    
    Serial.begin(115200);
    penUp();
    
    // Homing
    stepperX.step(2000);
    stepperY.step(2000);
    
    // Drawing
''')

        for i, contour in enumerate(scaled_contours):
            if len(contour) < 2:
                continue
                
            f.write(f'    // Contour {i+1}\n')
            f.write(f'    moveSteppers({contour[0][0]}, {contour[0][1]});\n')
            f.write('    penDown();\n')
            for point in contour[1:]:
                f.write(f'    moveSteppers({point[0]}, {point[1]});\n')
            f.write('    penUp();\n\n')

        f.write('''
    // Retour à l'origine
    moveSteppers(0, 0);
}

void loop() {
}''')

if __name__ == "__main__":
    image_to_arduino_contours(
        image_path="image.png",
        output_file="monalisa",
        canny_threshold1=30,
        canny_threshold2=120
    )
