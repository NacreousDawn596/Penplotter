import turtle

def show_and_save(contours, scale=1, offset_x=0, offset_y=0, container=2000, output_file="file.ino"):
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
            
def save_polygons(name, polygons):
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
    
    print(f"polygons saved to {name}.ino")