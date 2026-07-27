"""
four_way_stop_queue_demo.py
===========================================================================
A SMALL TEACHING DEMO: a four-way stop intersection viewed as a QUEUING SYSTEM.

WHY THIS EXISTS
---------------
Before building the full microsimulation, this demo isolates the queuing-theory
core of the problem so the idea is concrete and visible. It is deliberately
*adjacent* to the real artifact: a four-way stop is essentially four queues
(the four approaches) competing for one shared "server" (the intersection
conflict zone, which can serve only one vehicle at a time under first-come-
first-served priority rules).

THE QUEUING-THEORY MAPPING (Garber & Hoel, 2009; Mpanza & Ncube, 2018)
----------------------------------------------------------------------
    Queuing concept            In this demo
    ----------------           -----------------------------------------
    Arrivals / input           Vehicles spawning at the end of each approach
                               (Poisson process, adjustable arrival rate lambda)
    The queue                  The line of stopped vehicles on each approach
    Service facility           The intersection: serves ONE vehicle at a time
    Service rate (mu)          1 / service_time  (services per second)
    Arrival rate (lambda_tot)  4 * lambda_per_approach
    Utilisation (rho)          lambda_tot / mu  =  4 * lambda * service_time
    Key result                 As rho -> 1, the queue grows toward infinity.
                               (Garber & Hoel: expected number in system -> inf
                                as arrival/service ratio -> 1.)

WHAT TO WATCH
-------------
Start with a stable system (rho < 1) and slowly raise the arrival rate. The
queues stay short and steady. Push rho past ~0.9 and the queues start to
explode; past 1.0 they grow without bound. That single behaviour is the whole
point of queuing theory in traffic, and it justifies why signal control /
coordination matters when demand approaches capacity.

CONTROLS
--------
    UP / DOWN     : increase / decrease arrival rate lambda (per approach)
    RIGHT / LEFT  : increase / decrease service time (RIGHT = slower server)
    SPACE         : pause / resume
    F             : toggle fast-forward (fills queues quickly for screenshots)
    R             : reset statistics and re-seed (reproducible run)
    ESC / Q       : quit

This is a standalone script. It is intentionally NOT the final artifact's code
-- it is a learning stepping stone. Run it with:  python four_way_stop_queue_demo.py

Requires: pygame  (install with:  pip install pygame)
===========================================================================
"""

import sys
import random
from collections import deque

import pygame

# ===========================================================================
# 1. CONFIGURATION  --  every tunable number lives here, in one place.
#    (This mirrors the "configuration over code" principle we will use in the
#     full artifact: change behaviour by changing values, not logic.)
# ===========================================================================

# --- Window / layout ---
SCENE = 720                 # the square traffic scene is SCENE x SCENE pixels
PANEL_W = 400               # width of the stats panel on the right
WIN_W, WIN_H = SCENE + PANEL_W, SCENE
FPS = 60

# --- Geometry of the intersection (all in pixels, measured in the scene) ---
CENTER = SCENE // 2         # 360 -- centre of the intersection
ROAD_HALF = 60              # half the road width -> road is 120 px wide
BOX = ROAD_HALF             # the intersection box spans CENTER +/- BOX
LANE_OFF = 30               # offset of a lane centre from the road centreline
VEH_LEN = 26                # vehicle length (along direction of travel)
VEH_WID = 15                # vehicle width
GAP = 12                    # bumper-to-bumper gap when queued
SPAWN_D = 360               # default distance (px) from stop line where cars appear
MAX_SPEED = 170.0           # free-flow speed in px/second

# --- Queuing parameters (the ones you will vary in the demo) ---
ARRIVAL_RATE = 0.08         # lambda: vehicles per second PER APPROACH (Poisson)
SERVICE_TIME = 2.0          # MEAN seconds the intersection is "busy" per vehicle
                            # (actual service times are exponential about this mean)
SEED = 42                   # fixed RNG seed -> reproducible runs (reliability)

