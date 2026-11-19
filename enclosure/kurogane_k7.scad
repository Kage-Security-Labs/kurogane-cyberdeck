// Kurogane K-7 enclosure - parametric OpenSCAD model (rev A concept)
// Units: mm. Axes: X = width (left to right, seen from the front),
// Y = height (0 = bottom edge of the core, up = antenna crown), Z = thickness
// (0 = back face, T = front face).
//
// Render one part at a time for printing:
//   openscad -o front.stl  -D 'part="front"'       kurogane_k7.scad
//   openscad -o back.stl   -D 'part="back"'        kurogane_k7.scad
//   openscad -o sled.stl   -D 'part="module_sled"' kurogane_k7.scad
//   openscad -o cover.stl  -D 'part="cover_plate"' kurogane_k7.scad
// part="assembly" shows everything with ghosted display/PCBs.
//
// MEASURE BEFORE PRINTING: display outline/active-area offset, connector heights,
// and your pogo block. Values marked CHECK are from datasheets or estimates.

part = "assembly";   // [assembly, front, back, module_sled, cover_plate]
$fn = 48;

// ---------------------------------------------------------------- core body
W = 212;            // width
H = 252;            // height (core, without battery grip)
T = 34;             // thickness
R = 8;              // corner radius (XY)
wall = 2.2;         // shell wall
split_z = 16;       // front shell depth measured from the front face
clr = 0.25;         // print clearance

// zones, measured DOWN from the top edge (match the mockup)
crown_h  = 14;
screen_h = 122;
pad_h    = 40;
kb_h     = 72;
function y_from_top(d) = H - d;

// ---------------------------------------------------------------- display
// Raspberry Pi Touch Display 2: overall 189.32 x 120.24, active 154.56 x 86.94
disp_w = 189.32;  disp_h = 120.24;  disp_t = 10;      // CHECK thickness on your unit
act_w  = 154.56;  act_h  = 86.94;
act_dx = 0;       act_dy = 0;                         // CHECK active-area offset from outline centre
screen_cy = y_from_top(crown_h + screen_h / 2);

// ---------------------------------------------------------------- gamepad strip (centres, mm)
pad_cy  = y_from_top(156);
dpad_c  = [28.7, pad_cy];   dpad_arm = [29.3, 9.3];
l_c     = [57.3, y_from_top(150.7)];
r_c     = [67.3, y_from_top(164)];
btn_d   = 13;
tb_c    = [W / 2, y_from_top(150)];   tb_open = [22, 18];   // PIM447 bezel opening
mouse_y = y_from_top(166.7);  mouse_w = 8.7;  mouse_h = 5.3;  mouse_pitch = 10.6;
sel_c   = [142, y_from_top(151.3)];  start_c = [142, y_from_top(159.3)];  pill = [17.3, 5.3];
abxy_c  = [180, pad_cy];  abxy_r = 11.3;  abxy_d = 10.8;

// ---------------------------------------------------------------- keyboard opening
kb_x0 = 6.7;  kb_x1 = W - 6.7;
kb_y0 = y_from_top(245.3);  kb_y1 = y_from_top(176);

// ---------------------------------------------------------------- top edge: antennas + vents
sma_n = 6;  sma_pitch = 30;  sma_d = 6.6;  sma_z = 21;
// labels left to right: Wi-Fi, LTE main, LTE div, aux 1, aux 2, GNSS puck
vent_z = [4, 11];  vent_w = 3;  vent_pitch = 7;

// ---------------------------------------------------------------- side ports (y from top, size w(along Y) x h(along Z))
port_z = 12;   // centre height above back face, matches mainboard connector level (CHECK)
left_ports  = [ [40, 9.2, 3.6], [58, 14.5, 6.6], [72, 6.2, 6.2], [92, 16.2, 13.8] ]; // USB-C charge, USB-A, 3.5 mm, RJ45
right_ports = [ [40, 9.2, 3.6], [58, 15.4, 6.2], [74, 4.5, 2.2], [84, 8.5, 3.2] ];  // USB-C host, HDMI, BOOT, kill switch

