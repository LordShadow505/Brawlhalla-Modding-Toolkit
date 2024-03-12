import math
#haz un programa que deje introducir 2 parametros y hagaa lo siguiente:

'''
rotate_skew0 = int(matrix.get('rotateSkew0'))
                rotate_skew1 = int(matrix.get('rotateSkew1'))
                if has_rotate == "true":
                    angle_rad = math.atan2(rotate_skew1, rotate_skew0)
                    angle_deg = math.degrees(angle_rad)'''

print("Introduce el valor de rotate_skew0")
rotate_skew0 = int(input())
print("Introduce el valor de rotate_skew1")
rotate_skew1 = int(input())

angle_rad = math.atan2(rotate_skew1, rotate_skew0)
angle_deg = math.degrees(angle_rad)

print("El valor de angle_deg es: ", angle_deg)