# --- Colours (R, G, B) ---
C_BG        = (28, 30, 36)
C_ROAD      = (55, 58, 66)
C_BOX       = (70, 74, 84)
C_LINE      = (225, 225, 225)
C_PANEL     = (20, 22, 27)
C_TEXT      = (232, 232, 236)
C_DIM       = (150, 154, 163)
C_APPROACH  = (90, 150, 235)   # a moving/approaching vehicle
C_WAIT      = (235, 120, 90)    # a stopped/queuing vehicle
C_CROSS     = (110, 210, 130)   # the vehicle currently being served (crossing)
C_GOOD      = (110, 210, 130)
C_BAD       = (235, 95, 95)
C_CHART     = (120, 190, 240)
C_ACCENT    = (240, 200, 90)


# ===========================================================================
# 2. APPROACH DEFINITIONS
#    Each of the four approaches is described purely by geometry. A vehicle's
#    screen position is derived from a single 1-D coordinate `d` = distance
#    from the stop line (positive = still approaching, 0 = at the line,
#    negative = inside/through the intersection).
# ===========================================================================

# axis        : which screen axis the vehicle travels along ('x' or 'y')
# direction   : +1 or -1, the sign of motion along that axis
# lane        : the constant coordinate on the OTHER axis (keeps right-hand traffic)
# stop        : the coordinate on the travel axis where the stop line sits
APPROACHES = {
    "West":  dict(axis="x", direction=+1, lane=CENTER + LANE_OFF, stop=CENTER - BOX),
    "East":  dict(axis="x", direction=-1, lane=CENTER - LANE_OFF, stop=CENTER + BOX),
    "North": dict(axis="y", direction=+1, lane=CENTER - LANE_OFF, stop=CENTER - BOX),
    "South": dict(axis="y", direction=-1, lane=CENTER + LANE_OFF, stop=CENTER + BOX),
}


def screen_pos(app, d):
    """Convert (approach, distance-from-stop-line d) into an (x, y) pixel centre.

    coord_on_travel_axis = stop - direction * d
      - when d > 0 the vehicle is 'behind' the stop line (upstream),
      - when d < 0 it has moved past the line into/through the intersection.
    """
    travel = app["stop"] - app["direction"] * d
    if app["axis"] == "x":
        return travel, app["lane"]
    else:
        return app["lane"], travel


# ===========================================================================
# 3. VEHICLE
#    Holds its own state and the timestamps needed to compute queuing metrics.
# ===========================================================================

class Vehicle:
    __slots__ = ("app_name", "d", "speed", "granted", "reached_line",
                 "t_spawn", "t_reach_line", "t_granted", "moving")

    def __init__(self, app_name, d, t_now):
        self.app_name = app_name
        self.d = d                 # distance from stop line (px)
        self.speed = 0.0           # current speed (px/s)
        self.granted = False       # has the server given this car right-of-way?
        self.reached_line = False  # has it arrived at the stop line yet?
        self.moving = True         # is it moving this frame? (False => queuing)
        # --- timestamps for metrics ---
        self.t_spawn = t_now       # when it entered the system
        self.t_reach_line = None   # when it first reached the stop line
        self.t_granted = None      # when the server started serving it


# ===========================================================================
# 4. SIMULATION  --  the model. Knows nothing about drawing.
# ===========================================================================

