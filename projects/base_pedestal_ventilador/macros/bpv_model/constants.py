"""Stage 1: real-world values, mm. User, 2026-11-26 (brief and answers)."""

# the fan's existing base (user): a circle, D_FAN_BASE across, H_FAN_BASE tall
D_FAN_BASE = 95.0
H_FAN_BASE = 10.0

# platform disc
D_OUT = 190.0      # twice the fan base
H_DISC = 10.0      # lifts the fan base by this much
D_STOP = 80.0      # through hole; the ring D_STOP..D_SOCKET is the stop the fan base sits on

# socket ring on top of the disc
D_SOCKET = 95.0    # exact, no play (user: "la medida tiene que ser exacta 95mm, no puede haber juego")
WALL = 10.0        # socket wall, so OD = D_SOCKET + 2 * WALL = 115 (user confirmed)
H_SOCKET = 5.0
CHAMFER = 1.0      # 45 deg lead-in at the socket mouth (user, 2026-11-26)

# material-saving slots through the disc (user chose 12 radial slots)
N_SLOTS = 12
SLOT_W = 20.0      # tangential width
RIM_IN = 5.0       # solid ring between the socket OD and the slots' inner ends
RIM_OUT = 5.0      # solid rim between the slots' outer corners and the disc edge (its thinnest point)
