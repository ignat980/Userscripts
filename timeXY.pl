#!/usr/bin/perl

# acceleration of gravity. note sign.
$g = -9.8;
#initial height
$y = 2;
#initial x_position
$x = 0;
#initial speed (1 m / s)
$v_0 = 1;

#take-off angle, deg
$theta = 45;

for($t = 0; $t < 10;$t +=0.02) {
   $x = $v_0 * $t;
   $y = ($v_0 * $t * sin($theta)) + (($g*($t*$t))/2);
   printf("t=%0.1f  x_pos=%0.1f   y_pos=%0.1f\n", $t, $x, $y);
   last if ($y < 0);
}