class Simulation:
    def __init__(self):
        self.arrival_rate = ARRIVAL_RATE
        self.service_time = SERVICE_TIME
        self.reset()

    # -- (re)initialise state; re-seeding keeps runs reproducible --
    def reset(self):
        random.seed(SEED)
        self.time = 0.0
        # one FIFO list of vehicles per approach (front of list handled via min-d)
        self.vehicles = {name: [] for name in APPROACHES}
        # next scheduled Poisson arrival time per approach
        self.next_arrival = {name: random.expovariate(self.arrival_rate)
                             for name in APPROACHES}
        # the single server:
        self.busy_until = 0.0          # sim-time when the intersection frees up
        self.serving = None            # the vehicle currently being served
        # --- metrics ---
        self.served = 0                # vehicles that have been served
        self.sum_wait = 0.0            # sum of (t_granted - t_reach_line)
        self.max_queue = 0             # largest total queue seen
        self.queue_time_integral = 0.0 # integral of total-queue over time (for avg)
        self.dropped = 0               # arrivals dropped due to overflow cap

    # ---------------------------------------------------------------
    # Derived queuing-theory quantities
    # ---------------------------------------------------------------
    @property
    def lambda_total(self):
        return 4.0 * self.arrival_rate           # total arrivals/sec

    @property
    def mu(self):
        return 1.0 / self.service_time           # services/sec

    @property
    def rho(self):
        return self.lambda_total / self.mu       # utilisation

    def theoretical_Lq(self):
        """Average queue length predicted by the M/M/1 model, Lq = rho^2/(1-rho).
        Valid only while rho < 1; returns None (unbounded) otherwise.
        NOTE: a four-way FCFS stop is only APPROXIMATELY M/M/1, so we present
        this as a reference, not an exact prediction."""
        r = self.rho
        return (r * r) / (1.0 - r) if r < 1.0 else None

    def observed_avg_queue(self):
        return self.queue_time_integral / self.time if self.time > 0 else 0.0

    def avg_wait(self):
        return self.sum_wait / self.served if self.served else 0.0

    def throughput_per_min(self):
        return (self.served / self.time * 60.0) if self.time > 0 else 0.0

    def total_queue(self):
        return sum(self.queue_len(name) for name in APPROACHES)

    def queue_len(self, name):
        """Number of vehicles stopped (queuing) on an approach."""
        return sum(1 for v in self.vehicles[name]
                   if not v.moving and not v.granted)

    # ---------------------------------------------------------------
    # One simulation step of length dt seconds
    # ---------------------------------------------------------------
    def step(self, dt):
        self.time += dt
        self._spawn(dt)
        self._drive(dt)
        self._serve()
        self._cleanup()
        # accumulate time-averaged metrics
        tq = self.total_queue()
        self.max_queue = max(self.max_queue, tq)
        self.queue_time_integral += tq * dt

    # -- Poisson arrivals: spawn a car when its scheduled time arrives --
    def _spawn(self, dt):
        for name, app in APPROACHES.items():
            if self.time < self.next_arrival[name]:
                continue
            # schedule the NEXT arrival (exponential inter-arrival time)
            self.next_arrival[name] += random.expovariate(self.arrival_rate)
            queue = self.vehicles[name]
            # spawn behind the current backmost car so nothing overlaps; this
            # lets a queue physically extend upstream as it grows.
            back_d = max((v.d for v in queue), default=SPAWN_D - (VEH_LEN + GAP))
            spawn_d = max(SPAWN_D, back_d + VEH_LEN + GAP)
            if spawn_d > 3000:          # hard cap so memory stays bounded
                self.dropped += 1
                continue
            queue.append(Vehicle(name, spawn_d, self.time))

    # -- car-following within each approach + crossing motion --
    def _drive(self, dt):
        min_gap = VEH_LEN + GAP
        for name, queue in self.vehicles.items():
            # sort front-to-back: front vehicle has the smallest d
            queue.sort(key=lambda v: v.d)
            leader_d = None
            for v in queue:
                # base floor from the leader (the car ahead). No leader => open road.
                base = -10_000.0 if leader_d is None else leader_d + min_gap
                # A vehicle that has NOT been granted right-of-way may never pass
                # the stop line (d = 0), no matter where its leader is. This is
                # what keeps the four-way stop a genuine single-server queue:
                # only the one granted car proceeds; everyone else holds at the line.
                floor = base if v.granted else max(base, 0.0)

                # mark arrival at the stop line (enters the "service queue")
                if not v.reached_line and v.d <= 0.5:
                    v.reached_line = True
                    v.t_reach_line = self.time

                # move forward (reducing d) up to MAX_SPEED, clamped at floor
                target = v.d - MAX_SPEED * dt
                if target <= floor:
                    v.d = floor
                    v.speed = 0.0
                    v.moving = v.granted     # a granted car at floor is still "crossing"
                else:
                    v.d = target
                    v.speed = MAX_SPEED
                    v.moving = True

                leader_d = v.d

    # -- the single server: pick the earliest arrival, FCFS across approaches --
    def _serve(self):
        # free the server once its busy period ends
        if self.serving is not None and self.time >= self.busy_until:
            self.serving = None
        if self.serving is not None:
            return  # still busy -> nobody else may go

        # gather each approach's front vehicle IF it is waiting at the line
        candidates = []
        for name, queue in self.vehicles.items():
            # The front of the *waiting* queue = the frontmost car not yet granted.
            # (A previously granted car may still be physically clearing the box,
            #  so we must ignore it and look at the next one in line.)
            waiting = [v for v in queue if not v.granted]
            if not waiting:
                continue
            front = min(waiting, key=lambda v: v.d)
            if front.reached_line:
                candidates.append(front)
        if not candidates:
            return

        # FIRST-COME-FIRST-SERVED: the one who reached the line earliest
        chosen = min(candidates, key=lambda v: v.t_reach_line)
        chosen.granted = True
        chosen.t_granted = self.time
        self.serving = chosen
        # Service duration is EXPONENTIAL with mean = service_time. Using an
        # exponential service distribution (not a fixed one) makes the pooled
        # system a genuine M/M/1 queue, so the theoretical comparison is valid.
        self.busy_until = self.time + random.expovariate(self.mu)
        # record its waiting time (time spent stopped at the line before service)
        self.sum_wait += (chosen.t_granted - chosen.t_reach_line)
        self.served += 1

    # -- remove vehicles that have driven off the scene --
    def _cleanup(self):
        for name, app in APPROACHES.items():
            kept = []
            for v in self.vehicles[name]:
                x, y = screen_pos(app, v.d)
                if -60 <= x <= SCENE + 60 and -60 <= y <= SCENE + 60:
                    kept.append(v)
            self.vehicles[name] = kept

    # ---------------------------------------------------------------
    # Parameter adjustment helpers (used by keyboard controls)
    # ---------------------------------------------------------------
    def bump_arrival(self, delta):
        self.arrival_rate = max(0.01, round(self.arrival_rate + delta, 3))

    def bump_service(self, delta):
        self.service_time = max(0.25, round(self.service_time + delta, 2))


