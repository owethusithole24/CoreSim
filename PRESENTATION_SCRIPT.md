# 3-Minute Presentation — Speaker Script

**How to use this:** the slides carry the images; these are the words you say. Target ~2:50 so you don't overrun. Rehearse out loud against a timer at least twice. Advance slides with the arrow keys (or Space). Press **F** for fullscreen before you start.

Before the day: run the demo and save three images into the `CoreSim` folder — `corridor_map.png` (your Figure 2), `demo_stable.png` (ρ<1), `demo_saturated.png` (ρ≥1). The deck fills the slots automatically.

---

## Slide 1 — Problem & aim  *(~25s)*

"Every morning the four-way stop at the NWU main gate backs up — long queues, unpredictable delays, students arriving late. Widening the road just induces more traffic. So instead of changing the road, my project asks: *how do you design a small-scale microsimulation to test traffic-control alternatives along this corridor* — cheaply, and without disrupting the real intersection?"

*(Advance.)*

## Slide 2 — What I'm building  *(~30s)*

"The artifact is a custom microscopic simulation in Python, driven by synthetic data, following Design Science Research. The key idea is this: I model one corridor and one traffic demand, and I compare three controls at the main gate. Scenario one is today's unsignalised four-way stop. Scenario two replaces it with a single fixed-time traffic light. Scenario three coordinates the signals along the corridor into a green wave. Same road, same cars — only the control changes."

*(Advance.)*

## Slide 3 — How it's built  *(~45s)*

"The design is four components — network, vehicle, control, and output — inside a time-stepped engine. Network holds the road geometry. Vehicle drives individual cars using the Intelligent Driver Model from Treiber and Kesting, which my literature review already pointed to. Output records delay, queue length, and throughput.

The important decision is that **only the control component swaps** between my three scenarios — so the comparison is genuinely fair, because everything else is held identical. And the engine runs *headless*, separately from the visuals, so I can batch many runs fast and get the same result every time. That's what makes it reliable and performant — two of my evaluation criteria."

*(Advance.)*

## Slide 4 — Proof it's underway  *(~45s)*

"To make sure I understood the queuing core before building the whole thing, I've already built a working stepping-stone. It treats the four-way stop as a queuing system — four queues competing for one server, the intersection.

On the left, when arrivals stay below service capacity, queues stay short and steady. On the right, as utilisation approaches one, the queue grows without bound — exactly what queuing theory predicts, Garber and Hoel. This proves I can model arrivals, queues, and delay. The full artifact then adds the car-following behaviour, the real corridor geometry, and the swappable control on top."

*(Advance.)*

## Slide 5 — The road ahead  *(~25s)*

"From here the build is incremental: engine, network, vehicles, then each control in turn, and finally the comparison and analysis. I'm confirming two things with my supervisor — the exact intersection spacing, and which intersection to signalise first. The end deliverable is a low-cost, open-source artifact that shows whether signalisation and coordination actually reduce congestion on this corridor. Thank you."

---

### Delivery tips
- **Use the screenshots, not a live demo** — a live run can lag or hang under pressure; images give the same impact with none of the risk.
- If you're running long, the easiest cut is the second half of Slide 3 — keep "only the control swaps," drop the reliability/performance sentence.
- Land the last line cleanly and stop; don't trail off into "yeah, so, that's it."
