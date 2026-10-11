# EE367 Course Project: Elevator Control Systems (Team 4)

## 1. Project Overview 💻

This project is a graphical simulation written in Python using the Tkinter
library to compare the operational efficiency of two fundamental elevator
(disk) scheduling algorithms:

- **First-Come, First-Served (FCFS)**
- **LOOK**

The goal is to demonstrate the trade-offs between a simple, fairness-based
scheduling policy (FCFS) and an optimized, locality-based policy (LOOK).
The simulation generates **25 randomized elevator requests** (by default)
and tracks the movement of two independent elevator cars (one using FCFS,
one using LOOK) on a 4-floor system in real time.

The results are analyzed using a set of Key Performance Indicators (KPIs),
providing a quantitative comparison of algorithm performance.

---

## 2. Requirements and Setup

- **Python version:** 3.6+
- **Libraries:**
  - Standard: `tkinter`, `time`, `random`, `dataclasses`, `threading`
  - System/monitoring: `psutil` (optional), `resource` (Unix-like systems)


---

## 3. How to Run the Code

1. Save the Python file as **`ElevatorSimulationOptimized.py`**  
   (or your chosen filename, and update the command below accordingly).
2. Open a terminal or command prompt.
3. Navigate to the directory where you saved the file.
4. Run

 * A GUI window titled "Elevator Simulation – FCFS & LOOK (Both) with Performance Metrics" will open.
* Click the "Start Simulation" button to begin the generation of 25 requests and the simultaneous
  movement of both elevators.


4. Reading and Interpreting Results (Key Performance Indicators)
The main comparison table displays the Key Performance Indicators (KPIs) 
that quantify the efficiency of each algorithm. 
Note that Memory usage (MB) (Shared) is only displayed once the simulation is complete.



* Time (Seconds):
  * Goal: Lower
  * Interpretation: Total duration to complete all 25 requests.

* Avg Wait Time (s):
  * Goal: Lower
  * Interpretation: The average time a passenger waits in the queue until the elevator arrives for pickup. 
    Critical measure of user experience.

* Throughput (req/s):
  * Goal: Higher
  * Interpretation: The rate of completed work (requests serviced per second). Measures system capacity.

* Distance:
  * Goal: Lower
  * Interpretation: The total number of floors the elevator traveled. Relates to energy usage and mechanical wear.

* Steps:
  * Goal: Lower
  * Interpretation: The total number of movement instructions the algorithm executed.

* Memory usage (MB) (Shared):
  * Goal: Lower
  * Interpretation: The memory consumed by the application, excluding the baseline memory used at startup. 
    This value is shared by both algorithms.

* CPU Utilization (%):
  * Goal: Lower (for the same workload)
  * Interpretation: The average percentage of CPU time used by the simulation process while servicing all requests.
    In this project, CPU usage is expected to be relatively low and similar for both algorithms, since the simulation
    is driven by timed GUI events rather than heavy computation.


Expected Outcome:
You should observe that the LOOK algorithm significantly outperforms FCFS across the most critical metrics 
(Avg Wait Time, Time, Distance, Steps, and often Throughput), demonstrating its superior efficiency
in scheduling requests based on its current direction of travel, while requiring a similar level of CPU utilization.