# ===========================================================================
# 5. RENDERING  --  reads the simulation and draws it. Changes nothing.
# ===========================================================================

class Renderer:
    def __init__(self, screen):
        self.screen = screen
        self.f_big = pygame.font.SysFont("consolas,menlo,monospace", 26, bold=True)
        self.f_med = pygame.font.SysFont("consolas,menlo,monospace", 19, bold=True)
        self.f_sm = pygame.font.SysFont("consolas,menlo,monospace", 16)
        self.f_xs = pygame.font.SysFont("consolas,menlo,monospace", 14)
        # rolling history of total queue length, for the chart
        self.history = deque(maxlen=600)   # ~ last stretch of samples
        self._sample_acc = 0.0

    def text(self, s, x, y, font=None, color=C_TEXT):
        font = font or self.f_sm
        self.screen.blit(font.render(s, True, color), (x, y))

    # -- the traffic scene --
    def draw_scene(self, sim):
        # roads (two crossing bands)
        pygame.draw.rect(self.screen, C_ROAD,
                         (CENTER - ROAD_HALF, 0, ROAD_HALF * 2, SCENE))
        pygame.draw.rect(self.screen, C_ROAD,
                         (0, CENTER - ROAD_HALF, SCENE, ROAD_HALF * 2))
        # intersection box (the shared "server")
        pygame.draw.rect(self.screen, C_BOX,
                         (CENTER - BOX, CENTER - BOX, BOX * 2, BOX * 2))

        # centre lane dividers (dashed)
        for a in range(0, SCENE, 28):
            pygame.draw.line(self.screen, C_DIM, (CENTER, a), (CENTER, a + 14), 1)
            pygame.draw.line(self.screen, C_DIM, (a, CENTER), (a + 14, CENTER), 1)

        # stop lines (white bars just before the box on each approach)
        pygame.draw.line(self.screen, C_LINE,
                         (CENTER - BOX, CENTER), (CENTER - BOX, CENTER + ROAD_HALF), 3)
        pygame.draw.line(self.screen, C_LINE,
                         (CENTER + BOX, CENTER - ROAD_HALF), (CENTER + BOX, CENTER), 3)
        pygame.draw.line(self.screen, C_LINE,
                         (CENTER - ROAD_HALF, CENTER - BOX), (CENTER, CENTER - BOX), 3)
        pygame.draw.line(self.screen, C_LINE,
                         (CENTER, CENTER + BOX), (CENTER + ROAD_HALF, CENTER + BOX), 3)

        # vehicles
        for name, app in APPROACHES.items():
            horizontal = (app["axis"] == "x")
            for v in sim.vehicles[name]:
                cx, cy = screen_pos(app, v.d)
                if v.granted:
                    color = C_CROSS
                elif not v.moving:
                    color = C_WAIT
                else:
                    color = C_APPROACH
                w, h = (VEH_LEN, VEH_WID) if horizontal else (VEH_WID, VEH_LEN)
                rect = pygame.Rect(0, 0, w, h)
                rect.center = (int(cx), int(cy))
                pygame.draw.rect(self.screen, color, rect, border_radius=3)

    # -- the stats / theory panel --
    def draw_panel(self, sim, paused, fast):
        px = SCENE
        pygame.draw.rect(self.screen, C_PANEL, (px, 0, PANEL_W, SCENE))
        x = px + 22
        y = 18
        self.text("FOUR-WAY STOP", x, y, self.f_big, C_ACCENT); y += 30
        self.text("as a queuing system", x, y, self.f_xs, C_DIM); y += 30

        # --- live queuing parameters ---
        self.text("QUEUING PARAMETERS", x, y, self.f_med, C_TEXT); y += 26
        self.text(f"Arrival per approach : {sim.arrival_rate:5.3f} veh/s", x, y); y += 20
        self.text(f"Total arrival rate     : {sim.lambda_total:5.3f} veh/s", x, y); y += 20
        self.text(f"mean service time : {sim.service_time:5.2f} s", x, y); y += 20
        self.text(f"mu (service rate) : {sim.mu:5.3f} veh/s", x, y); y += 24

        # utilisation rho -- the headline number, coloured by stability
        r = sim.rho
        rc = C_GOOD if r < 0.9 else (C_ACCENT if r < 1.0 else C_BAD)
        self.text(f"ρ = lambda/mu   : {r:5.3f}", x, y, self.f_med, rc); y += 22
        note = "stable" if r < 0.9 else ("near capacity" if r < 1.0 else "UNSTABLE  queue -> inf")
        self.text(note, x, y, self.f_xs, rc); y += 26

        # --- measured metrics ---
        self.text("MEASURED (live)", x, y, self.f_med, C_TEXT); y += 26
        self.text(f"total in queue    : {sim.total_queue():d}", x, y); y += 20
        self.text(f"max queue seen    : {sim.max_queue:d}", x, y); y += 20
        self.text(f"avg wait at line  : {sim.avg_wait():5.1f} s", x, y); y += 20
        self.text(f"throughput        : {sim.throughput_per_min():5.1f} veh/min", x, y); y += 20
        self.text(f"vehicles served   : {sim.served:d}", x, y); y += 20
        self.text(f"sim clock         : {sim.time:5.0f} s", x, y); y += 26

        # --- theory vs observation ---
        self.text("THEORY vs OBSERVED", x, y, self.f_med, C_TEXT); y += 26
        Lq = sim.theoretical_Lq()
        if Lq is None:
            self.text("M/M/1 Lq  : unbounded (rho>=1)", x, y, self.f_sm, C_BAD); y += 20
        else:
            self.text(f"M/M/1 Lq  : {Lq:5.2f} veh  (approx)", x, y); y += 20
        self.text(f"observed avg queue: {sim.observed_avg_queue():5.2f} veh", x, y); y += 20
        self.text("Garber & Hoel: as rho->1,", x, y, self.f_xs, C_DIM); y += 16
        self.text("expected queue -> infinity.", x, y, self.f_xs, C_DIM); y += 24

        # --- queue-length chart ---
        self.draw_chart(px + 22, y, PANEL_W - 44, 90, sim)
        y += 90 + 26

        # --- controls ---
        self.text("CONTROLS", x, y, self.f_med, C_TEXT); y += 24
        for line in ("UP/DOWN  arrival rate",
                     "LEFT/RIGHT  service time",
                     "SPACE pause   F fast   R reset"):
            self.text(line, x, y, self.f_xs, C_DIM); y += 17

        # status flags
        flags = []
        if paused: flags.append("PAUSED")
        if fast:   flags.append("FAST x4")
        if flags:
            self.text("  ".join(flags), x, SCENE - 26, self.f_med, C_ACCENT)

    # -- simple rolling line chart of the total queue length --
    def draw_chart(self, x, y, w, h, sim):
        self.text("total queue over time", x, y - 2, self.f_xs, C_DIM)
        y += 16
        pygame.draw.rect(self.screen, (14, 15, 19), (x, y, w, h))
        pygame.draw.rect(self.screen, C_DIM, (x, y, w, h), 1)
        if len(self.history) < 2:
            return
        peak = max(max(self.history), 5)
        pts = []
        n = len(self.history)
        for i, q in enumerate(self.history):
            px_ = x + int(i / (n - 1) * (w - 2)) + 1
            py_ = y + h - 1 - int(q / peak * (h - 2))
            pts.append((px_, py_))
        pygame.draw.lines(self.screen, C_CHART, False, pts, 2)
        self.text(f"{peak:d}", x + 3, y + 1, self.f_xs, C_DIM)

    # -- called each frame to feed the chart at a steady sample rate --
    def sample(self, sim, dt):
        self._sample_acc += dt
        if self._sample_acc >= 0.2:      # sample ~5x per simulated second
            self._sample_acc = 0.0
            self.history.append(sim.total_queue())