// ---------------------------------------------------------------- DeckBus side bays
rail_y0 = 2;  rail_len = 110;            // rails run from y = 2 to 112
rail_z  = [8, 26];                         // rail centre heights
dt_base = 6;  dt_top = 8;  dt_h = 3;       // dovetail: width at body, width at tip, height
pogo_c  = [57, 17];                        // window centre (y, z)
pogo_win = [27.5, 7.5];                    // 2 x 10 block at 2.54 mm pitch + margin (CHECK your block)
screw_c = [8, 17];                         // M3 brass-insert hole for the sled thumbscrew (y, z)
sled_w = 34; sled_len = 110; sled_t = 30;

// ---------------------------------------------------------------- back
heat_win = [31, y_from_top(110), 150, 90];      // x, y, w, h  (aluminium plate sits over this)
hatchA   = [20, y_from_top(170), 80, 42];
hatchB   = [112, y_from_top(170), 80, 42];
grip     = [16, -30, 180, 100, 24];             // x, y, w, h, depth behind the back face
grip_door = [8, 8];                              // door inset from the grip edges

// ================================================================ helpers
module rrect(size, r) { offset(r = r) offset(delta = -r) square(size); }
module rbox(w, h, d, r) { linear_extrude(d) rrect([w, h], r); }
module at_xy(p) { translate([p[0], p[1], 0]) children(); }

module body_solid() { rbox(W, H, T, R); }
module body_void()  { translate([wall, wall, wall]) rbox(W - 2 * wall, H - 2 * wall, T - 2 * wall, R - wall); }

// dovetail rail along Y, protruding in -X from x = 0 (left side); mirrored for the right
module dovetail_profile(base, top, h) { polygon([[0, -base / 2], [0, base / 2], [-h, top / 2], [-h, -top / 2]]); }
module rail_left() {
    for (z = rail_z)
        translate([0, rail_y0, z]) rotate([-90, 0, 0]) linear_extrude(rail_len) rotate(0) dovetail_profile(dt_base, dt_top, dt_h);
}

// ================================================================ cutouts
module front_cuts() {
    zc = T - wall - 1;  hc = wall + 2;
    translate([0, 0, zc]) linear_extrude(hc) {
        // screen window
        translate([W / 2 + act_dx - (act_w + 1) / 2, screen_cy + act_dy - (act_h + 1) / 2]) rrect([act_w + 1, act_h + 1], 1.5);
        // D-pad
        at_xy(dpad_c) { square(dpad_arm, center = true); rotate(90) square(dpad_arm, center = true); }
        // L / R
        at_xy(l_c) circle(d = btn_d);
        at_xy(r_c) circle(d = btn_d);
        // trackball + mouse buttons
        translate([tb_c[0] - tb_open[0] / 2, tb_c[1] - tb_open[1] / 2]) rrect(tb_open, 5);
        for (i = [-1 : 1]) translate([W / 2 + i * mouse_pitch - mouse_w / 2, mouse_y - mouse_h / 2]) rrect([mouse_w, mouse_h], 1.5);
        // select / start
        for (c = [sel_c, start_c]) translate([c[0] - pill[0] / 2, c[1] - pill[1] / 2]) rrect(pill, pill[1] / 2 - 0.01);
        // ABXY
        for (a = [0, 90, 180, 270]) translate([abxy_c[0] + abxy_r * cos(a), abxy_c[1] + abxy_r * sin(a)]) circle(d = abxy_d);
        // keyboard opening
        translate([kb_x0, kb_y0]) rrect([kb_x1 - kb_x0, kb_y1 - kb_y0], 4);
        // speaker grilles beside the screen
        for (sx = [13, W - 13]) for (j = [-2 : 2]) for (k = [0, 1])
            translate([sx - 2.5 + k * 5, screen_cy + j * 5]) circle(d = 2.2);
    }
}

module top_cuts() {
    // SMA bulkheads (through the top wall, along Y)
    for (i = [0 : sma_n - 1])
        translate([W / 2 + (i - (sma_n - 1) / 2) * sma_pitch, H - wall - 1, sma_z]) rotate([-90, 0, 0]) cylinder(d = sma_d, h = wall + 2);
    // exhaust vents behind the antenna row
    for (x = [20 : vent_pitch : W - 20])
        translate([x - vent_w / 2, H - wall - 1, vent_z[0]]) cube([vent_w, wall + 2, vent_z[1] - vent_z[0]]);
}

module side_port_cuts() {
    for (p = left_ports)
        translate([-1, y_from_top(p[0]) - p[1] / 2, port_z - p[2] / 2]) cube([wall + 2, p[1], p[2]]);
    for (p = right_ports)
        translate([W - wall - 1, y_from_top(p[0]) - p[1] / 2, port_z - p[2] / 2]) cube([wall + 2, p[1], p[2]]);
    // DeckBus pogo windows + thumbscrew insert holes, both sides
    for (sx = [-1, W - wall - 1]) {
        translate([sx, pogo_c[0] - pogo_win[0] / 2, pogo_c[1] - pogo_win[1] / 2]) cube([wall + 2, pogo_win[0], pogo_win[1]]);
        translate([sx, screw_c[0], screw_c[1]]) rotate([0, 90, 0]) cylinder(d = 4.2, h = wall + 2);  // M3 heat-set insert
    }
}

module back_cuts() {
    translate([0, 0, -1]) linear_extrude(wall + 2) {
        translate([heat_win[0], heat_win[1]]) rrect([heat_win[2], heat_win[3]], 3);
        for (h = [hatchA, hatchB]) translate([h[0], h[1]]) rrect([h[2], h[3]], 3);
    }
    // M2.5 insert holes around the heat plate and hatches
    for (h = [[heat_win[0], heat_win[1], heat_win[2], heat_win[3]], hatchA, hatchB])
        for (c = [[h[0] - 4, h[1] + 4], [h[0] + h[2] + 4, h[1] + 4], [h[0] - 4, h[1] + h[3] - 4], [h[0] + h[2] + 4, h[1] + h[3] - 4]])
            translate([c[0], c[1], -1]) cylinder(d = 3.6, h = wall + 4);
}

// ================================================================ battery grip (part of the back shell)
module grip_solid() {
    translate([grip[0], grip[1], -grip[4]]) rbox(grip[2], grip[3], grip[4] + wall, 10);
}
module grip_void() {
    translate([grip[0] + wall, grip[1] + wall, -grip[4] + wall]) rbox(grip[2] - 2 * wall, grip[3] - 2 * wall, grip[4] + wall, 10 - wall);
}
module grip_door_cut() {
    translate([grip[0] + grip_door[0], grip[1] + grip_door[1], -grip[4] - 1]) rbox(grip[2] - 2 * grip_door[0], grip[3] - 2 * grip_door[1] - 30, wall + 2, 6);
}

// ================================================================ shells
module shell_full() {
    difference() {
        union() {
            body_solid();
            rail_left();
            translate([W, 0, 0]) mirror([1, 0, 0]) rail_left();
            grip_solid();
        }
        body_void();
        grip_void();
        front_cuts();
        top_cuts();
        side_port_cuts();
        back_cuts();
        grip_door_cut();
    }
}

module front_shell() { intersection() { shell_full(); translate([-50, -50, T - split_z]) cube([W + 100, H + 100, split_z + 1]); } }
module back_shell()  { intersection() { shell_full(); translate([-50, -50, -50]) cube([W + 100, H + 100, T - split_z + 50]); } }