# ===========================================================================
# 6. MAIN LOOP
# ===========================================================================

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIN_W, WIN_H))
    pygame.display.set_caption("Four-way stop as a queuing system")
    clock = pygame.time.Clock()

    sim = Simulation()
    renderer = Renderer(screen)
    paused = False
    fast = False

    while True:
        # ---- real elapsed time; scale it for fast-forward ----
        dt_real = clock.tick(FPS) / 1000.0
        dt = dt_real * (4.0 if fast else 1.0)
        # guard against huge dt after a stall (keeps physics stable)
        dt = min(dt, 0.1)

        # ---- input ----
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    pygame.quit(); sys.exit()
                elif event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_f:
                    fast = not fast
                elif event.key == pygame.K_r:
                    sim.reset(); renderer.history.clear()
                elif event.key == pygame.K_UP:
                    sim.bump_arrival(+0.01)
                elif event.key == pygame.K_DOWN:
                    sim.bump_arrival(-0.01)
                elif event.key == pygame.K_RIGHT:
                    sim.bump_service(+0.25)
                elif event.key == pygame.K_LEFT:
                    sim.bump_service(-0.25)

        # ---- update ----
        if not paused:
            sim.step(dt)
            renderer.sample(sim, dt)

        # ---- draw ----
        screen.fill(C_BG)
        renderer.draw_scene(sim)
        renderer.draw_panel(sim, paused, fast)
        pygame.display.flip()


if __name__ == "__main__":
    main()