// ================================================================ DeckBus module sled (left-hand; mirror for right)
module module_sled() {
    // inner face at x = 0, sled extends to -sled_w; z matches the body
    z0 = (T - sled_t) / 2;
    difference() {
        translate([-sled_w, rail_y0, z0]) rbox(sled_w, sled_len, sled_t, 6);
        // female dovetails (open at the top end so the sled slides down)
        for (z = rail_z)
            translate([0.01, rail_y0 - 1, z]) rotate([-90, 0, 0]) linear_extrude(sled_len + 2)
                dovetail_profile(dt_base + 2 * clr, dt_top + 2 * clr, dt_h + clr);
        // PCB pocket on the inner face (28 x 100 x 1.6 board, pads face the deck)
        translate([-dt_h - 2.2, pogo_c[0] - 50 - clr, pogo_c[1] - 14 - clr]) cube([2.2 + 0.01, 100 + 2 * clr, 28 + 2 * clr]);
        // contact window in front of the pads: the deck's pogo tips must stand
        // about dt_h + 0.5 mm proud of the side wall to reach the pads (CHECK your block)
        translate([-dt_h - 0.3, pogo_c[0] - pogo_win[0] / 2, pogo_c[1] - pogo_win[1] / 2]) cube([dt_h + 0.31, pogo_win[0], pogo_win[1]]);
        // payload cavity
        translate([-sled_w + 3, rail_y0 + 6, z0 + 3]) cube([sled_w - 3 - dt_h - 2.2 - 1.5, sled_len - 12, sled_t - 6]);
        // SMA on the top end of the sled
        translate([-sled_w / 2 - 2, rail_y0 + sled_len - 4, sled_t / 2 + z0]) rotate([-90, 0, 0]) cylinder(d = sma_d, h = 6);
        // thumbscrew through-hole lined up with the body insert
        translate([-sled_w - 1, screw_c[0], screw_c[1]]) rotate([0, 90, 0]) cylinder(d = 3.4, h = sled_w + 2);
    }
}

module cover_plate() {
    // 4 mm blank plate with the same female dovetails, for an empty bay
    difference() {
        translate([-4 - dt_h, rail_y0, (T - sled_t) / 2]) rbox(4 + dt_h, sled_len, sled_t, 2);
        for (z = rail_z)
            translate([0.01, rail_y0 - 1, z]) rotate([-90, 0, 0]) linear_extrude(sled_len + 2)
                dovetail_profile(dt_base + 2 * clr, dt_top + 2 * clr, dt_h + clr);
        translate([-4 - dt_h - 1, screw_c[0], screw_c[1]]) rotate([0, 90, 0]) cylinder(d = 3.4, h = 10);
    }
}

// ================================================================ ghosts for the assembly view
module ghosts() {
    // display
    %translate([W / 2 - disp_w / 2, screen_cy - disp_h / 2, T - wall - disp_t]) cube([disp_w, disp_h, disp_t]);
    // mainboard 190 x 105 behind the display
    %translate([W / 2 - 95, screen_cy - 52.5 + 6, 3]) cube([190, 105, 1.6]);
    // CM5 on the mainboard
    %translate([W / 2 - 27.5, screen_cy - 20, 4.6 + 3]) cube([55, 40, 4.7]);
    // keyboard / gamepad board 196 x 112
    %translate([W / 2 - 98, 4, T - wall - 8]) cube([196, 112, 1.6]);
    // 2S2P pack in the grip
    %translate([W / 2 - 67.5, -24, -grip[4] + wall + 0.5]) cube([135, 40, 19]);
}

// ================================================================ output
if (part == "front") front_shell();
else if (part == "back") back_shell();
else if (part == "module_sled") module_sled();
else if (part == "cover_plate") cover_plate();
else {
    color("#2a2c2f") back_shell();
    color("#1b1d1f") translate([0, 0, 0.5]) front_shell();
    color("#3a3e43") translate([-0.5, 0, 0]) module_sled();
    color("#3a3e43") translate([W + 0.5, 0, 0]) mirror([1, 0, 0]) module_sled();
    ghosts();
}
